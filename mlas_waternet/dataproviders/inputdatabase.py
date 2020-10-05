from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, Date, Float, Boolean
from sqlalchemy.orm import sessionmaker
import datetime
from tqdm import tqdm    
from enum import IntEnum
import os, glob
from pathlib import Path
from mlas_waternet.secrets import DB_INPUT_URL
from geoalchemy2 import Geometry, WKTElement

from mlas.objects.crosssection import Crosssection
from mlas.helpers import case_insensitive_glob
from mlas.objects.cpt import CPT

from mlas_waternet.settings import SETTINGS, LOG_FILES

Base = declarative_base()

class DBCrosssectionsTable(Base):
    __tablename__ = "crosssections"

    id = Column(Integer, primary_key=True)
    leveecode = Column(String)
    chainage = Column(Integer)
    jsonfile = Column(String)
    imgfile = Column(String)
    date = Column(Date)
    geom = Column(Geometry('LINESTRING'))

class DBCPTTable(Base):
    __tablename__ = "cpts"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    z = Column(Float(precision=2))
    date = Column(Date)
    geom = Column(Geometry('POINT'))

class DBSTBUSimpleTable(Base):
    __tablename__ = "stbusimple"
    id = Column(Integer, primary_key=True)
    result = Column(Boolean)
    imgfile = Column(String)
    jsonfile = Column(String)
    date = Column(Date)
    geom = Column(Geometry('POINT'))

class DBInput():
    def __init__(self):
        self.engine = create_engine(DB_INPUT_URL)
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def get_crosssections(self, levee_code, chainage_start=0, chainage_end=1e9):
        return [Crosssection.parse(r.jsonfile) for r in self.session.query(DBCrosssectionsTable).all()\
             if r.leveecode==levee_code and r.chainage >= chainage_start and r.chainage <= chainage_end]
        
    def add_crosssection(self, crosssection, jsonfile, imgfile): 
        # convert to database input
        geom = f"LineString({crosssection.startpoint.x} {crosssection.startpoint.y}, {crosssection.endpoint.x} {crosssection.endpoint.y})"
        row = DBCrosssectionsTable(
            leveecode=crosssection.levee_code, 
            chainage=crosssection.levee_chainage,
            jsonfile=jsonfile,
            imgfile=imgfile,
            date=datetime.date.today().strftime("%Y-%m-%d"),
            geom=geom
        )
        
        # check if we already have a row with this levee_code and chainage
        # todo > maybe use referencepoint to check instead of levee_code and chainage
        check_row = self.session.query(DBCrosssectionsTable). \
            filter(DBCrosssectionsTable.leveecode.like(crosssection.levee_code)). \
            filter(DBCrosssectionsTable.chainage == crosssection.levee_chainage).first()        

        if check_row is not None: # update
            self.session.query(DBCrosssectionsTable).filter(DBCrosssectionsTable==check_row.id). \
                update(
                    {
                        'jsonfile':jsonfile, 
                        'imgfile':imgfile, 
                        'date':datetime.date.today().strftime("%Y-%m-%d"), 
                        'geom':geom
                    }
                ) 
        else: # new row
            self.session.add(row)
        self.session.commit()

    
    def add_stbusimple(self, stbu_simple):   
        # convert to database input
        geom_string =  f"Point({stbu_simple.point.x} {stbu_simple.point.y})"
        date = datetime.datetime.today().strftime("%Y-%m-%d")

        # do we already have an entry at this point
        check_row = self.session.query(DBSTBUSimpleTable).filter(func.ST_Contains(DBSTBUSimpleTable.geom, WKTElement(geom_string))).first() 
        if not check_row: # add a new one
            row = DBSTBUSimpleTable(
                result = stbu_simple.result,
                imgfile = stbu_simple.imgfile,
                jsonfile = stbu_simple.logfile,
                date = date,
                geom = geom_string,
            )
            self.session.add(row)
        else: # update the old one
            self.session.query(DBSTBUSimpleTable).filter(DBSTBUSimpleTable==check_row.id).update(
                {
                    'result':stbu_simple.result, 
                    'jsonfile':stbu_simple.logfile, 
                    'imgfile':stbu_simple.imgfile, 
                    'date':date
                }
            )

        self.session.commit()

    def check_cpts(self):
        # create a logfile for the errors
        logfile = open(LOG_FILES['cpts'], 'a+')

        # get all cpts from the database
        current_cptfiles = [r.filename for r in self.session.query(DBCPTTable).all()]
        # get all cpt files in the given directory
        cptfiles = case_insensitive_glob(SETTINGS['cpt_path'], ".gef")
        for cptfile in tqdm(cptfiles):
            # skip if the filename is already in the database
            if str(cptfile) in current_cptfiles:
                continue

            cpt = CPT()
            try:
                cpt.read(cptfile) # todo > classfunction van maken?
            except Exception as e:
                logfile.write(f"Error reading {cptfile}\n")
                logfile.write(f"Error: {e}\n")
                continue

            # sometimes we find old coords where we have to add the Amersfoort coords
            if cpt.x < 0:
                cpt.x += 155000
                cpt.y += 463000

            # check if within valid x,y boundaries
            if cpt.x < 7000 or cpt.x > 300000 or cpt.y < 289000 or cpt.y > 629000:
                logfile.write(f"Error in {cptfile}\n")
                logfile.write(f"XY coords ({cpt.x}, {cpt.y}) not valid (limits x=[7000,300000], limits y=[289000,629000]\n")
                continue

            # check if the cpt as a valid date
            try:
                d = cpt.date
            except:
                logfile.write(f"Date error in {cptfile}\n")
                continue

            # check if the filename exists -> else add as new
            
            row = DBCPTTable(
                filename = str(cptfile),
                z = cpt.z_top,
                date = cpt.date,
                geom = f"Point({cpt.x} {cpt.y})",
            )

            self.session.add(row)
            self.session.commit()

        logfile.close()


if __name__=="__main__":
    engine = create_engine(DB_INPUT_URL)
    Base.metadata.create_all(engine)

    db = DBInput()
    db.check_cpts()

    #crss = db.get_crosssections("A145", 0, 100)
    #print(crss)


    
    