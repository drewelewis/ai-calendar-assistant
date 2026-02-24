"""
Delete licensed leaf-node users that are not demo-critical.
Uses the same logic as _find_removable_users.py to identify targets,
then calls DELETE /users/{id} for each one.
"""
import json
import subprocess
import urllib.request
import urllib.error

KEEP_UPN = {
    "liharwell",
    "ketran",
    "jiplunkett",
    "maokafor",
    "dchu",
    "rofaulkner",
    "anmoss",
    "jawhitfield",
    "admin",
}

def get_token():
    r = subprocess.run(
        "az account get-access-token --scope https://graph.microsoft.com/.default",
        capture_output=True, text=True, check=True, shell=True
    )
    return json.loads(r.stdout)["accessToken"]

def graph_get(token, path):
    url = "https://graph.microsoft.com/v1.0" + path
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())

def graph_delete(token, path):
    url = "https://graph.microsoft.com/v1.0" + path
    req = urllib.request.Request(url, method="DELETE",
                                  headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

def main():
    print("Getting token...", flush=True)
    token = get_token()

    data  = graph_get(token, "/users?$select=id,displayName,userPrincipalName,assignedLicenses,accountEnabled&$top=100")
    raw   = data.get("value", [])

    users = [
        u for u in raw
        if u.get("accountEnabled")
        and "#EXT#" not in u["userPrincipalName"]
        and not u["userPrincipalName"].startswith("conf_")
        and "service" not in u["displayName"].lower()
        and "bot" not in u["displayName"].lower()
    ]

    to_delete = []
    for u in sorted(users, key=lambda x: x["displayName"]):
        lic      = len(u.get("assignedLicenses", []))
        prefix   = u["userPrincipalName"].split("@")[0].lower()
        critical = any(prefix == k or prefix.startswith(k) for k in KEEP_UPN)
        if lic == 0 or critical:
            continue
        reps    = graph_get(token, f"/users/{u['id']}/directReports?$select=id&$top=5")
        manager = len(reps.get("value", [])) > 0
        if not manager:
            to_delete.append(u)

    print(f"\nAbout to DELETE {len(to_delete)} users:\n")
    for u in to_delete:
        lic = len(u.get("assignedLicenses", []))
        print(f"  {u['displayName']:<35}  {u['userPrincipalName']}  (lic={lic})")

    print("\nProceeding in 3 seconds... Ctrl-C to abort.", flush=True)
    import time; time.sleep(3)

    freed = 0
    for u in to_delete:
        status = graph_delete(token, f"/users/{u['id']}")
        lic    = len(u.get("assignedLicenses", []))
        if status == 204:
            freed += lic
            print(f"  DELETED  {u['displayName']} (freed {lic} license(s))", flush=True)
        else:
            print(f"  FAILED   {u['displayName']} — HTTP {status}", flush=True)

    print(f"\nDone. {freed} license(s) freed.", flush=True)

main()
