"""
Step 10a: Create RD_Name field (layer merged locally)

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.

Choose the variant that matches how the "BC Public Lands" layer was built: 10a if the layer was merged locally from the original per-RD source layers, 10b if it came from an already-merged layer (e.g. built by a collaborator) and RD_Name needs to be copied over by matching PID_NUMBER. Note: CZRD = Comox Valley, SUN = Stikine Region.
"""

import arcpy

# ── Configuration ────────────────────────────────────────────────────────────
merged_layer   = "BC Public Lands"
tracking_field = "RD_Name"

original_layers = {
    # Original 16
    "Public_CRD":   "Capital",
    "Public_CVRD":  "Cowichan Valley",
    "Public_MVRD":  "Metro Vancouver",
    "Public_RDN":   "Nanaimo",
    "Public_RDOS":  "Okanagan-Similkameen",
    "Public_SCRD":  "Sunshine Coast",
    "Public_SLRD":  "Squamish-Lillooet",
    "Public_RDKS":  "Kitimat-Stikine",
    "Public_RDKB":  "Kootenay Boundary",
    "Public_RDEK":  "East Kootenay",
    "Public_RDCK":  "Central Kootenay",
    "Public_SRD":   "Strathcona",
    "Public_RDMW":  "Mount Waddington",
    "Public_RDAC":  "Alberni-Clayoquot",
    "Public_FVRD":  "Fraser Valley",
    "Public_CZRD":  "Comox Valley",
    # 12 newly added
    "Public_CBRD":  "Cariboo",
    "Public_CCRD":  "Central Coast",
    "Public_CSRD":  "Columbia Shuswap",
    "Public_NCRD":  "Northern Rockies",
    "Public_NRRM":  "NRRM",
    "Public_PRRD":  "Peace River",
    "Public_QRD":   "qathet",
    "Public_RDBN":  "Bulkley-Nechako",
    "Public_RDCO":  "Central Okanagan",
    "Public_RDFFG": "Fraser Fort George",
    "Public_SUN":   "Stikine Region",
    "Public_TNRD":  "Thompson-Nicola",
}
# ─────────────────────────────────────────────────────────────────────────────

# 1. Add RD_Name if it doesn't exist
existing_fields = [f.name for f in arcpy.ListFields(merged_layer)]
if tracking_field not in existing_fields:
    print(f"Creating field '{tracking_field}'...")
    arcpy.management.AddField(merged_layer, tracking_field, "TEXT", field_length=50)

# 2. Read MERGE_SRC directly from BC Public Lands and write RD_Name in one pass.
# MERGE_SRC values look like "June 29\Public_MVRD" (underscores) or
# "June 29\Public MVRD" (spaces) — normalise both to underscores before matching.
print("Updating RD_Name from MERGE_SRC...")
updated   = 0
unmatched = 0

with arcpy.da.UpdateCursor(merged_layer, ["MERGE_SRC", tracking_field]) as cur:
    for row in cur:
        src = str(row[0]) if row[0] is not None else ""
        src_normalised = src.replace(" ", "_")

        rd_name = None
        for layer_key, rd in original_layers.items():
            if layer_key in src_normalised:
                rd_name = rd
                break

        if rd_name:
            row[1] = rd_name
            cur.updateRow(row)
            updated += 1
        else:
            unmatched += 1

print(f"Done. Updated: {updated:,} | Unmatched: {unmatched:,}")
