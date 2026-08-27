"""
Step 11: Calculate amenity terciles by regional district and categories

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy
import numpy as np

# 1. Configuration
layer = "BC Public Lands"
amenities = ["caf", "ccf", "ef", "emp", "hf", "psef", "srf"]

# 2. Add Category Fields
existing_fields = [f.name for f in arcpy.ListFields(layer)]
for am in amenities:
    cat_field = f"cat_{am}"
    if cat_field not in existing_fields:
        print(f"Adding field: {cat_field}")
        arcpy.management.AddField(layer, cat_field, "TEXT", field_length=15)

# 3. Collect unique RD names
rd_names = sorted(set(
    row[0] for row in arcpy.da.SearchCursor(layer, ["RD_Name"])
    if row[0] is not None
))
print(f"Found {len(rd_names)} RD names: {rd_names}")

# 4. Process each amenity × RD name combination
for am in amenities:
    max_field = f"max_{am}"
    cat_field = f"cat_{am}"

    # --- Calculate tercile thresholds per RD name ---
    thresholds = {}
    for rd in rd_names:
        vals = [
            row[0] for row in arcpy.da.SearchCursor(
                layer, [max_field], where_clause=f"RD_Name = '{rd}'"
            )
            if row[0] is not None and row[0] > 0
        ]

        if not vals:
            print(f"  [{rd}] No non-zero data for {am}, will mark all as 'None'.")
            thresholds[rd] = None
        else:
            t1 = np.percentile(vals, 33.33)
            t2 = np.percentile(vals, 66.66)
            thresholds[rd] = (t1, t2)
            print(f"  [{rd}] {am}: Low <= {t1:.2f} < Medium <= {t2:.2f} < High")

    # --- Update categories using RD-specific thresholds ---
    with arcpy.da.UpdateCursor(layer, ["RD_Name", max_field, cat_field]) as cursor:
        for row in cursor:
            rd, val = row[0], row[1]
            t = thresholds.get(rd)

            if val is None or val == 0 or t is None:
                row[2] = "None"
            elif val <= t[0]:
                row[2] = "Poor"
            elif val <= t[1]:
                row[2] = "Good"
            else:
                row[2] = "Excellent"

            cursor.updateRow(row)

print("Categorization complete! Please refresh your attribute table.")
