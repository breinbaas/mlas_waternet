import argparse
import sys
from pathlib import Path
import shapefile
from tqdm import tqdm

from mlas.objects.points import Point2D

from mlas_waternet.creators.crosssectioncreator import CrosssectionCreator
from mlas_waternet.creators.waterbottomcreator import WaterBottomCreator
from mlas_waternet.dataproviders.heightdataprovider import HeightDataProvider, TileType
from mlas_waternet.settings import OUTPUT_PATHS
from mlas_waternet.dataproviders.inputdatabase import DBInput


HEIGHT_DATA = TileType.AHN3
WATERBOTTOM_DATA = TileType.WATERBOTTOM
DITCHES_DATA = TileType.DITCHES

if __name__=="__main__":
    db = DBInput()
    # preload the heightdataproviders saves time
    ahn3hdp = HeightDataProvider(tile_type=HEIGHT_DATA)
    ditchhdp = HeightDataProvider(tile_type=DITCHES_DATA)
    waterbottomhdp = HeightDataProvider(tile_type=WATERBOTTOM_DATA)

    if len(sys.argv) == 1: # for debugging purposes
        args = {
            "leveecode":"P019",
            "centertocenter":10
        }
    else:
        argparser = argparse.ArgumentParser(description='Create crosssections for a given levee.')
        argparser.add_argument("-l", "--leveecode", required=True, help="Levee code (like A145)")
        argparser.add_argument("-c", "--centertocenter", required=False, help="Center to center distance between crosssections")

        args = vars(argparser.parse_args())
    
    crc = CrosssectionCreator(
        levee_code=args["leveecode"],
        center_to_center_distance_chainage=int(args["centertocenter"]),
        height_data_provider = ahn3hdp
    )    

    print("Creating crosssections, this might take some time...")
    for crs in tqdm(crc.execute()):
        # # add ditches
        # dtc = WaterBottomCreator(
        #     height_data_provider = ditchhdp,
        #     start_point = crs.startpoint,
        #     end_point = crs.endpoint       
        # )
        # ditches = dtc.execute()

        # for ditch in ditches:
        #     crs.add_ditch([Point2D(x=p.l, z=p.z) for p in ditch])        

        # # add waterbottom of levee
        # wbc = WaterBottomCreator(
        #     height_data_provider = waterbottomhdp,
        #     start_point = crs.startpoint,
        #     end_point = crs.endpoint       
        # )
        # waterbottoms = wbc.execute()

        # for waterbottom in waterbottoms:
        #     crs.add_waterbottom([Point2D(x=p.l, z=p.z) for p in waterbottom])

        crs_pfilename = crs.serialize(filepath=OUTPUT_PATHS["crosssections_json"])
        crs_pimgname = crs.plot(filepath=OUTPUT_PATHS["crosssection_plots"])

        crs_filename = str(crs_pfilename.resolve())
        crs_imgname = str(crs_pimgname.resolve())
        db.add_crosssection(crs, jsonfile=crs_filename, imgfile=crs_imgname)
