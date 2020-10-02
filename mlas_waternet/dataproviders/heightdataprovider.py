import math
import numpy as np
import datetime

from pydantic.dataclasses import dataclass
from typing import List, Tuple

from mlas.objects.points import Point3D
from mlas_waternet.gis.tiles import Tileset, TileType
from mlas_waternet.gis.routes import Routes


@dataclass
class HeightDataProvider:
    """HeightDataProvider class

    Use this class to get height data

    Args:
        tile_type (TileType): type of tiles (see mlaslib.objects.gis.tiles.TileType)
    """

    tile_type: TileType
    tileset: Tileset = None

    def __post_init_post_parse__(self):
        """Executed after pydantic validation, intializes the tileset"""
        if not self.tileset:
            self.tileset = Tileset(tile_type=self.tile_type)

    def get_z(self, x: float, y: float) -> float:
        """Get the z value of the given x,y point

        Args:
            x (float): x coordinate of the point
            y (float): y coordinate of the point

        Returns:
            float: z value at (x,y)
        """
        return self.tileset.get_point3d(x, y).z

    def get(
        self, start: Point3D, end: Point3D, center_to_center_distance: float = 0.5
    ) -> List[Point3D]:
        """
        Generate heightdata

        Args:
            levee_code (str): levee code according to the shapefile with the routes
            start (Point3D): chainage to start crosssection generation, defaults to 0m
            end (Point3D): last chainage for crosssection generation, defaults to 0m
            center_to_center_distance (float): distance between the points

        Returns:
            List[Point3D]: the generated crosssections
        """
        # get all the points even if they are nan
        result = []
        dl = math.sqrt(pow(start.x - end.x, 2) + pow(start.y - end.y, 2))
        for l in np.arange(0, dl + center_to_center_distance * 0.99, center_to_center_distance):
            xp = round(start.x + (l / dl) * (end.x - start.x), 2)
            yp = round(start.y + (l / dl) * (end.y - start.y), 2)
            result.append(Point3D(x=xp, y=yp, z=round(self.get_z(xp, yp), 2)))

        return result
