from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from mlas_waternet.dataproviders.inputdatabase import DBCrosssectionsTable
from mlas_waternet.secrets import DB_INPUT_URL

engine = create_engine(DB_INPUT_URL)

Base = declarative_base()


