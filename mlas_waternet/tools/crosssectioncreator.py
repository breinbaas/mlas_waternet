# temp hack as long as mlas and geolib are not distributed as packages
import sys
sys.path.append("/home/breinbaas/Programming/packages/mlas")

from mlas.objects.crosssection import Crosssection
from heightdataprovider import HeightDataProvider

# create code to generate crosssections