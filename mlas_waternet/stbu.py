from pydantic import BaseModel
from typing import List
import math
from shapely.geometry import LineString
from tqdm import tqdm

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

from mlas.objects.cpt import CPT
from mlas.objects.geometry import SoilLayer
from mlas.objects.points import Point3D
from mlas.convertors.cptconvertor import CPTConvertor, CPTConvertorMethod
from mlas.settings import SOILCOLORS

from mlas_waternet.dataproviders.inputdatabase import DBInput
from mlas_waternet.settings import OUTPUT_PATHS

class STBUSimple_Input(BaseModel):
    chainage_start: int = 0
    chainage_end: int = 1e9
    dth: float
    slopes: dict
    toplayer: str

class STBUSimple_Result(BaseModel):
    point: Point3D = None
    result: bool = False
    logfile: str = ""
    imgfile: str = ""
    

class STBUSimpleAssessment(BaseModel):
    class Config:
        arbitrary_types_allowed = True
    
    levee_code: str
    cpts: List[CPT] = []
    stbu_inputs: List[STBUSimple_Input] = []

    plots_path: str
    log_path: str    

    db: DBInput = None

    def _find_closest_cpt(self, point: Point3D):
        dlmin = 1e9

        result = None
        for cpt in self.cpts:
            dl = math.sqrt(math.pow(point.x - cpt.x, 2) + math.pow(point.y - cpt.y, 2))
            if  dl < dlmin:
                result = cpt
                dlmin = dl
        return result


    def _handle_stbu_input(self, stbu_input: STBUSimple_Input) -> None:
        # get all crosssections that are part of the stbu input definition
        crosssections = [crs for crs in self.db.get_crosssections(self.levee_code) if \
            crs.levee_chainage >= stbu_input.chainage_start and crs.levee_chainage <= stbu_input.chainage_end]

        # handle each crosssection
        for crosssection in tqdm(crosssections):
            # get the closest cpt
            cpt = self._find_closest_cpt(crosssection.reference_point)
            if cpt is None:
                # todo > log error
                continue

            # create soillayers > TODO > do this in advance, speeds up process
            cptconvertor = CPTConvertor(cpt=cpt, method=CPTConvertorMethod.THREE_TYPE_RULE, minimum_layer_height=0.2)
            soillayers = cptconvertor.execute()

            if soillayers[0].z_top < crosssection.z_top:
                soillayers.insert(0, SoilLayer(z_top=crosssection.z_top, z_bottom=soillayers[0].z_top, soil_code=stbu_input.toplayer))

            # create the current levee line
            levee_line_points = [(p.l, p.z) for p in crosssection.points if p.l<=crosssection.reference_point.l]
            leveeline = LineString(levee_line_points)

            # create the minimum line
            xs, zs = [], []
            
            # filter the soillayers (only save those with the bottom of the layer < DTH)
            checklayers = [sl for sl in soillayers if sl.z_bottom < stbu_input.dth]

            # round toplayer at DTH
            checklayers[0].z_top = stbu_input.dth

            # now we can calculate the minimum line
            x = crosssection.reference_point.l
            z = stbu_input.dth
            xs.append(x)
            zs.append(z)
            for layer in checklayers:
                x -= layer.height * stbu_input.slopes[layer.soil_code]
                z = layer.z_bottom
                xs.append(x)
                zs.append(z)

            # check for intersections
            minline = LineString((p[0], p[1]) for p in zip(xs,zs))

            stbr = STBUSimple_Result()
            stbr.point = crosssection.reference_point
            stbr.result = not minline.intersects(leveeline)
            

            if stbr.result == False:
                color = 'r--'
            else:
                color = 'g--'     

            # create visual output           
            fig = plt.figure(figsize=(20, 10))
            ax = fig.add_subplot()

            ax.grid(which="both")

            # plot the crosssection (dashed)
            ax.plot([p.l for p in crosssection.points], [p.z for p in crosssection.points], 'k--')
            # and the line we are checking
            ax.plot([p[0] for p in levee_line_points], [p[1] for p in levee_line_points], 'k')
            # plot the minimum line
            ax.plot(xs, zs, color)

            # plot the soilprofile
            for soillayer in soillayers:
                facecolor = SOILCOLORS[soillayer.soil_code]
                ax.add_patch(
                    patches.Rectangle(
                        (0, soillayer.z_bottom),
                        crosssection.reference_point.l,
                        soillayer.height,
                        fill=True,
                        facecolor=facecolor,
                    )
                )           

            plt.tight_layout()
            
            # save 
            filename = f"{crosssection.levee_code}_{crosssection.levee_chainage:05d}.png"
            path = Path(self.plots_path).resolve() / filename
            stbr.logfile = ""
            stbr.imgfile = str(path)
            plt.savefig(path)
            plt.close()

            # add to database
            self.db.add_stbusimple(stbr)


    def execute(self) -> None:
        if self.db is None: self.db = DBInput()
        for stbu_input in self.stbu_inputs:
            self._handle_stbu_input(stbu_input)


if __name__ == "__main__":

    # TODO > move input to project structured folder
    # and create a project for a base of ALL assessments

    CPT_CREST_FILES = [
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-67.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-69.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-71.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-73.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-75.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_K07/K07-77.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L07/L07-4.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L07/L07-5.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-32.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-34.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-36.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-38.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-40.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-42.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-44.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-46.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-48.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-50.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-52.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-54.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-56.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-58.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-60.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-62.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-64.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-66.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-68.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-72.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-74.GEF",
        "C:/Users/brein/Programming/Python/mlas_waternet/data/input/grondonderzoek/sonderingen/VAK_L06/L06-76.GEF",
    ]

    cpts = []
    for cptfile in CPT_CREST_FILES:
        cpt = CPT()
        cpt.read(cptfile)
        cpts.append(cpt)
    
    stbu_input = STBUSimple_Input(
        #chainage_start=0, 
        #chainage_end=250,
        dth = 1.0,
        toplayer = "Clay",
        slopes = {
            "Peat": 6,
            "Clay": 2,
            "Sand": 4,
        }          
    )

    stbu_simple_assessment = STBUSimpleAssessment(
        levee_code = 'A146',
        cpts = cpts,
        stbu_inputs = [stbu_input],
        plots_path = OUTPUT_PATHS['stbu_simple_assessment'],
        log_path = OUTPUT_PATHS['stbu_simple_assessment']
    ) 

    stbu_simple_assessment.execute()

        


