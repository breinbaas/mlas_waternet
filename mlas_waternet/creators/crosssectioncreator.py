# temp hack as long as mlas and geolib are not distributed as packages
import sys
sys.path.append("/home/breinbaas/Programming/packages/mlas")

from pydantic import BaseModel
from typing import List
import math
import numpy as np

from mlas.objects.crosssection import Crosssection
from mlas.objects.points import Point3D, PointType
from mlas_waternet.dataproviders.heightdataprovider import HeightDataProvider, TileType
from mlas_waternet.gis.routes import Routes


class CrosssectionCreator(BaseModel):
    levee_code: str    
    tile_type: TileType = TileType.AHN3
    left_from_refpoint: int = 20
    right_from_refpoint: int = 50
    center_to_center_distance_chainage: int = 10
    center_to_center_distance_crosssection: float = 0.5
    rdp_epsilon: float = 0.05
    height_data_provider: HeightDataProvider
    _routes: Routes = Routes()

    def execute(self) -> List[Crosssection]:        
        if self.levee_code not in self._routes.get_levee_codes():
            raise ValueError(f"Unknown levee code '{self.levee_code}'")

        result = []
        rt = self._routes.get_by_levee_code(self.levee_code)

        for chainage in range(rt.min_chainage, rt.max_chainage, self.center_to_center_distance_chainage):
            x, y, alpha = rt.xya_at_chainage(chainage)

            alpha_l = alpha - math.radians(90)
            alpah_r = alpha + math.radians(90)
            xl = round(x + self.left_from_refpoint * math.cos(alpha_l), 2)
            yl = round(y + self.left_from_refpoint * math.sin(alpha_l), 2)
            xr = round(x + self.right_from_refpoint * math.cos(alpah_r), 2)
            yr = round(y + self.right_from_refpoint * math.sin(alpah_r), 2)

            points = self.height_data_provider.get(
                start=Point3D(x=xl, y=yl),
                end=Point3D(x=xr, y=yr),
                center_to_center_distance=self.center_to_center_distance_crosssection,
            )

            # add l (2d representation) to the points:
            for i in range(len(points)):
                points[i].l = round(
                    math.sqrt(
                        math.pow(points[i].x - points[0].x, 2) + math.pow(points[i].y - points[0].y, 2)
                    ),
                    2,
                )
                if points[i].l == 0:
                    points[i].point_type = PointType.REFERENCEPOINT

            # remove all nan's except for the start- and endpoint and the reference point
            points_no_nan = []
            for i in range(len(points)):
                if i == 0 or i == len(points) - 1 or points[i].point_type == PointType.REFERENCEPOINT:
                    points_no_nan.append(points[i])
                elif not np.isnan(points[i].z):
                    points_no_nan.append(points[i])

            # if the leftmost / rightmost point has no valid z coordinate then copy the z of the next point
            if np.isnan(points_no_nan[0].z):
                points_no_nan[0].z = points_no_nan[1].z
            if np.isnan(points_no_nan[-1].z):
                points_no_nan[-1].z = points_no_nan[-2].z

            # if the reference point has a nan value, add the interpolated value of the two consequetive points
            for i, p in enumerate(points_no_nan):
                if p.point_type == PointType.REFERENCEPOINT and p.z == np.nan:
                    if i>0 and i<len(points_no_nan)-1:
                        p1 = points_no_nan[i-1]
                        p2 = points_no_nan[i+1]
                        points_no_nan[i].z = round(p1.z + (p.l - p1.l) / (p2.l - p1.l) * (p2.z - p1.z), 2)


            crosssection = Crosssection(
                levee_code = self.levee_code,
                levee_chainage = chainage,
                points=points_no_nan, 
                reference_point=Point3D(x=x, y=y, l=self.left_from_refpoint, point_type=PointType.REFERENCEPOINT),
            )

            if self.rdp_epsilon > 0:
                crosssection.rdp(self.rdp_epsilon)

            result.append(crosssection)

        return result



