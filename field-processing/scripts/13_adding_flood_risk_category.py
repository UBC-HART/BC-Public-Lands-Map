"""
Step 13: Adding flood risk category

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# 1. Setup
layer_name = "BC Public Lands"
in_field = "Flood_Risk"
out_field = "Flood_Risk_Cat"

# 2. Add Flood_Risk_Cat field if it doesn't exist
existing_fields = [f.name for f in arcpy.ListFields(layer_name)]
if out_field not in existing_fields:
    print(f"Adding field: {out_field}")
    arcpy.management.AddField(layer_name, out_field, "TEXT", field_length=15)

# 3. Update categories
with arcpy.da.UpdateCursor(layer_name, [in_field, out_field]) as cursor:
    for row in cursor:
        val = row[0]
        if val is None:
            row[1] = None
        elif val == 1: row[1] = "Very Low"
        elif val == 2: row[1] = "Low"
        elif val == 3: row[1] = "Low-Moderate"
        elif val == 4: row[1] = "High-Moderate"
        elif val == 5: row[1] = "High"
        elif val == 6: row[1] = "Very High"
        else:          row[1] = None
        cursor.updateRow(row)

print("Field 'Flood_Risk_Cat' has been updated.")
