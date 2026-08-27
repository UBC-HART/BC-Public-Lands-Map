"""
Step 7: Calculate grocery store proximity

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- 1. Settings ---
layer = "BC Public Lands"
min_field = "min_gs"
cat_field = "cat_gs"

# --- 2. Setup Fields ---
existing_fields = [f.name for f in arcpy.ListFields(layer)]
if min_field not in existing_fields:
    arcpy.management.AddField(layer, min_field, "DOUBLE")
if cat_field not in existing_fields:
    arcpy.management.AddField(layer, cat_field, "TEXT", field_length=15)

# --- 3. Processing with expanded check ---
# Fields: 0:w1, 1:t1, 2:w3, 3:t3, 4:w5, 5:t5, 6:min_gs, 7:cat_gs
fields = ["walk_gs_1", "transit_gs_1", "walk_gs_3", "transit_gs_3", "walk_gs_5", "transit_gs_5", min_field, cat_field]

print("Processing grocery access (Checking gs_1, gs_3, and gs_5)...")
with arcpy.da.UpdateCursor(layer, fields) as cursor:
    for row in cursor:
        w1, t1, w3, t3, w5, t5 = row[0], row[1], row[2], row[3], row[4], row[5]
 
        # Mode is valid if ANY of the three stores have a non-zero/non-null value
        walk_is_valid = any(v != 0 and v is not None for v in [w1, w3, w5])
        transit_is_valid = any(v != 0 and v is not None for v in [t1, t3, t5])

        final_time = -1.0

        if walk_is_valid and transit_is_valid:
            # Both valid; compare 1st store times
            v_w1 = w1 if w1 is not None else 0.0
            v_t1 = t1 if t1 is not None else 0.0
            final_time = float(min(v_w1, v_t1))
        elif walk_is_valid:
            # Only walk has data; take its 1st store time
            final_time = float(w1) if w1 is not None else 0.0
        elif transit_is_valid:
            # Only transit has data; take its 1st store time
            final_time = float(t1) if t1 is not None else 0.0
 
        # Assign the time
        row[6] = final_time
 
        # Categorize
        if final_time == -1:
            category = "None"
        elif 0 <= final_time <= 10:
            category = "Excellent"
        elif 10 < final_time <= 20:
            category = "Good"
        elif 20 < final_time <= 30:
            category = "Poor"
        else:
            category = "None"
 
        row[7] = category
        cursor.updateRow(row)

arcpy.management.ClearWorkspaceCache()
print("Done! Updated min_gs and cat_gs based on gs_1, gs_3, and gs_5 checks.")
