"""
Create a COO user, set their manager to Julie Parker,
then reassign Linda Hartwell, Robert Faulkner, and Pim van Denderen
to report to the new COO.
"""
import json, subprocess, urllib.request, urllib.error

SKU_ID = "18a4bd3f-0b5b-4887-b04f-61dd0ee15f5e"   # Microsoft_365_E5_(no_Teams)

DOMAIN = "MngEnvMCAP623732.onmicrosoft.com"

COO = {
    "displayName":       "Catherine Brooks",
    "givenName":         "Catherine",
    "surname":           "Brooks",
    "jobTitle":          "Chief Operating Officer",
    "department":        "Executive",
    "city":              "New York",
    "state":             "NY",
    "country":           "United States",
    "usageLocation":     "US",
    "userPrincipalName": f"cabrooks@{DOMAIN}",
    "mailNickname":      "cabrooks",
    "passwordProfile": {
        "forceChangePasswordNextSignIn": False,
        "password": "TempP@ss2026!"
    },
    "accountEnabled": True,
}

REASSIGN_UPN_PREFIXES = ["liharwell", "rofaulkner", "pim"]

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
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def graph_put(token, path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        "https://graph.microsoft.com/v1.0" + path,
        data=data, method="PUT",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    token = get_token()

    # Get all users
    data  = graph_get(token, "/users?$select=id,displayName,userPrincipalName,assignedLicenses&$top=100")
    users = {
        u["userPrincipalName"].split("@")[0].lower(): u
        for u in data.get("value", [])
        if "#EXT#" not in u["userPrincipalName"]
    }

    # Find Julie Parker
    julie = next((u for p, u in users.items() if "juparker" in p or "juparker" == p), None)
    if not julie:
        print("ERROR: Julie Parker not found"); return
    print(f"Found Julie Parker: {julie['id']}")

    # 1. Create COO
    print("\nCreating COO: Catherine Brooks...", flush=True)
    status, result = graph_post(token, "/users", COO)
    if status not in (200, 201):
        print(f"FAILED to create COO: HTTP {status} — {result}"); return
    coo_id = result["id"]
    print(f"  Created: {result['displayName']} ({coo_id})", flush=True)

    # 2. Assign license to COO
    status, _ = graph_post(token, f"/users/{coo_id}/assignLicense", {
        "addLicenses": [{"skuId": SKU_ID}],
        "removeLicenses": []
    })
    print(f"  License assigned (HTTP {status})", flush=True)

    # 3. Set COO's manager to Julie
    status, err = graph_put(token, f"/users/{coo_id}/manager/$ref", {
        "@odata.id": f"https://graph.microsoft.com/v1.0/users/{julie['id']}"
    })
    print(f"  Manager set to Julie Parker (HTTP {status})" + (f" — {err}" if err else ""), flush=True)

    # 4. Reassign Linda, Robert, Pim to report to COO
    print("\nReassigning direct reports to COO...", flush=True)
    for prefix in REASSIGN_UPN_PREFIXES:
        match = next((u for upn, u in users.items() if upn.startswith(prefix)), None)
        if not match:
            print(f"  NOT FOUND: {prefix}"); continue
        status, err = graph_put(token, f"/users/{match['id']}/manager/$ref", {
            "@odata.id": f"https://graph.microsoft.com/v1.0/users/{coo_id}"
        })
        print(f"  {match['displayName']:<35} → Catherine Brooks  (HTTP {status})" + (f" — {err}" if err else ""), flush=True)

    print("\nDone.", flush=True)

main()
