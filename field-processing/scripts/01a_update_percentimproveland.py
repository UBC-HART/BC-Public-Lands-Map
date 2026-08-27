"""
Step 1a: Update PercentImproveLand

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Configuration ---
layer_name = "BC Public Lands"        # Update to match your layer name
field_name = "PercentImproveLand"

# --- Update nulls to 0 ---
lyr = arcpy.management.MakeFeatureLayer(layer_name, "lyr_temp")[0]

null_count_before = int(arcpy.management.GetCount(
    arcpy.management.SelectLayerByAttribute(lyr, "NEW_SELECTION", f"{field_name} IS NULL")[0]
)[0])

print(f"Nulls found: {null_count_before}")

if null_count_before > 0:
    with arcpy.da.UpdateCursor(layer_name, [field_name], f"{field_name} IS NULL") as cursor:
        updated = 0
        for row in cursor:
            row[0] = 0
            cursor.updateRow(row)
            updated += 1
    print(f"Updated {updated} rows: null → 0")
else:
    print("No null values found — nothing to update.")

arcpy.management.SelectLayerByAttribute(lyr, "CLEAR_SELECTION")
print("Done.")
