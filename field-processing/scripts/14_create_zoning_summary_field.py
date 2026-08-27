"""
Step 14: Create Zoning summary field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# 1. Setup
layer_name = "BC Public Lands"
out_field = "Zoning_summary"

# 2. Add Zoning_summary field if it doesn't exist
existing_fields = [f.name for f in arcpy.ListFields(layer_name)]
if out_field not in existing_fields:
    print(f"Adding field: {out_field}")
    arcpy.management.AddField(layer_name, out_field, "TEXT", field_length=255)

# 3. Update Zoning_summary
fields = ["Zoning", "Zoning_1", "General_Zone", out_field]
with arcpy.da.UpdateCursor(layer_name, fields) as cursor:
    for row in cursor:
        zoning, zoning_1, general_zone = row[0], row[1], row[2]

        if zoning and str(zoning).strip():
            row[3] = zoning
        elif zoning_1 and str(zoning_1).strip():
            row[3] = zoning_1
        elif general_zone and str(general_zone).strip():
            row[3] = general_zone
        else:
            row[3] = "n/a"

        cursor.updateRow(row)

print("Field 'Zoning_summary' has been updated.")
