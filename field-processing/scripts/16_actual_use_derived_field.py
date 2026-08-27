"""
Step 16: Actual use derived field

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# 1. Setup
layer_name = "BC Public Lands"
lookup_table = "June22_Lookup_ExcelToTable" #**MAY NEED TO UPDATE THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**
out_field = "Actual_Use_Derived"

# 2. Add Actual_Use_Derived field if it doesn't exist
existing_fields = [f.name for f in arcpy.ListFields(layer_name)]
if out_field not in existing_fields:
    print(f"Adding field: {out_field}")
    arcpy.management.AddField(layer_name, out_field, "TEXT", field_length=100)

# 3. Build lookup dictionary from Sheet1$
lookup = {}
with arcpy.da.SearchCursor(lookup_table, ["Actual_Use_Description", "Category"]) as cursor:
    for row in cursor:
        if row[0] is not None:
            lookup[row[0]] = row[1]

print(f"Loaded {len(lookup)} entries from {lookup_table}")

# 4. Update Actual_Use_Derived using the lookup
with arcpy.da.UpdateCursor(layer_name, ["ACTUAL_USE_DESCRIPTION", out_field]) as cursor:
    for row in cursor:
        val = row[0]
        row[1] = lookup.get(val) or "n/a"
        cursor.updateRow(row)

print("Field 'Actual_Use_Derived' has been updated.")
