"""
Step 1d: Update Vacant values to "Y" if PercentImproveLand = 0 and "N" otherwise

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Configuration ---
layer_name = "BC Public Lands"        # Update to match your layer name
vacant_field = "Vacant"
pct_field = "PercentImproveLand"

# --- Update Vacant based on PercentImproveLand ---
with arcpy.da.UpdateCursor(layer_name, [vacant_field, pct_field]) as cursor:
    y_count = 0
    n_count = 0
    for row in cursor:
        if row[1] == 0:
            row[0] = "Y"
            y_count += 1
        else:
            row[0] = "N"
            n_count += 1
        cursor.updateRow(row)

print(f"Set Vacant = 'Y' (PercentImproveLand = 0): {y_count} rows")
print(f"Set Vacant = 'N' (PercentImproveLand != 0): {n_count} rows")
print("Done.")
