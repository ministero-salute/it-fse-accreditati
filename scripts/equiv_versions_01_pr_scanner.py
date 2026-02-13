import os
import requests
import base64
import json
from datetime import datetime, timedelta
from urllib.parse import quote
import pandas as pd

# ------------------- Configuration -------------------
GITHUB_API = "https://api.github.com"
OWNER = "ministero-salute"
REPO = "it-fse-accreditamento"
TOKEN = os.getenv("GITHUB_TOKEN_IT_FSE_ACCREDITAMENTO_READ_ONLY")

# where we store the downloaded version-JSON files
OUTPUT_DIR = "pr_versions"
# -----------------------------------------------------

def github_get(url):
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_closed_prs():
    """Return a list of dicts, each representing a closed PR."""
    return github_get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/pulls?state=closed")

def get_pr_files(pr_number):
    """Return a list of file dicts for the given PR number."""
    return github_get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/pulls/{pr_number}/files")

def download_file_at_sha(file_path, sha, destination):
    """Fetch a file at a given commit SHA and write it to *destination*."""
    raw_url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{quote(file_path)}?ref={sha}"
    try:
        info = github_get(raw_url)
        content = base64.b64decode(info["content"])
        with open(destination, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌  Failed to download {file_path}@{sha}: {e}")
        return False

def extract_version_info(json_path):
    """
    Load a version JSON file and pull the required metadata.
    Expected keys (case-insensitive):
        - vendor
        - app_id   (or id)
        - main_version (or version)
        - equivalent_versions (list)
    Returns a dict with the normalized fields or empty strings if missing.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        vendor = data.get("appVendor")
        app_id = data.get("appID")
        main_version = data.get("appVersion")
        equiv = data.get("equiv_releases")

        if isinstance(equiv, str):
            equiv = [v.strip() for v in equiv.split(",") if v.strip()]

        return {
            "Vendor": vendor,
            "App ID": app_id,
            "Main Version": main_version,
            "Equivalent Versions": ", ".join(equiv) if equiv else "",
        }
    except Exception as e:
        print(f"⚠️  Could not parse {json_path}: {e}")
        return {
            "Vendor": "",
            "App ID": "",
            "Main Version":"",
            "Equivalent Versions":"",
        }

def is_recently_closed(pr, days=30):
    """True if the PR was closed within the last *days* days."""
    closed_at = pr.get("closed_at")
    if not closed_at:
        return False
    closed_dt = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.utcnow() - closed_dt <= timedelta(days=days)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.join(OUTPUT_DIR, today, "closed")
    os.makedirs(base_dir, exist_ok=True)

    records = []   # rows for the summary sheet

    for pr in get_closed_prs():
        if not is_recently_closed(pr, days=30):
            continue

        pr_number = pr["number"]
        pr_title  = pr["title"]
        head_sha  = pr["head"]["sha"]
        print(f"\n🔍 Closed PR #{pr_number} (within 30 days): {pr_title}")

        # Look for version*.json files in the PR
        version_files = [
            f for f in get_pr_files(pr_number)
            if f["filename"].lower().endswith(("version.json", "versions.json"))
        ]

        if not version_files:
            print("   ↪ No version JSON files - skipping.")
            continue

        for vf in version_files:
            local_name = f"PR{pr_number}_{os.path.basename(vf['filename'])}"
            local_path = os.path.join(base_dir, local_name)

            if download_file_at_sha(vf["filename"], head_sha, local_path):
                print(f"   📦 Downloaded {vf['filename']} → {local_path}")

                # ---- Extract metadata from the JSON file ----
                meta = extract_version_info(local_path)

                # ---- Append a row for this file ----
                records.append({
                    "PR #": pr_number,
                    "Title": pr_title,
                    "Version JSON file": os.path.basename(local_path),
                    "Local path": local_path,
                    "Vendor": meta["Vendor"],
                    "App ID": meta["App ID"],
                    "Main Version": meta["Main Version"],
                    "Equivalent Versions": meta["Equivalent Versions"],
                })
            else:
                print(f"   ❌ Failed to download {vf['filename']}")

    # Write Excel and Feather summary if any records exist
    if records:
        summary_path = os.path.join(OUTPUT_DIR, today, f"_pr_versions_summary_{today}.xlsx")
        df = pd.DataFrame(records)
        with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Versions PRs")
        print(f"\n✅ Excel summary written to {summary_path}")

        feather_path = os.path.join(OUTPUT_DIR, today, f"_pr_versions_summary_{today}.feather")
        df.to_feather(feather_path)
        print(f"✅ Feather summary written to {feather_path}")
    else:
        print("\n⚠️ No recently closed PRs with version JSON files were found.")

if __name__ == "__main__":
    main()