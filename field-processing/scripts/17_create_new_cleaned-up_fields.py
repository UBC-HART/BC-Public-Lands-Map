"""
Step 17: Create new cleaned-up fields

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.
"""

import arcpy

table = "BC Public Lands"

# -------------------------------------------------------------
# SOURCE FIELDS (Verify these match your exact column names)
# -------------------------------------------------------------
f_pid = "PID_int"
f_owner = "OwnerType"
f_mean = "MEAN"
f_env = "ENV_RMDTN_SITES_ID"
f_toa = "TOA_Tier"
f_fire = "Fire_Risk"

# Fire_Risk values that should be collapsed to a simple "No data"
FIRE_NO_DATA_PHRASES = [
    "No Data (Private Land)",
    "No Data (Private Managed Forest Land)"
]

# -------------------------------------------------------------
# NEW FIELDS TO CREATE
# -------------------------------------------------------------
new_fields = [
    ("PID_Formatted", 50),
    ("OwnerType_Clean", 100),
    ("Slope_Popup", 50),
    ("Env_Rem_ID_Clean", 50),
    ("TOA_Tier_Clean", 50),
    ("Fire_Risk_Clean", 100)
]

# 1. Safely add the new text fields if they don't already exist
existing_fields = [f.name for f in arcpy.ListFields(table)]
for field_name, field_length in new_fields:
    if field_name not in existing_fields:
        arcpy.management.AddField(table, field_name, "TEXT", field_length=field_length)

# 2. Define the cursor layout (source fields followed by the new calculation fields)
cursor_fields = [
    f_pid, f_owner, f_mean, f_env, f_toa, f_fire,          # Indices 0 to 5
    "PID_Formatted", "OwnerType_Clean", "Slope_Popup",     # Indices 6 to 8
    "Env_Rem_ID_Clean", "TOA_Tier_Clean", "Fire_Risk_Clean" # Indices 9 to 11
]

# Helper function to clean text or return empty string
def clean_str(val):
    return str(val).strip() if val is not None else ""

# 3. Process data formatting
with arcpy.da.UpdateCursor(table, cursor_fields) as cursor:
    for row in cursor:
        pid, owner, mean_val, env_id, toa_tier, fire = (
            row[0], row[1], row[2], row[3], row[4], row[5]
        )

        # --- 1. PID_Formatted (###-###-### with leading zeroes) ---
        if pid is not None and str(pid).strip() != "":
            try:
                # Strip any float decimal (e.g. "12345678.0") before pulling digits
                s = str(pid).strip()
                if "." in s:
                    s = s.split(".")[0]
                clean_pid = "".join(filter(str.isdigit, s))
                pid_padded = f"{int(clean_pid):09d}"
                pid_formatted = f"{pid_padded[:3]}-{pid_padded[3:6]}-{pid_padded[6:]}"
            except ValueError:
                pid_formatted = clean_str(pid)  # Fallback to cleaned text if conversion fails
        else:
            pid_formatted = "n/a"

        # --- 2. OwnerType_Clean (Sentence case & mapping) ---
        owner_clean = clean_str(owner)
        if owner_clean.upper() == "UNTITLEDPROV":
            owner_formatted = "Untitled provincial"
        elif owner_clean:
            owner_formatted = owner_clean.capitalize()
        else:
            owner_formatted = "n/a"

        # --- 3. Slope_Popup ("##.# (slope description)") ---
        if mean_val is not None:
            try:
                val = float(mean_val)
                # Apply categorization rules
                if val < 1:
                    desc = "flat"
                elif 1 <= val < 5:
                    desc = "mild slope"
                elif 5 <= val < 10:
                    desc = "moderate slope"
                else:
                    desc = "steep slope"
                slope_formatted = f"{val:.1f} ({desc})"
            except ValueError:
                slope_formatted = "n/a"
        else:
            slope_formatted = "n/a"

        # --- 4. Env_Rem_ID_Clean (String copy or "n/a") ---
        env_clean = clean_str(env_id)
        env_formatted = env_clean if env_clean else "n/a"

        # --- 5. TOA_Tier_Clean (String copy or "n/a") ---
        # Note: If the field is a numeric type, removing decimals or converting to int helps presentation
        toa_clean = clean_str(toa_tier)
        if toa_clean:
            # Drop trailing '.0' if it is a double/float stored in text form
            if toa_clean.endswith(".0"):
                toa_clean = toa_clean[:-2]
            toa_formatted = toa_clean
        else:
            toa_formatted = "n/a"

        # --- 6. Fire_Risk_Clean (collapse "No Data (...)" variants to "No data") ---
        fire_clean = clean_str(fire)
        if not fire_clean:
            fire_formatted = "n/a"
        elif any(phrase in fire_clean for phrase in FIRE_NO_DATA_PHRASES):
            fire_formatted = "No data"
        else:
            fire_formatted = fire_clean

        # Write calculations back into row indexes 6 through 11
        row[6] = pid_formatted
        row[7] = owner_formatted
        row[8] = slope_formatted
        row[9] = env_formatted
        row[10] = toa_formatted
        row[11] = fire_formatted

        cursor.updateRow(row)

print("Experience Builder optimization fields successfully calculated.")
