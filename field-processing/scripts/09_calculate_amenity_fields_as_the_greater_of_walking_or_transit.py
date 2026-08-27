"""
Step 9: Calculate amenity fields as the greater of Walking or Transit

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- 1. Settings ---
layer = "BC Public Lands"
amenities = ["caf", "ccf", "ef", "emp", "hf", "psef", "srf"]

# --- 2. Add Missing Fields ---
existing_fields = [f.name for f in arcpy.ListFields(layer)]
for am in amenities:
    max_field = f"max_{am}"
    if max_field not in existing_fields:
        print(f"Adding field: {max_field}")
        arcpy.management.AddField(layer, max_field, "DOUBLE")

# --- 3. Calculate Maximums ---
# Build a simple list of fields to use in the cursor
fields = []
for am in amenities:
    fields.extend([f"walk_{am}", f"transit_{am}", f"max_{am}"])

print("Starting maximum calculations...")
try:
    with arcpy.da.UpdateCursor(layer, fields) as cursor:
        for row in cursor:
            # We convert to list to make it mutable
            row_list = list(row)
            for i in range(len(amenities)):
                # walk=i*3, transit=i*3+1, max=i*3+2
                w_val = row_list[i*3] if row_list[i*3] is not None else 0
                t_val = row_list[i*3+1] if row_list[i*3+1] is not None else 0
 
                row_list[i*3+2] = max(w_val, t_val)
 
            # Save the changes for this row
            cursor.updateRow(row_list)
    print("Successfully calculated all maximum fields.")
except Exception as e:
    print(f"An error occurred: {e}")

# Clear cache to force the attribute table to update visually
arcpy.management.ClearWorkspaceCache()
