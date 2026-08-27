"""
Step 1b: Update Underutilized

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Configuration ---
layer_name = "BC Public Lands"        # Update to match your layer name
underutilized_field = "Underutilized"
pct_field = "PercentImproveLand"

# --- Update Underutilized field ---
where_y = f"{pct_field} > 0 AND {pct_field} < 20"
where_n = f"NOT ({where_y})"

with arcpy.da.UpdateCursor(layer_name, [underutilized_field, pct_field]) as cursor:
    updated_y = 0
    updated_n = 0
    for row in cursor:
        pct = row[1]
        if pct is not None and 0 < pct < 20:
            row[0] = "Y"
            updated_y += 1
        else:
            row[0] = "N"
            updated_n += 1
        cursor.updateRow(row)

print(f"Set to 'Y' (0 < PercentImproveLand < 20): {updated_y} rows")
print(f"Set to 'N' (all others, including 0 and null): {updated_n} rows")
print("Done.")
