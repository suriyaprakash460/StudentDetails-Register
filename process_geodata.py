import json
import os

base_path = r"d:\student.py\taluka_temp\node_modules\india-location-data\src\data"

with open(os.path.join(base_path, "states.json"), "r") as f:
    states = json.load(f)
with open(os.path.join(base_path, "districts.json"), "r") as f:
    districts = json.load(f)
with open(os.path.join(base_path, "blocks.json"), "r") as f:
    blocks = json.load(f)

# Build mappings
state_map = {s["id"]: s["name"] for s in states}
district_map = {d["id"]: {"name": d["name"], "stateId": d["stateId"], "blocks": []} for d in districts}

for b in blocks:
    d_id = b["districtId"]
    if d_id in district_map:
        district_map[d_id]["blocks"].append(b["name"])

# Final result
result = {}
for d_id, d_info in district_map.items():
    s_name = state_map.get(d_info["stateId"], "Unknown")
    if s_name not in result:
        result[s_name] = {}
    
    # Sort blocks alphabetically
    d_info["blocks"].sort()
    result[s_name][d_info["name"]] = d_info["blocks"]

# Output
with open(r"d:\student.py\static\india_geodata.json", "w") as f:
    json.dump(result, f, indent=2)

print("Mapping generated successfully!")
