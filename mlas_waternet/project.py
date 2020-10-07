from pydantic import BaseModel
from typing import List
from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
import geojson
import contextily as ctx
import pandas as pd
from pyproj import Transformer
import smopy
from tqdm import tqdm
import matplotlib.gridspec as gridspec

from mlas.objects.cpt import CPT
from mlas.objects.crosssection import Crosssection
from mlas.objects.geometry import SoilProfile2D, SoilProfile2DLocation, SoilProfile3D
from mlas.objects.points import Point3D
from mlas.helpers import case_insensitive_glob
from mlas.convertors.cptconvertor import CPTConvertor, CPTConvertorMethod
from mlas.creators.soilprofile2dcreator import SoilProfile2DCreator, SoilProfile2DCreatorMethod

from mlas_waternet.settings import SETTINGS

PROJECT_FOLDERS = {
    "parameters":"input/parameters",
    "refline":"input/referenceline",
    "cpts_crest":"input/soilinvestigations/cpts/crest",
    "cpts_polder":"input/soilinvestigations/cpts/polder",
    "boreholes_crest":"input/soilinvestigations/boreholes/crest",
    "boreholes_polder":"input/soilinvestigations/boreholes/polder",
    "geoprofile_crest":"input/soilinvestigations/geoprofile/crest",
    "geoprofile_polder":"input/soilinvestigations/geoprofile/polder",
    "overview":"output/overview",
    "stbu_simple":"output/sbtu_simple"    
}



