from enum import IntEnum
import os, glob
import dataclasses
import numpy as np

from pathlib import Path
from typing import Tuple
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from pydantic.types import List, Optional
import rasterio as rio

from mlas.objects.points import Point3D
from mlas_waternet.settings import SETTINGS
from mlas_waternet.const import TILES_INIFILENAME


class TileType(IntEnum):
    AHN3 = 0
    WATERBOTTOM = 1
    DITCHES = 2
    HYDRAULIC_HEAD = 3


class TileBoundary(BaseModel):
    left: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    top: float = 0.0


class TileResolution(BaseModel):
    x: float = 0.0
    y: float = 0.0


class TileShape(BaseModel):
    columns: int = 0
    rows: int = 0


class Tile(BaseModel):
    """A tile is a geotiff file with x,y,z data"""

    boundary: TileBoundary = TileBoundary()
    resolution: TileResolution = TileResolution()
    shape: TileShape = TileShape()
    data: np.ndarray = None
    nodata: float = None
    filename: str = ""

    class Config:
        arbitrary_types_allowed = True  # for np.ndarray

    def _read(self) -> None:
        """Read the geotiff file using GDAL, see the README for common GDAL problems"""
        if self.data is None:
            r = rio.open(self.filename)
            self.data = r.read(1, masked=True).data

    def get_z(self, x: float, y: float) -> float:
        """Get the z value at the given x,y coordinates

        Args:
            x (float): x coordinate of the point
            y (float): y coordinate of the point

        Returns:
            x (float): z coordinate of the point or np.nan
        """
        self._read()
        dx = x - self.boundary.left
        dy = self.boundary.top - y

        idx = int(round(dx / self.resolution.x))
        if idx < 0 or idx >= self.shape.columns:
            return None

        idy = int(round(dy / self.resolution.y))
        if idy < 0 or idy >= self.shape.rows:
            return None

        z = self.data[idy, idx]
        if z == self.nodata:
            return None
        return z


@dataclass
class Tileset:
    """A tileset is a collection of tiles, since they cannot be loaded into 
    memory because of the size the tileset will load the tiles if they are 
    necessary.
    
    The tile files will be preprocessed on first sight to create an ini file 
    to quickly find the bounding boxes.
    """

    tiles: List[Tile] = dataclasses.field(default_factory=list)
    tile_type: TileType = TileType.AHN3

    def __post_init_post_parse__(self):
        """Called after validation, sets up the tiles and ini file if needed"""
        if self.tile_type == TileType.AHN3:
            self._tilesdir = SETTINGS["filepath_ahn3_geotiff"]
        elif self.tile_type == TileType.WATERBOTTOM:
            self._tilesdir = SETTINGS["filepath_waterbodem"]
        elif self.tile_type == TileType.DITCHES:
            self._tilesdir = SETTINGS["filepath_ditches"]
        elif self.tile_type == TileType.HYDRAULIC_HEAD:
            self._tilesdir = SETTINGS["filepath_hydraulic_head"]
        else:
            raise ValueError(f"Unknown tile type {self.tile_type}")

        self._inifile = Path(self._tilesdir) / TILES_INIFILENAME
        self._initialize_available_data()

    def _initialize_available_data(self) -> None:
        """Checks if an ini file is available / valid"""
        if os.path.isfile(self._inifile):
            self._read_ini()
        else:
            self._setup_ini()

    def _setup_ini(self) -> None:
        """Generates an ini file of the tiles"""
        fout = open(self._inifile, "w")

        files = glob.glob(self._tilesdir + "/*.tif")

        if len(files) == 0:
            files = glob.glob(self._tilesdir + "/*.img")

        fout.write("file;left;right;bottom;top;resolution_x;resolution_y;rows;columns;no_data\n")
        for file in files:
            r = rio.open(file)
            fout.write(
                "{};{};{};{};{};{};{};{};{};{}\n".format(
                    file,
                    r.bounds.left,
                    r.bounds.right,
                    r.bounds.bottom,
                    r.bounds.top,
                    r.res[1],
                    r.res[0],
                    r.meta["width"],
                    r.meta["height"],
                    r.meta["nodata"],
                )
            )
        fout.close()
        self._read_ini()

    def _read_ini(self) -> None:
        """Read the ini file for fast access"""
        fin = open(self._inifile)
        lines = fin.readlines()
        fin.close()
        for line in lines[1:]:
            args = [s.strip() for s in line.split(";")]
            tile = Tile()
            tile.filename = args[0]
            tile.resolution.x = float(args[5])
            tile.resolution.y = float(args[6])
            tile.boundary.left = float(args[1]) - tile.resolution.x / 2.0
            tile.boundary.right = float(args[2]) - tile.resolution.x / 2.0
            tile.boundary.bottom = float(args[3]) + tile.resolution.y / 2.0
            tile.boundary.top = float(args[4]) + tile.resolution.y / 2.0
            tile.shape.columns = int(args[7])
            tile.shape.rows = int(args[8])
            tile.nodata = float(args[9])
            self.tiles.append(tile)

    def get_point3d(self, x: float, y: float) -> Point3D:
        """Generate a point at x, y and fill in the z based on the tile data

        Args:
            x (float): x coordinate of the point
            y (float): y coordinate of the point

        Returns:
            Point3D: point with the z coordinate filled in (or np.nan if not available)
        """
        for tile in self.tiles:
            if (
                tile.boundary.left <= x <= tile.boundary.right
                and tile.boundary.bottom <= y <= tile.boundary.top
            ):
                z = tile.get_z(x, y)
                if z is not None:
                    return Point3D(x=x, y=y, z=z)
        return Point3D(x=x, y=y, z=np.nan)


if __name__ == "__main__":
    ts = Tileset(tile_type=TileType.HYDRAULIC_HEAD)
    #ts.

    for x in range(122000, 122100):
        print(ts.get_point3d(x, 478628))
