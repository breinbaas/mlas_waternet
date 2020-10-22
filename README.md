# mlas_waternet
MLAS implementation at Waternet

## Installation on Windows

## Databases aanmaken

We use PostGIS and SQLAlchemy

### Example command to add rasterdata to database:

C:\Program Files\PostgreSQL\12\bin>raster2pgsql.exe -s 28992 -I -C -M "c:\Users\brein\Documents\GIS DataBase\Stijghoogte\Stijghoogte eerste wvp1.tif" -F -t 100x100 public.stijghoogte | psql.exe -d uitgangspunten -U postgres

see https://docs.boundlessgeo.com/suite/1.1.0/dataadmin/pgGettingStarted/raster2pgsql.html

### tables

Snelle tutorial, maak een class als DBCrosssectionsTable in inputdatabase.py en run het script. De tabel wordt automatisch aangemaakt.

Let op dat bij nieuwe databases eerst '''CREATE EXTENSION postgis;''' moet worden uitgevoerd om de GIS functionaliteit toe te voegen.
Idem '''CREATE EXTENSION postgis_raster;''' om rasterbestanden toe te staan



#### crosssections

field | type | description
--- | --- | --- 
id | int | unique id
leveecode | str | code of the levee (for example A145
chainage | int | chainage of the crosssection
jsonfile | str | filepath of the json data
imgfile | str | filepath of the image file
date | date | date of the crosssection
geom | LineString | geographical line between start- and endpoint

#### cpts

field | type | description
--- | --- | --- 
id | int | unique id
filename | str | filename of the CPT
z | float,2 | top level of the CPT
date | date | date od the CPT
geom | Point | geographical point of the CPT


## TIPS QGis

* Use the processing toolbox option **offset curve** to create a polder referenceline.
* Use Export | Save Selected Features As and choose GeoJSON as filetype. Be sure to choose the right CRS (EPS:28992) and GeometryType = LineString





