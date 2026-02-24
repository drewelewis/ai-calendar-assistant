import json, subprocess, urllib.request
r = subprocess.run(
    "az account get-access-token --scope https://graph.microsoft.com/.default",
    capture_output=True, text=True, check=True, shell=True
)
token = json.loads(r.stdout)["accessToken"]
req = urllib.request.Request(
    "https://graph.microsoft.com/v1.0/subscribedSkus",
    headers={"Authorization": "Bearer " + token}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    skus = json.loads(resp.read())["value"]
for s in skus:
    avail = s["prepaidUnits"]["enabled"] - s["consumedUnits"]
    print(f"  {s['skuPartNumber']:<40} id={s['skuId']}  consumed={s['consumedUnits']}  enabled={s['prepaidUnits']['enabled']}  available={avail}")
