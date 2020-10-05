from pydantic import BaseModel
from typing import List
from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import pandas as pd
from pyproj import Transformer
import smopy

from mlas.objects.cpt import CPT
from mlas.objects.crosssection import Crosssection
from mlas.objects.geometry import SoilProfile2D, SoilProfile2DLocation, SoilProfile3D
from mlas.objects.points import Point3D
from mlas.helpers import case_insensitive_glob

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
    referenceline: List[Point3D] = []

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
        # CREST CPTS
        if len(self.cpts_crest) > 0:
            cpts_crest = [{'name':cpt.name, 'x': cpt.x, 'y': cpt.y} for cpt in self.cpts_crest] 
                   
            for cpt in cpts_crest:
                cpt['lat'], cpt['lon'] = transformer.transform(cpt['x'], cpt['y'])

            lats = [cpt['lat'] for cpt in cpts_crest]
            lons = [cpt['lon'] for cpt in cpts_crest]

            map = smopy.Map((min(lats), min(lons), max(lats), max(lons)), z=14)
            
            ax = map.show_mpl(figsize=(15, 15))
            for cpt in cpts_crest:
                x, y = map.to_pixels(cpt['lat'], cpt['lon'])
                ax.plot(x, y, 'or', ms=2, mew=1)
                ax.text(x, y, cpt['name'])

            plt.tight_layout()
            plt.savefig(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"] / "location_crest_cpts.png")
            plt.close()

        # POLDER CPTS
        if len(self.ctps_polder) > 0:
            cpts_polder = [{'name':cpt.name, 'x': cpt.x, 'y': cpt.y} for cpt in self.ctps_polder]        

            for cpt in cpts_polder:
                cpt['lat'], cpt['lon'] = transformer.transform(cpt['x'], cpt['y'])

            lats = [cpt['lat'] for cpt in cpts_polder]
            lons = [cpt['lon'] for cpt in cpts_polder]

            map = smopy.Map((min(lats), min(lons), max(lats), max(lons)), z=14)
            
            ax = map.show_mpl(figsize=(15, 15))
            for cpt in cpts_polder:
                x, y = map.to_pixels(cpt['lat'], cpt['lon'])
                ax.plot(x, y, 'or', ms=2, mew=1)
                ax.text(x, y, cpt['name'])

            plt.tight_layout()
            plt.savefig(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["overview"] / "location_polder_cpts.png")
            plt.close()

    def _init_crest_cpts(self):
        cptfiles_crest = case_insensitive_glob(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["cpts_crest"], ".gef")
        for cptfile in cptfiles_crest:
            cpt = CPT()
            cpt.read(cptfile)
            self.cpts_crest.append(cpt)


    def _init_polder_cpts(self):
        cptfiles_polder = case_insensitive_glob(Path(self.base_folder).resolve() / self.levee_code / PROJECT_FOLDERS["cpts_polder"], ".gef")
        for cptfile in cptfiles_polder:
            cpt = CPT()
            cpt.read(cptfile)
            self.ctps_polder.append(cpt)

    def _plot_crest_cpts(self):
        pass

    def _plot_polder_cpts(self):
        pass

    # INITIALIZATION
    def init(self) -> None:
        # read data
        self._init_crest_cpts()
        self._init_polder_cpts()

        # generate plots
        self._plot_crest_cpts()
        self._plot_polder_cpts()


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

    # 