"""
Step 25: Change nulls to "No data available" for "Inferred Building Typology simple" field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# Reference the layer by its TOC name in the active Pro project
# If it's nested inside a group layer, use "GroupName\\BC Public Lands" instead
layer_name = "BC Public Lands"
field_name = "Inferred_Building_Typology_simple"
replacement_value = "No data available"

aprx = arcpy.mp.ArcGISProject("CURRENT")
active_map = aprx.activeMap
lyr = active_map.listLayers(layer_name)[0]

updated_count = 0

with arcpy.da.UpdateCursor(lyr, [field_name]) as cursor:
    for row in cursor:
        if row[0] is None:
            row[0] = replacement_value
            cursor.updateRow(row)
            updated_count += 1

print(f"Updated {updated_count} null values in '{field_name}' to '{replacement_value}'.")
