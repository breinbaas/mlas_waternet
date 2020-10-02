import numpy as np
import math
from pydantic import BaseModel
from typing import List

from mlas.objects.points import PointType, Point3D

from mlas_waternet.gis.tiles import Tileset, TileType
from mlas_waternet.dataproviders.heightdataprovider import HeightDataProvider

class WaterBottomCreator(BaseModel):
    """Algorithm to find waterbottom data for a crosssection
    
    Args:
        heigt_data_provider: HeightDataProvider the source of the height data
        points: List[Point3D]: list of points, the z coordinate will be replaced and the type
                                will be altered if a waterbottom point has been found at this location

    Returns:
        List[Point3D]: list with altered points
    """
    height_data_provider: HeightDataProvider = None
    start_point: Point3D
    end_point: Point3D
    center_to_center_distance: float = 0.5

    def execute(self) -> List[Point3D]:
        points = self.height_data_provider.get(
            start=self.start_point,
            end=self.end_point,
            center_to_center_distance=self.center_to_center_distance,
        )

        result = []
        waterbottom = []
        for p in points:
            if not np.isnan(p.z): 
                l = round(math.sqrt(math.pow(p.x - self.start_point.x, 2)+ math.pow(p.y - self.start_point.y, 2)), 2) 
                waterbottom.append(Point3D(x=p.x, y=p.y, z=round(p.z,2), l=l))
            else:
                if len(waterbottom) > 0:
                    result.append(waterbottom)
                    waterbottom = []

        return result

