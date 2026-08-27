"""
Step 3b: Create Full_Address and Address_url (updated to include X&Y coordinates if No Address Available) (*Updated June 29 with street direction: W, E, etc.)

Part of the BCPLM field-processing pipeline. Paste into the ArcGIS Pro
Python window with the "BC Public Lands" layer active, after running any
earlier-numbered steps this one depends on.

Updated June 29 to include street direction suffix (W, E, etc.).
"""

import arcpy
import urllib.parse
import re

table = "BC Public Lands"
# -------------------------------------------------------------
f_num    = "STREET_NUMBER"
f_name   = "STREET_NAME"
f_type   = "STREET_TYPE"
f_sfx    = "STREET_DIRECTION_SUFFIX"   # ← new
f_city   = "CITY"
f_pc     = "POSTAL_CODE"
f_x      = "X_Coord"
f_y      = "Y_Coord"
# -------------------------------------------------------------

existing_fields = [f.name for f in arcpy.ListFields(table)]
if "Full_Address" not in existing_fields:
    arcpy.management.AddField(table, "Full_Address", "TEXT", field_length=255)
if "Address_url" not in existing_fields:
    arcpy.management.AddField(table, "Address_url", "TEXT", field_length=500)

fields = [f_num, f_name, f_type, f_sfx, f_city, f_pc, f_x, f_y, "Full_Address", "Address_url"]

def clean(val):
    return str(val).strip() if val is not None else ""

def smart_title(text):
    if not text:
        return text
    titled = text.title()
    titled = re.sub(r"(\d)(St|Nd|Rd|Th)\b",
                    lambda m: m.group(1) + m.group(2).lower(),
                    titled)
    return titled

def text_url(addr):
    encoded = urllib.parse.quote_plus(addr)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

def coords_url(x, y):
    lat_long_str = f"{y},{x}" if y is not None and x is not None else ""
    encoded = urllib.parse.quote_plus(lat_long_str)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

with arcpy.da.UpdateCursor(table, fields) as cursor:
    for row in cursor:
        num, name, st_type, sfx, city, pc, x, y, _, _ = row

        num_clean   = clean(num)
        name_clean  = smart_title(clean(name))
        type_clean  = smart_title(clean(st_type))
        sfx_clean   = clean(sfx).upper()   # keep cardinal directions uppercase: W, NE, etc.
        city_clean  = smart_title(clean(city))
        pc_clean    = clean(pc).upper()

        if not num_clean and not name_clean and not type_clean:
            full_addr = "No address available"
        else:
            # Street line: NUMBER NAME TYPE SUFFIX
            # e.g. "741 Burnside Rd W"
            street_parts = [num_clean, name_clean, type_clean, sfx_clean]
            street_clean = " ".join(p for p in street_parts if p)

            prov_pc   = "BC" + (f" {pc_clean}" if pc_clean else "")
            addr_parts = [street_clean, city_clean, prov_pc]
            full_addr  = ", ".join(p for p in addr_parts if p)

        has_full_street = bool(num_clean)
        has_coords      = x is not None and y is not None

        if has_full_street:
            maps_url = text_url(full_addr)
        elif has_coords:
            maps_url = coords_url(x, y)
        elif full_addr != "No address available":
            maps_url = text_url(full_addr)
        else:
            maps_url = coords_url(x, y)

        row[8] = full_addr
        row[9] = maps_url
        cursor.updateRow(row)

print("Full_Address and Address_url fields successfully created and calculated.")
