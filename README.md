# mlas_waternet
MLAS implementation at Waternet

## Installation on Windows

## Databases aanmaken

We use PostGIS and SQLAlchemy

### tables

Snelle tutorial, maak een class als DBCrosssectionsTable in inputdatabase.py en run het script. De tabel wordt automatisch aangemaakt.

Let op dat bij nieuwe databases eerst '''CREATE EXTENSION postgis;''' moet worden uitgevoerd om de GIS functionaliteit toe te voegen.

#### crosssections

id        | int
leveecode | str
chainage  | int
jsonfile  | str
imgfile   | str
date      | date
geom      | LineString 

#### cpts

id        | int
filename  | str
z         | float,2
date      | date
geom      | str
date      | date
geom      | Point 