class Project(BaseModel):    
    base_folder: str  
    levee_code: str  

    ctps_polder: List[CPT] = []
    cpts_crest: List[CPT] = []
    soilprofile2d_crest: SoilProfile2D = None
    soilprofile2d_polder: SoilProfile2D = None
    soilprofile3d: SoilProfile3D = None
    referenceline_crest: List[Point3D] = []
    referenceline_polder: List[Point3D] = []

    # ASSESSMENTS
    def assess_stbu_simple(self):
        """this code starts a stbu simple assessment based on the given input"""
        pass

    # DATA CONVERSIONS / CREATION
    def create_geoprofile_crest(self):
        """generate a geoprofile for the crest"""
        pass

    def create_geoprofile_polder(self):
        """generate a geoprofile for the polder"""
        pass

    def create_geoprofile_3d(self):
        """generate a 3d profile"""
        pass

    def create_crosssections(self):
        """generate crosssections"""
        pass

    def create_empty(self, filepath: str):
        """create an empty project folder for a new project"""
        pass

    def plot_overview(self):
        transformer = Transformer.from_crs(28992, 4326)   

        # CREST OVERVIEW
        fig = plt.figure(constrained_layout=True, figsize=(30, 10))
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 3])
        ax_map = fig.add_subplot(gs[0, 0])
        ax_profile = fig.add_subplot(gs[0, 1])
        if len(self.cpts_crest) > 0:
            cpts_crest = [{'name':cpt.name, 'x': cpt.x, 'y': cpt.y} for cpt in self.cpts_crest] 
                   
            for cpt in cpts_crest:
                cpt['lat'], cpt['lon'] = transformer.transform(cpt['x'], cpt['y'])

            lats = [cpt['lat'] for cpt in cpts_crest]
            lons = [cpt['lon'] for cpt in cpts_crest]

            map = smopy.Map((min(lats), min(lons), max(lats), max(lons)), z=14)
            
            map.show_mpl(ax=ax_map)
            for cpt in cpts_crest:
                x, y = map.to_pixels(cpt['lat'], cpt['lon'])
                ax_map.plot(x, y, 'or', ms=2, mew=1)
                ax_map.text(x, y, cpt['name'])

            # REFERENCELINE 
            xs, ys = [], []
            for p in self.referenceline_crest:
                x, y = p.x, p.y
                lat, lon = transformer.transform(x, y)
                px, py = map.to_pixels(lat, lon)
                xs.append(px)
                ys.append(py)
            ax_map.plot(xs, ys, 'k--')         
           
            self.soilprofile2d_crest.plot(ax=ax_profile)
            
            fig.savefig(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"] / "location_crest_cpts.png")
            plt.close()

        # POLDER OVERVIEW
        fig = plt.figure(constrained_layout=True, figsize=(30, 10))
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 3])
        ax_map = fig.add_subplot(gs[0, 0])
        ax_profile = fig.add_subplot(gs[0, 1])
        if len(self.ctps_polder) > 0:
            cpts_polder = [{'name':cpt.name, 'x': cpt.x, 'y': cpt.y} for cpt in self.ctps_polder]        

            for cpt in cpts_polder:
                cpt['lat'], cpt['lon'] = transformer.transform(cpt['x'], cpt['y'])

            lats = [cpt['lat'] for cpt in cpts_polder]
            lons = [cpt['lon'] for cpt in cpts_polder]

            map = smopy.Map((min(lats), min(lons), max(lats), max(lons)), z=14)
            
            map.show_mpl(ax=ax_map)
            for cpt in cpts_polder:
                x, y = map.to_pixels(cpt['lat'], cpt['lon'])
                ax_map.plot(x, y, 'or', ms=2, mew=1)
                ax_map.text(x, y, cpt['name'])

            # REFERENCELINE 
            xs, ys = [], []
            for p in self.referenceline_polder:
                x, y = p.x, p.y
                lat, lon = transformer.transform(x, y)
                px, py = map.to_pixels(lat, lon)
                xs.append(px)
                ys.append(py)
            ax_map.plot(xs, ys, 'k--')
            self.soilprofile2d_polder.plot(ax=ax_profile)
            plt.savefig(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"] / "location_polder_cpts.png")
            plt.close()       

    def _init_cpts(self):
        cptfiles_crest = case_insensitive_glob(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["cpts_crest"], ".gef")
        print("reading crest CPTs...")
        for cptfile in tqdm(cptfiles_crest):
            cpt = CPT()
            cpt.read(cptfile)
            # cptconvertor = CPTConvertor(cpt=cpt, method=CPTConvertorMethod.THREE_TYPE_RULE, minimum_layer_height=0.2)
            # cptconvertor.execute()
            # cptconvertor.plot(filepath=str(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"]))
            self.cpts_crest.append(cpt)

        cptfiles_polder = case_insensitive_glob(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["cpts_polder"], ".gef")
        print("reading polder CPTs...")
        for cptfile in tqdm(cptfiles_polder):
            cpt = CPT()
            cpt.read(cptfile)
            # cptconvertor = CPTConvertor(cpt=cpt, method=CPTConvertorMethod.THREE_TYPE_RULE, minimum_layer_height=0.2)
            # cptconvertor.execute()
            # cptconvertor.plot(filepath=str(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"]))
            self.ctps_polder.append(cpt)

    def _init_soilprofile2ds(self):
        sp2dcreator = SoilProfile2DCreator(
            method = SoilProfile2DCreatorMethod.CPT_ONLY,
            cptconvertor_method = CPTConvertorMethod.THREE_TYPE_RULE,
            max_cpt_distance=100        
        )

        for cpt in self.cpts_crest:
            sp2dcreator.add_cpt(cpt)  
        self.soilprofile2d_crest = sp2dcreator.execute(polyline=self.referenceline_crest, fill=True)

        sp2dcreator.clear()
        for cpt in self.ctps_polder:
            sp2dcreator.add_cpt(cpt)  
        self.soilprofile2d_polder = sp2dcreator.execute(polyline=self.referenceline_polder, fill=True)
    
    def _init_reflines(self):
        crest_file = str(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["refline"] / "crest.geojson")
        polder_file = str(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["refline"] / "polder.geojson")

        with open(crest_file) as f:
            crest_points = geojson.load(f)
            for coord in crest_points["geometry"]["coordinates"][0]:
                self.referenceline_crest.append(Point3D(x=coord[0], y=coord[1]))

        with open(polder_file) as f:
            polder_points = geojson.load(f)
            for coord in polder_points["geometry"]["coordinates"]:
                self.referenceline_polder.append(Point3D(x=coord[0], y=coord[1]))

    # INITIALIZATION
    def init(self) -> None:
        # read data
        self._init_cpts()
        self._init_reflines()
        self._init_soilprofile2ds()   
        


    def new(self) -> None:
        """if the given folder contains data this will create a necessary input"""
        pathname = Path(self.base_folder).resolve() / self.levee_code
        pathname.mkdir(parents=True, exist_ok=True)

        # init all necessary directories
        for _, foldername in PROJECT_FOLDERS.items():
            pathname = Path(self.base_folder).resolve() / self.levee_code / foldername
            pathname.mkdir(parents=True, exist_ok=True)


if __name__=="__main__":
    # create a new project
    project = Project(base_folder=SETTINGS["project_path"], levee_code="A146")
    project.new()
    project.init()
    project.plot_overview()