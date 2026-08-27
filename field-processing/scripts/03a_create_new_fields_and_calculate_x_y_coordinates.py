"""
Step 3a: Create new fields and calculate X & Y coordinates

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# Define your layer variable
polygon_layer = "BC Public Lands"

# Add fields to hold the double-precision floating numbers
arcpy.management.AddField(in_table=polygon_layer, field_name="X_Coord", field_type="DOUBLE")
arcpy.management.AddField(in_table=polygon_layer, field_name="Y_Coord", field_type="DOUBLE")


import arcpy

polygon_layer = "BC Public Lands"

# Run the geometry calculation tool forcing WGS 1984 (4326) Decimal Degrees
arcpy.management.CalculateGeometryAttributes(
    in_features=polygon_layer,
    geometry_property=[["X_Coord", "CENTROID_X"], ["Y_Coord", "CENTROID_Y"]],
    coordinate_system=arcpy.SpatialReference(4326) # 4326 is WGS 1984 (Lat/Long)
)
