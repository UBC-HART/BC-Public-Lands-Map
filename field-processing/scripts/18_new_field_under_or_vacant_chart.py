"""
Step 18: New field: Under_or_Vacant_chart

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Configuration ---
layer_name = "BC Public Lands"
new_field = "Under_or_Vacant_chart"
vacant_field = "Vacant"
underutilized_field = "Underutilized"

# --- Add new field ---
arcpy.management.AddField(layer_name, new_field, "TEXT", field_length=30)
print(f"Added field: {new_field}")

# --- Populate field ---
with arcpy.da.UpdateCursor(layer_name, [new_field, vacant_field, underutilized_field]) as cursor:
    vacant_count = 0
    underutilized_count = 0
    neither_count = 0

    for row in cursor:
        if row[1] == "Y":
            row[0] = "Vacant"
            vacant_count += 1
        elif row[2] == "Y":
            row[0] = "Underutilized"
            underutilized_count += 1
        else:
            row[0] = "Not Vacant or Underutilized"
            neither_count += 1
        cursor.updateRow(row)

print(f"\nResults:")
print(f"  Vacant:                    {vacant_count:>8} rows")
print(f"  Underutilized:             {underutilized_count:>8} rows")
print(f"  Not Vacant or Underutilized: {neither_count:>6} rows")
print("Done.")
