Readme.md

The objective of the project is to identify all public land parcels in BC, and then evaluate them for housing (especially affordable housing) suitability.

This project includes Python files used for spatial data processing using arcpy and R files used to process digital elevation data.

The overall workflow begins with creating a public land data layer for BC using ParcelMap_SelectBCPub.py.
Next, this is joined to BC Assessment spatial layers for each jurisdiction witin a Regional District in BC using JoinRDTables.py.  
The public land for each jurisdiction within a Regional District are then appended together to create a single Regional District public land layer.  Many other datasets are then spatially joined to this layer to add attributes to use in evaluating housing suitability.  This all happens in AppendRD.py.

Two utility python files are used by these three python files.  JoinUtil.py is used for the by JoinRDTables.py, while FunctionUtility is used by all three.

In the prototype RD, Metro Vancouver Regional District, a DEM for most of the RD was created after the BCA data was joined. However, this soon proved infeasible for the whole province.  In order to reduce the time and space needed to create a slope raster for each RD, the final public land layer for each RD is buffered by 1000m and used to select DEM tiles that are then mosaiced together, projected into BC Albers coordinate reference system, and then used to derived a degree slope layer that covers only as much of the public land as possible.  This is a bit out of sequence so an UpdateMean.py file is used to revise the slope mean.

Ian Parfitt  27 Aug 2026
