"""
Print the current M365 org chart as an ASCII tree.
"""
import json, subprocess, urllib.request

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

def main():
    token = get_token()

    data  = graph_get(token, "/users?$select=id,displayName,jobTitle,city,userPrincipalName,assignedLicenses,accountEnabled&$top=100")
    raw   = data.get("value", [])

    humans = {
        u["id"]: u for u in raw
        if u.get("accountEnabled")
        and "#EXT#" not in u["userPrincipalName"]
        and not u["userPrincipalName"].startswith("conf_")
        and "service" not in u["displayName"].lower()
        and "bot" not in u["displayName"].lower()
    }

    # Build manager -> [direct reports] map
    children = {uid: [] for uid in humans}
    has_manager = set()

    for uid in humans:
        r = graph_get(token, f"/users/{uid}/directReports?$select=id&$top=20")
        for rep in r.get("value", []):
            rid = rep["id"]
            if rid in humans:
                children[uid].append(rid)
                has_manager.add(rid)

    roots = [uid for uid in humans if uid not in has_manager]

    def print_tree(uid, prefix="", is_last=True):
        u     = humans[uid]
        conn  = "└── " if is_last else "├── "
        title = u.get("jobTitle") or ""
        city  = u.get("city") or ""
        loc   = f" ({city})" if city else ""
        print(f"{prefix}{conn}{u['displayName']} — {title}{loc}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        kids = sorted(children[uid], key=lambda x: humans[x]["displayName"])
        for i, kid in enumerate(kids):
            print_tree(kid, child_prefix, i == len(kids) - 1)

    print("\nOrg Chart\n" + "="*60)
    roots_sorted = sorted(roots, key=lambda x: humans[x]["displayName"])
    for i, r in enumerate(roots_sorted):
        print_tree(r, "", i == len(roots_sorted) - 1)

main()
