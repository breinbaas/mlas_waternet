# mlas_waternet
MLAS implementation at Waternet

## Installation on Windows

#### mod_spatialite.dll

To make Python work with spatialite databases you need to install the '''mod_spatialite.dll''' found at https://www.sqlite.org/download.html 

Note that if you have QGis installed you will find this under '''C:\Program Files\QGIS 3.14\bin''' (or any other location you might have chosen for QGis)

Be sure to add the directory containing this dll to the PATH environment in Windows

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

