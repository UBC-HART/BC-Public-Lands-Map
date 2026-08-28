# MosaiceProjectSlope_DEM20000.R
# Mosaices the LBC 20000 DEMs into single virtual DEM
# Creates virtual DEM, writes to a file 
# Project to BC Albers, optionally writes to a file
# Creates a degree slope file
# Code is provided for local and UBC ARC
# Update RD and if necessary file paths and file names.

# Ian Parfitt 27 Aug 2026

# Install and load the terra package if not already installed

library(terra) 
# Cap terra's memory processing threshold to match slurm request
terraOptions(memmax=180, memfrac=0.5)

RDinit <- "PRRD"

# setwd("C:/working/GISdata/LidarBC/PRRD/DEM20000")
setwd('/scratch/st-craigmac-1/iparfitt/sockeye_jobs')


# 1. Select input files - either by directory or by individual files

# Directory: List all the DEM files (e.g., .tif files) in the directory
# full.names = TRUE ensures you get the full file path
# input_path <- '/scratch/st-craigmac-1/LidarBCSource/PRRD/DEM20000'
# input_path <- "C:/working/GISdata/LidarBC/PRRD/DEM20000"
# dem_files <- list.files(path = input_path, pattern = "\\.tif$", full.names = TRUE)

# Individual files: Define the full paths to your TIFF files
dem_files <- c(
   "PRRD_LBC_20000_y24alb_DEM.tif",
   "PRRD_LBC_20000_y21alb_DEM.tif"
 )

# 2 Create virtual DEM raster
vfn <- paste0(RDinit, "_LBC_20000_DEMalb.vrt")

vrt_mosaic <- vrt(
  dem_files, 
  vfn, 
  options = c(
    "-resolution", "highest", 
    "-srcnodata", "nan",
    "-vrtnodata", "nan"
  ), 
  overwrite = TRUE
)


# WriteRaster
vfnt <- paste0(RDinit, "_LBC_20000_DEMalb.tif")
writeRaster(vrt_mosaic, filename = vfnt, filetype="GTiff", overwrite = TRUE, wopt=list(gdal=c("COMPRESS=LZW")))


# 3. Project into BC Albers using EPSG:3005
# Using bilinear interpolation for continuous terrain data
# Set res to cell size
vrt_dem_albers <- project(vrt_mosaic, "epsg:3005", method = "bilinear", res = 1)

# Optional: Save and print the Albers DEM 
# Using LZW compression with PREDICTOR=2 for integer data compression optimization
# vfna <- paste0(RDinit, "_LBC_20000_DEM_alb.tif")
# writeRaster(vrt_dem_albers, 
#            filename = vfna, 
#            datatype = "INT2S", 
#            gdal = c("COMPRESS=LZW", "PREDICTOR=2"), 
#            overwrite = TRUE)

# 4. Calculate slope in degrees
vfns <- paste0(RDinit, "_LBCHRDEM_SLP_alb.tif")
slope_deg <- terrain(vrt_mosaic,v="slope",unit = "degrees", filename = vfns, overwrite = TRUE, gdal=c("COMPRESS=LZW", "TILED=YES"))





