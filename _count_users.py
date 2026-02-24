import asyncio
import httpx
from azure.identity import DefaultAzureCredential

def get_token():
    return DefaultAzureCredential().get_token("https://graph.microsoft.com/.default").token

async def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/users?$select=displayName,userPrincipalName,assignedLicenses,accountEnabled&$top=100"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        users = r.json().get("value", [])
        human = [u for u in users if u.get("accountEnabled") and "#EXT#" not in u["userPrincipalName"]]
        print(f"Total enabled internal users: {len(human)}")
        licensed = [u for u in human if len(u.get("assignedLicenses", [])) > 0]
        unlicensed = [u for u in human if len(u.get("assignedLicenses", [])) == 0]
        print(f"  With licenses   : {len(licensed)}")
        print(f"  Without licenses: {len(unlicensed)}")
        print()
        for i, u in enumerate(sorted(human, key=lambda x: x["displayName"]), 1):
            lic = len(u.get("assignedLicenses", []))
            flag = "  " if lic > 0 else "⚠ "
            print(f"  {flag}{i:2}. {u['displayName'][:32]:33} {u['userPrincipalName'][:52]:53} lic={lic}")

asyncio.run(main())
