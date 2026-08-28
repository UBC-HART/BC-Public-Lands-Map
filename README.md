Readme.md

The objective of the project is to identify all public land parcels in BC, and then evaluate them for housing (especially affordable housing) suitability.

This project includes Python files used for spatial data processing using arcpy and R files used to process digital elevation data.

The overall workflow begins with creating a public land data layer for BC using ParcelMap_SelectBCPub.py.
Next, this is joined to BC Assessment spatial layers for each jurisdiction witin a Regional District in BC using JoinRDTables.py.  
The public land for each jurisdiction within a Regional District are then appended together to create a single Regional District public land layer.  Many other datasets are then spatially joined to this layer to add attributes to use in evaluating housing suitability.  This all happens in AppendRD.py.

Two utility python files are used by these three python files.  JoinUtil.py is used for the by JoinRDTables.py, while FunctionUtility is used by all three.

In the prototype RD, Metro Vancouver Regional District, a DEM for most of the RD was created after the BCA data was joined. However, this soon proved infeasible for the whole province.  In order to reduce the time and space needed to create a slope raster for each RD, the final public land layer for each RD is buffered by 1000m and used to select DEM tiles that are then mosaiced together, projected into BC Albers coordinate reference system, and then used to derived a degree slope layer that covers only as much of the public land as possible.  This is a bit out of sequence so an UpdateMean.py file is used to revise the slope mean.

Several python files were developed to automate the selection and downloading of DEM raster TIF files from LidarBC and the federal HRDEM program. RDPubExtent.py creates an area of interest layer for a given RD by buffering the public land data for that RD by 1000m. LidarBC_import_tifs.py and HRDEM_import_tifs are then used to select and download the LidarBC and HRDEM files respectively.

R with the terra library was used to mosaic TIF tiles together into a virtual mosaic, write it out to a TIF file, project it to BC Albers and create a degree slope.  MosiacProjectSlope_DEM20000.R can be modified for the DEM2500 tiles or the HRDEM tiles.  We used both a local instance of R and UBC Advanced Research Computing (ARC) online R instances; the main difference in the code is the directory paths where the input tiles are stored and output data will be saved. We found that some RDs included multiple UTM Zones, vertical datums, or cell sizes: these need to be processed separately. We created separate folders (i.e. .../LidarBC/<RD>/DEM20000/UTM10  and .../LidarBC/<RD>/DEM20000/UTM9), moved appropriate input tiles into them, and then processed each.

All the final public land layers for all regional districts were copied to a geodatabase, and MergeALLRDs.py was then used to create the final "BC Public Lands" layer.

Once the Regional District public land layers are appended together, the resulting "BC Public Lands" layer is further processed to add the fields used for parcel scoring and the map's public-facing attributes. These field-processing scripts, along with a full step index, are in the field-processing folder.

Ian Parfitt  27 Aug 2026
