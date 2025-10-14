import json
from datetime import datetime
from pathlib import Path

RESULTS_PATH = Path("RESULTS/results.json")
EQUIV_NAMES_PATH = Path("RESULTS/equiv_names.json")

def main():

    # Read existing equiv_names.json if it exists
    existing_entries = {}
    try:
        with open(EQUIV_NAMES_PATH, "r", encoding="utf8") as f:
            existing_data = json.load(f)
            for entry in existing_data.get("names", []):
                key = (entry["appVendor"].upper(), tuple([n.upper() for n in entry["equiv_names"]]))
                existing_entries[key] = entry
    except FileNotFoundError:
        existing_entries = {}

    # Read new data from results.json
    with open(RESULTS_PATH, "r", encoding="utf8") as f:
        results_data = json.load(f)
    
    new_entries = []
    for result in results_data["results"]:
        if "equiv_names" in result and result["equiv_names"]:
            app_vendor = result["vendor"].upper()
            equiv_names = [n.upper() for n in result["equiv_names"]]
            key = (app_vendor, tuple(equiv_names))
            
            # Only add new entries not present in existing
            if key not in existing_entries:
                new_entry = {
                    "appVendor": app_vendor,
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "equiv_names": equiv_names
                }
                new_entries.append(new_entry)
    
    # Combine existing entries with new ones
    final_entries = list(existing_entries.values()) + new_entries
    
    # Prepare output structure
    output = {
        "names": final_entries
    }
    
    # Write to file
    with open("RESULTS/equiv_names.json", "w", encoding="utf8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
