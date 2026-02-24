"""
Assign Microsoft_365_E5 licenses to all unlicensed human users.
Skips service accounts, conference rooms, and anyone already licensed.
"""
import json, subprocess, urllib.request, urllib.error

SKU_ID = "18a4bd3f-0b5b-4887-b04f-61dd0ee15f5e"   # Microsoft_365_E5_(no_Teams)

SKIP_UPN = {"conf_apollo", "conf_gemini", "ms-serviceaccount"}
SKIP_DISPLAY_KEYWORDS = {"service account", "bot"}

def get_token():
    r = subprocess.run(
        "az account get-access-token --scope https://graph.microsoft.com/.default",
        capture_output=True, text=True, check=True, shell=True
    )
    return json.loads(r.stdout)["accessToken"]

def graph_get(token, path):
    req = urllib.request.Request(
        "https://graph.microsoft.com/v1.0" + path,
        headers={"Authorization": "Bearer " + token}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())

def graph_post(token, path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        "https://graph.microsoft.com/v1.0" + path,
        data=data, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    token = get_token()

    data  = graph_get(token, "/users?$select=id,displayName,userPrincipalName,assignedLicenses,accountEnabled&$top=100")
    users = [
        u for u in data.get("value", [])
        if u.get("accountEnabled")
        and "#EXT#" not in u["userPrincipalName"]
    ]

    assigned = skipped = 0
    for u in sorted(users, key=lambda x: x["displayName"]):
        prefix  = u["userPrincipalName"].split("@")[0].lower()
        display = u["displayName"].lower()

        if prefix in SKIP_UPN or any(k in display for k in SKIP_DISPLAY_KEYWORDS):
            continue

        already = any(l["skuId"] == SKU_ID for l in u.get("assignedLicenses", []))
        if already:
            print(f"  SKIP     {u['displayName']:<35} already licensed", flush=True)
            skipped += 1
            continue

        status, err = graph_post(token, f"/users/{u['id']}/assignLicense", {
            "addLicenses": [{"skuId": SKU_ID}],
            "removeLicenses": []
        })
        if status in (200, 204):
            print(f"  ASSIGNED {u['displayName']:<35} {u['userPrincipalName']}", flush=True)
            assigned += 1
        else:
            print(f"  FAILED   {u['displayName']:<35} HTTP {status}: {err}", flush=True)

    print(f"\nDone. {assigned} assigned, {skipped} already had license.", flush=True)

main()
