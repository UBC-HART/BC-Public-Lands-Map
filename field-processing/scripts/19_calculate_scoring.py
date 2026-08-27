"""
Step 19: Calculate scoring

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

# --- Configuration ---
layer_name = "BC Public Lands"

# --- Field definitions (name, type, length) ---
new_fields = [
    ("Scr_emp",       "SHORT", None),
    ("Scr_transit",   "SHORT", None),
    ("Scr_schools",   "SHORT", None),
    ("Scr_health",    "SHORT", None),
    ("Scr_grocery",   "SHORT", None),
    ("Scr_pharmacy",  "SHORT", None),
    ("Scr_srf",       "SHORT", None),
    ("Scr_childcare", "SHORT", None),
    ("Scr_amenity",   "SHORT", None),
    ("Scr_density",   "SHORT", None),
    ("Scr_devcat",    "SHORT", None),
    ("Scr_vac_under", "SHORT", None),
    ("Scr_slope",     "SHORT", None),
    ("Scr_flood",     "SHORT", None),
    ("Scr_shape",     "SHORT", None),
    ("Scr_fire",      "SHORT", None),
    ("Scr_site",      "SHORT", None),
    ("BCPLM_Score",   "SHORT", None),
]

# --- Add fields ---
print("Adding fields...")
for field_name, field_type, field_length in new_fields:
    arcpy.management.AddField(layer_name, field_name, field_type)
    print(f"  Added: {field_name}")

# --- Scoring functions ---

def score_amenity_critical(value):
    return {"None": 0, "Poor": 2, "Good": 4, "Excellent": 6}.get(value, 0)

def score_amenity_normal(value):
    return {"None": 0, "Poor": 1, "Good": 2, "Excellent": 3}.get(value, 0)

def score_density(max_d, toa_d):
    val = max(max_d or 0, toa_d or 0)
    if val >= 200:   return 14
    if val >= 140:   return 11
    if val >= 25:    return 8
    return 4

def score_devcat(value):
    return {"Very Low": 1, "Low": 2, "Moderate": 3, "High": 4, "Very High": 5}.get(value, 0)

def score_vac_under(vacant, underutilized):
    if vacant == "Y" and underutilized == "Y":
        return None  # Conflict flag
    if vacant == "Y":        return 25
    if underutilized == "Y": return 15
    return 0

def score_slope(mean):
    if mean is None: return 0
    if mean < 1:     return 5
    if mean < 5:     return 4
    if mean < 10:    return 3
    if mean < 15:    return 2
    if mean < 20:    return 1
    return 0

def score_flood(value):
    return {"Very Low": 5, "Low": 4, "Low-Moderate": 3, "High-Moderate": 3, "High": 2, "Very High": 1}.get(value, 0)

def score_shape(value):
    return 0 if value == "Irregular" else 5

def score_fire(value):
    return {
        "No Threat": 5,
        "Water":     5,
        "Low":       4,
        "Moderate":  3,
        "High":      2,
        "Extreme":   1,
        "No Data (Private Land)":                  3,
        "No Data (Private managed Forest Land)":   3,
    }.get(value, 0)

# --- Cursor fields ---
input_fields = [
    "cat_emp", "Transit_cat", "cat_ef", "cat_hf",   # Critical amenities
    "cat_gs", "Pharmacy_cat", "cat_srf", "cat_ccf",  # Normal amenities
    "Max_Density", "TOA_Density",                     # Density
    "DevCategory",                                    # Recent development
    "Vacant", "Underutilized",                        # Vacant & underutilized
    "MEAN",                                           # Slope
    "Flood_Risk_Cat",                                 # Flood risk
    "Irregular",                                      # Shape
    "Fire_Risk",                                      # Fire risk
]

output_fields = [
    "Scr_emp", "Scr_transit", "Scr_schools", "Scr_health",
    "Scr_grocery", "Scr_pharmacy", "Scr_srf", "Scr_childcare",
    "Scr_amenity",
    "Scr_density",
    "Scr_devcat",
    "Scr_vac_under",
    "Scr_slope", "Scr_flood", "Scr_shape", "Scr_fire",
    "Scr_site",
    "BCPLM_Score",
]

all_fields = input_fields + output_fields

# --- Populate scores ---
print("\nCalculating scores...")
conflict_count = 0
total_rows = 0

with arcpy.da.UpdateCursor(layer_name, all_fields) as cursor:
    for row in cursor:
        # Unpack inputs
        (cat_emp, transit_cat, cat_ef, cat_hf,
         cat_gs, pharmacy_cat, cat_srf, cat_ccf,
         max_density, toa_density,
         dev_category,
         vacant, underutilized,
         mean_slope,
         flood_risk_cat,
         irregular,
         fire_risk) = row[:len(input_fields)]

        # --- Amenity scores ---
        scr_emp       = score_amenity_critical(cat_emp)
        scr_transit   = score_amenity_critical(transit_cat)
        scr_schools   = score_amenity_critical(cat_ef)
        scr_health    = score_amenity_critical(cat_hf)
        scr_grocery   = score_amenity_normal(cat_gs)
        scr_pharmacy  = score_amenity_normal(pharmacy_cat)
        scr_srf       = score_amenity_normal(cat_srf)
        scr_childcare = score_amenity_normal(cat_ccf)
        scr_amenity   = (scr_emp + scr_transit + scr_schools + scr_health +
                         scr_grocery + scr_pharmacy + scr_srf + scr_childcare)

        # --- Density score ---
        scr_density = score_density(max_density, toa_density)

        # --- Recent development score ---
        scr_devcat = score_devcat(dev_category)

        # --- Vacant & underutilized score ---
        scr_vac_under = score_vac_under(vacant, underutilized)
        if scr_vac_under is None:
            conflict_count += 1
            scr_vac_under = 25  # Default to Vacant score; flag printed at end

        # --- Site characteristic scores ---
        scr_slope = score_slope(mean_slope)
        scr_flood = score_flood(flood_risk_cat)
        scr_shape = score_shape(irregular)
        scr_fire  = score_fire(fire_risk)
        scr_site  = scr_slope + scr_flood + scr_shape + scr_fire

        # --- Final total ---
        bcplm_score = scr_amenity + scr_density + scr_devcat + scr_vac_under + scr_site

        # Write outputs
        row[len(input_fields):]  = [
            scr_emp, scr_transit, scr_schools, scr_health,
            scr_grocery, scr_pharmacy, scr_srf, scr_childcare,
            scr_amenity,
            scr_density,
            scr_devcat,
            scr_vac_under,
            scr_slope, scr_flood, scr_shape, scr_fire,
            scr_site,
            bcplm_score,
        ]
        cursor.updateRow(row)
        total_rows += 1

print(f"\nComplete. {total_rows} rows processed.")
if conflict_count:
    print(f"WARNING: {conflict_count} rows had both Vacant = 'Y' and Underutilized = 'Y' — these were scored as Vacant (25 pts). Please review.")
else:
    print("No Vacant/Underutilized conflicts detected.")
print("Done.")
