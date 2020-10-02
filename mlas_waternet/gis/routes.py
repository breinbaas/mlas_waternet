import math
from typing import List
import shapefile
import dataclasses

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from mlas.objects.points import ChainagePoint, Point3D

from mlas_waternet.settings import SETTINGS


class Route(BaseModel):
    """A Route contains the chainage and corresponding RD coordinates for the reference
    line of a levee
    
    Args:
        name (str): levee name
    """

    name: str = ""
    chainage_points: List[ChainagePoint] = []

    @property
    def max_chainage(self):
        """Returns the maximum chainage"""
        if len(self.chainage_points) == 0:
            raise IndexError("No chainage points in this route")
        return self.chainage_points[-1].chainage

    @property
    def min_chainage(self):
        """Returns the minimum chainage"""
        if len(self.chainage_points) == 0:
            raise IndexError("No chainage points in this route")
        return self.chainage_points[0].chainage

    def xya_at_chainage(self, chainage: int):
        """Return the x and y coordinate and orientation of the given chainage

        NOTE the the orientation expects the water to be on the right side of
        the route line


                  water 
                    ^
                    |                
        start --------------- end

        Args:
            chainage (int): chainage on the route

        Returns:
            x (float): x-coordinate of the given chainage
            y (float): y-coordinate of the given chainage
            a (float): alpha, orientation of the given chainage

        Todo:
            * check if orientation story above is correct
        """
        for i in range(1, len(self.chainage_points)):
            m1, x1, y1 = (
                self.chainage_points[i - 1].chainage,
                self.chainage_points[i - 1].point3d.x,
                self.chainage_points[i - 1].point3d.y,
            )
            m2, x2, y2 = (
                self.chainage_points[i].chainage,
                self.chainage_points[i].point3d.x,
                self.chainage_points[i].point3d.y,
            )

            if m1 <= chainage <= m2:
                x = x1 + (chainage - m1) / (m2 - m1) * (x2 - x1)
                y = y1 + (chainage - m1) / (m2 - m1) * (y2 - y1)
                alpha = math.atan2((y1 - y2), (x1 - x2))
                return round(x, 2), round(y, 2), alpha

        raise ValueError(
            f"Unknown chainage {chainage} at route {self.name} with minimum chainage {self.min_chainage} and max chainage {self.max_chainage}"
        )

    def get_bounding_box(self, margin=0.0):
        """Get the bounding box of the route coordinates"""
        result = [1e9, 1e9, -1e9, -1e9]  # [xmin, ymin, xmax, ymax]
        for point in self.chainage_points:
            if point.point3d.x < result[0]:
                result[0] = point.point3d.x
            if point.point3d.x > result[2]:
                result[2] = point.point3d.x
            if point.point3d.y < result[1]:
                result[1] = point.point3d.y
            if point.point3d.y > result[3]:
                result[3] = point.point3d.y
        return [
            result[0] - margin,
            result[1] - margin,
            result[2] + margin,
            result[3] + margin,
        ]


@dataclass
class Routes:
    """The Routes class contains all available routes based on the information in
    the given shapefile

    NOTE the shapefile expects the field with the levee codes to be named DWKIDENT
    adjust the code if defined otherwise

    Args:
        shapefile (str): filelocation of the shapefile
    """

    routes: dict = dataclasses.field(default_factory=dict)
    shapefile: str = SETTINGS["shapefile_routes"]

    def __post_init_post_parse__(self):
        """Called after validation, reads the given shapefile"""
        try:
            self._read_from_shapefile()
        except Exception as e:
            raise ValueError(f"Error reading {self.shapefile} with error {e}")

    def _read_from_shapefile(self):
        """Reads the shapefile"""
        shape = shapefile.Reader(self.shapefile)
                
        for i in range(len(shape.records())):
            record = shape.records()[i]
            geometry = shape.shapes()[i]
            rt = Route(name=record['DWKIDENT'])
            
            m = 0
            for j in range(len(geometry.points)):
                pt = geometry.points[j]
                if j == 0:
                    rt.chainage_points.append(
                        ChainagePoint(chainage=0, point3d=Point3D(x=pt[0], y=pt[1]))
                    )
                else:
                    dx = rt.chainage_points[-1].point3d.x - pt[0]
                    dy = rt.chainage_points[-1].point3d.y - pt[1]
                    m += math.sqrt(dx ** 2 + dy ** 2)
                    rt.chainage_points.append(
                        ChainagePoint(chainage=int(m), point3d=Point3D(x=pt[0], y=pt[1]))
                    )

            self.routes[rt.name] = rt

    def get_levee_codes(self):
        """Return the available levee codes

        Returns:
            List[str]: list with levee codes
        """
        return self.routes.keys()

    def get_by_levee_code(self, dtcode):
        """Get a route by it's levee code

        Args:
            levee_code (str): code of the levee

        Returns:
            route (Route): the according route
        """
        if dtcode in self.routes.keys():
            return self.routes[dtcode]
        else:
            return None


if __name__ == "__main__":
    rts = Routes()
    print(rts.get_levee_codes())
    print(rts.routes["A143"].chainage_points)  #  mxy_to_csv('A143.csv')
