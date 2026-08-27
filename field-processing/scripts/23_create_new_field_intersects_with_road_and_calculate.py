"""
Step 23: Create new field "Intersects_with_road" and calculate

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# Reference the layer by name in the active map
aprx = arcpy.mp.ArcGISProject("CURRENT")
map_ = aprx.activeMap
lyr = map_.listLayers("BC Public Lands")[0]

# 1. Add the new field
arcpy.management.AddField(
    lyr,
    "Intersects_with_road",
    "DOUBLE",
    field_alias="Intersects_with_road"
)

# 2. Calculate it as (Centroid_Road_Dist - THICKNESS) / THICKNESS
arcpy.management.CalculateField(
    lyr,
    "Intersects_with_road",
    "calc_ratio(!Centroid_Road_Dist!, !THICKNESS!)",
    "PYTHON3",
    code_block="""
def calc_ratio(dist, thickness):
    if dist is None or thickness is None or thickness == 0:
        return None
    return (dist - thickness) / thickness
"""
)

print("Field added and calculated on 'BC Public Lands'.")
