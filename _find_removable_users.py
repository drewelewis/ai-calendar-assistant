"""
Find licensed leaf-node users safe to remove from the tenant.
Leaf node = zero direct reports AND not demo-critical.
"""
import json
import subprocess
import urllib.request

KEEP_UPN = {
    "liharwell",    # Linda Hartwell    -- demo persona 1
    "ketran",       # Kevin Tran        -- demo persona 2
    "jiplunkett",   # Jim Plunkett      -- demo persona 3
    "maokafor",     # Marcus Okafor     -- S1 attendee
    "dchu",         # Diane Chu         -- S1 attendee
    "rofaulkner",   # Robert Faulkner   -- needs license
    "anmoss",       # Angela Moss       -- needs license
    "jawhitfield",  # James Whitfield   -- needs license
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

def main():
    print("Getting token...", flush=True)
    token = get_token()
    print("Token OK. Fetching users...", flush=True)

    data = graph_get(token, "/users?$select=id,displayName,userPrincipalName,assignedLicenses,accountEnabled&$top=100")
    raw  = data.get("value", [])
    print(f"Graph returned {len(raw)} users", flush=True)

    users = [
        u for u in raw
        if u.get("accountEnabled")
        and "#EXT#" not in u["userPrincipalName"]
        and not u["userPrincipalName"].startswith("conf_")
        and "service" not in u["displayName"].lower()
        and "bot" not in u["displayName"].lower()
    ]
    print(f"Enabled internal humans: {len(users)}\n", flush=True)

    removable = []
    kept      = []

    for u in sorted(users, key=lambda x: x["displayName"]):
        uid      = u["id"]
        lic      = len(u.get("assignedLicenses", []))
        prefix   = u["userPrincipalName"].split("@")[0].lower()
        critical = any(prefix == k or prefix.startswith(k) for k in KEEP_UPN)

        if lic == 0:
            continue   # already unlicensed

        reps    = graph_get(token, f"/users/{uid}/directReports?$select=id&$top=5")
        n_rep   = len(reps.get("value", []))
        manager = n_rep > 0

        tag = "MGR" if manager else "LEAF"
        crit = "CRITICAL" if critical else ""
        print(f"  [{tag:4}] lic={lic} {crit:8}  {u['displayName']}", flush=True)

        if manager or critical:
            why = []
            if manager:  why.append(f"manager ({n_rep} reports)")
            if critical: why.append("demo-critical")
            kept.append((u, why))
        else:
            removable.append(u)

    total_free = sum(len(u.get("assignedLicenses", [])) for u in removable)

    print(f"\n{'='*65}")
    print(f"SAFE TO REMOVE  ({len(removable)} users, {total_free} license(s) freed):")
    for u in removable:
        print(f"  CUT  {u['displayName']:<35}  {u['userPrincipalName']}")
    if not removable:
        print("  (none)")

    print(f"\nMUST KEEP  ({len(kept)} users):")
    for u, why in kept:
        print(f"  OK   {u['displayName']:<35}  {', '.join(why)}")

main()
