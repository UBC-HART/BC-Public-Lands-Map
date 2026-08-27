"""
Step 20: Create cleaned Infrastructure fields depending on if "Data Gap" is flagged for the jurisdiction

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy
import statistics
from scipy import stats

# --- Configuration ---
LAYER_NAME = "BC Public Lands"
JURISDICTION_FIELD = "JURISDICTION"
WATER_FIELD = "WaterMain_Dist"
HYDRO_FIELD = "BCHydroPrimary_Dist"
WATER_CLEAN_FIELD = "WaterMain_Clean"
HYDRO_CLEAN_FIELD = "BCHydroPrimary_Clean"
WATER_CLEAN_NUM_FIELD = "WaterMain_Clean_num"
HYDRO_CLEAN_NUM_FIELD = "BCHydro_Clean_num"

REFERENCE_JURISDICTIONS = {
    "City of Burnaby", "City of Coquitlam", "City of Surrey",
    "City of Vancouver", "City of Victoria", "City of Langley",
    "City of Parksville", "City of Pitt Meadows", "City of Duncan",
    "District of North Cowichan", "District of Oak Bay",
    "District of Saanich (SD61)", "Town of Gibsons", "Town of Sidney",
    "Township of Langley", "Township of Esquimalt"
}

P_THRESHOLD = 0.05
MEDIAN_TEST_THRESHOLD = 200
MEDIAN_HARD_THRESHOLD = 2000
MIN_N_FOR_TTEST = 10

# --- Collect values per jurisdiction ---
water_vals = {}
hydro_vals = {}

aprx = arcpy.mp.ArcGISProject("CURRENT")
map_obj = aprx.activeMap

target_layer = None
for lyr in map_obj.listLayers():
    if lyr.name == LAYER_NAME:
        target_layer = lyr
        break

if target_layer is None:
    print(f"ERROR: Layer '{LAYER_NAME}' not found in the active map.")
else:
    fields = [JURISDICTION_FIELD, WATER_FIELD, HYDRO_FIELD]

    with arcpy.da.SearchCursor(target_layer, fields) as cursor:
        for row in cursor:
            jurisdiction, water_dist, hydro_dist = row
            if jurisdiction is None:
                jurisdiction = "<Null>"
            if jurisdiction not in water_vals:
                water_vals[jurisdiction] = []
                hydro_vals[jurisdiction] = []
            if water_dist is not None and water_dist >= 0:
                water_vals[jurisdiction].append(water_dist)
            if hydro_dist is not None and hydro_dist >= 0:
                hydro_vals[jurisdiction].append(hydro_dist)

    # --- Build reference pools ---
    ref_water = []
    ref_hydro = []
    for j in REFERENCE_JURISDICTIONS:
        ref_water.extend(water_vals.get(j, []))
        ref_hydro.extend(hydro_vals.get(j, []))

    print(f"Reference pool: {len(ref_water)} water values, {len(ref_hydro)} hydro values\n")

    def classify(vals, ref_vals):
        """
        Returns (median, p_value, flag) for a jurisdiction's distance values.
        Flag is either 'DATA GAP' or 'OK'.
        """
        if not vals:
            return None, None, "NO DATA"

        med = statistics.median(vals)
        n = len(vals)

        # Hard threshold override
        if med > MEDIAN_HARD_THRESHOLD:
            return med, None, "DATA GAP"

        # Small sample — rely on hard threshold only
        if n < MIN_N_FOR_TTEST:
            if med > MEDIAN_TEST_THRESHOLD:
                return med, None, "DATA GAP"
            else:
                return med, None, "OK"

        # Median below test threshold — no test needed
        if med <= MEDIAN_TEST_THRESHOLD:
            return med, None, "OK"

        # Welch's t-test
        _, p = stats.ttest_ind(vals, ref_vals, equal_var=False)
        if p < P_THRESHOLD:
            return med, p, "DATA GAP"
        else:
            return med, p, "OK"

    # --- Classify each jurisdiction ---
    all_jurisdictions = sorted(set(list(water_vals.keys()) + list(hydro_vals.keys())))

    water_flags = {}
    hydro_flags = {}

    header = (f"{'JURISDICTION':<45} {'N':>5} {'Med_Water':>10} {'Water_Flag':>12}  "
              f"{'Med_Hydro':>10} {'Hydro_Flag':>12}")
    print(header)
    print("-" * 100)

    for j in all_jurisdictions:
        w_list = water_vals.get(j, [])
        h_list = hydro_vals.get(j, [])
        n = max(len(w_list), len(h_list))

        med_w, p_w, flag_w = classify(w_list, ref_water)
        med_h, p_h, flag_h = classify(h_list, ref_hydro)

        water_flags[j] = flag_w
        hydro_flags[j] = flag_h

        med_w_str = f"{med_w:>10.1f}" if med_w is not None else f"{'N/A':>10}"
        med_h_str = f"{med_h:>10.1f}" if med_h is not None else f"{'N/A':>10}"

        print(f"{str(j):<45} {n:>5} {med_w_str} {flag_w:>12}  {med_h_str} {flag_h:>12}")

    # --- Add/verify clean fields ---
    existing_fields = [f.name for f in arcpy.ListFields(target_layer)]

    for field_name in [WATER_CLEAN_FIELD, HYDRO_CLEAN_FIELD]:
        if field_name not in existing_fields:
            arcpy.management.AddField(target_layer, field_name, "TEXT", field_length=50)
            print(f"\nAdded field: {field_name}")
        else:
            print(f"\nField already exists, will overwrite: {field_name}")

    for field_name in [WATER_CLEAN_NUM_FIELD, HYDRO_CLEAN_NUM_FIELD]:
        if field_name not in existing_fields:
            arcpy.management.AddField(target_layer, field_name, "DOUBLE")
            print(f"Added field: {field_name}")
        else:
            print(f"Field already exists, will overwrite: {field_name}")

    # --- Populate clean fields ---
    update_fields = [JURISDICTION_FIELD, WATER_FIELD, HYDRO_FIELD,
                     WATER_CLEAN_FIELD, HYDRO_CLEAN_FIELD,
                     WATER_CLEAN_NUM_FIELD, HYDRO_CLEAN_NUM_FIELD]

    edited = 0
    with arcpy.da.UpdateCursor(target_layer, update_fields) as cursor:
        for row in cursor:
            jurisdiction, water_dist, hydro_dist, _, _, _, _ = row

            if jurisdiction is None:
                jurisdiction = "<Null>"

            w_flag = water_flags.get(jurisdiction, "OK")
            h_flag = hydro_flags.get(jurisdiction, "OK")

            # Water clean value (text)
            if w_flag == "DATA GAP":
                row[3] = "No data available"
            elif water_dist is not None:
                row[3] = f"{round(water_dist):,}"
            else:
                row[3] = "No data available"

            # Hydro clean value (text)
            if h_flag == "DATA GAP":
                row[4] = "No data available"
            elif hydro_dist is not None:
                row[4] = f"{round(hydro_dist):,}"
            else:
                row[4] = "No data available"

            # Water clean value (numeric) — mirrors text field, -1 where no data
            if row[3] == "No data available":
                row[5] = -1
            else:
                row[5] = water_dist

            # Hydro clean value (numeric) — mirrors text field, -1 where no data
            if row[4] == "No data available":
                row[6] = -1
            else:
                row[6] = hydro_dist

            cursor.updateRow(row)
            edited += 1

    print(f"\nUpdated {edited} rows in '{LAYER_NAME}'.")
    print("Done.")
