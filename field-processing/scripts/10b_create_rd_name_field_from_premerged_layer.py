"""
Step 10b: Create RD_Name field (copy from an already-merged layer)

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.

Choose the variant that matches how the "BC Public Lands" layer was built: 10a if the layer was merged locally from the original per-RD source layers, 10b if it came from an already-merged layer (e.g. built by a collaborator) and RD_Name needs to be copied over by matching PID_NUMBER. Note: CZRD = Comox Valley, SUN = Stikine Region.
"""

"""
Copy RD_Name from "BC Public Lands (Aug 7 backup)" to "BC Public Lands"
by matching on the unique key PID_NUMBER.

Run this inside ArcGIS Pro's Python window, or as a standalone script
with an active arcpy license (Pro must be installed).
"""

import arcpy

# ---- CONFIG: update these paths/names to match your project ----
SOURCE_LAYER = r"BC Public Lands (Aug 7 backup)"   # layer/feature class with populated RD_Name
TARGET_LAYER = r"BC Public Lands"                  # layer/feature class with empty RD_Name field
KEY_FIELD = "PID_NUMBER"
VALUE_FIELD = "RD_Name"
# ------------------------------------------------------------------

def build_lookup(source_layer, key_field, value_field):
    """Build {PID_NUMBER: RD_Name} dictionary from the source layer."""
    lookup = {}
    dupe_count = 0
    with arcpy.da.SearchCursor(source_layer, [key_field, value_field]) as cursor:
        for pid, rd_name in cursor:
            if pid is None:
                continue
            if pid in lookup and lookup[pid] != rd_name:
                dupe_count += 1
            lookup[pid] = rd_name
    if dupe_count:
        arcpy.AddWarning(
            f"{dupe_count} PID_NUMBER values had conflicting RD_Name values "
            "in the source layer — last value encountered was kept."
        )
    arcpy.AddMessage(f"Built lookup dictionary with {len(lookup)} entries from source layer.")
    return lookup


def apply_lookup(target_layer, key_field, value_field, lookup):
    """Update RD_Name on the target layer using the PID_NUMBER lookup."""
    matched = 0
    unmatched = 0
    unmatched_pids = []

    with arcpy.da.UpdateCursor(target_layer, [key_field, value_field]) as cursor:
        for row in cursor:
            pid = row[0]
            if pid in lookup:
                row[1] = lookup[pid]
                cursor.updateRow(row)
                matched += 1
            else:
                unmatched += 1
                unmatched_pids.append(pid)

    arcpy.AddMessage(f"Updated {matched} rows in target layer.")
    if unmatched:
        arcpy.AddWarning(f"{unmatched} rows in target layer had no matching PID_NUMBER in source.")
        # Print first 20 unmatched PIDs for spot-checking
        sample = unmatched_pids[:20]
        arcpy.AddWarning(f"Sample unmatched PID_NUMBER values: {sample}")

    return matched, unmatched


def main():
    lookup = build_lookup(SOURCE_LAYER, KEY_FIELD, VALUE_FIELD)
    matched, unmatched = apply_lookup(TARGET_LAYER, KEY_FIELD, VALUE_FIELD, lookup)

    # Basic sanity check against row counts
    source_count = int(arcpy.management.GetCount(SOURCE_LAYER)[0])
    target_count = int(arcpy.management.GetCount(TARGET_LAYER)[0])
    arcpy.AddMessage(f"Source rows: {source_count} | Target rows: {target_count}")
    arcpy.AddMessage(f"Matched: {matched} | Unmatched: {unmatched}")

    if matched + unmatched != target_count:
        arcpy.AddWarning("Matched + unmatched does not equal target row count — check for nulls or duplicate PIDs.")


if __name__ == "__main__":
    main()
