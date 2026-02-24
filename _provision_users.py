"""
One-time provisioning script:
 - Fix existing user manager chains, titles, departments, and locations
 - Create 14 new users (Wealth Management + Retail Banking)
 - Set manager relationships for all new users
 - Set city/state/postalCode/countryOrRegion for everyone
"""

import asyncio
import json
from azure.identity import DefaultAzureCredential
import httpx

DOMAIN = "MngEnvMCAP623732.onmicrosoft.com"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
COUNTRY = "United States"

# ---------------------------------------------------------------------------
# Existing user IDs (from directory audit)
# ---------------------------------------------------------------------------
EXISTING = {
    "julie_parker":    "07d4677a-e5dc-4f95-926e-4b953a37de78",
    "marin_devine":    "732e6f93-bc02-4cda-9aae-42184a723ecf",
    "pim_vandenderen": "241c1424-53ee-4179-b937-a71ebe089f36",
    "jonson_tsai":     "a7b2cfab-7b5f-4a5d-b864-dc203418b356",
    "drew_lewis":      "d75cc09c-b943-4adb-ad58-527340924bc3",
    "prita_khedoe":    "5d6bc6b4-4294-4994-8206-8be6ee865407",
    "hank_stram":      "0ed0096d-58fa-4f03-b5ec-2987f45cb0c1",
    "david_rodgers":   "6393f195-77c7-4eb4-b0d4-df86596d738c",
    "cal_johnson":     "c3168840-92ad-4ef9-8867-f5c39e08960e",
    "jake_lamotta":    "c6da6f72-cd6d-4865-ab49-f6e90868fb12",
    "jason_moy":       "25355e9b-4fec-4648-b77b-482b6f3b209a",
    "jim_plunkett":    "69149650-b87e-44cf-9413-db5c1a5b6d3f",
    "mary_smith":      "8afe1483-f269-4c28-936d-e82444c31efd",
    "ravi_penmetsa":   "9480ffca-a008-40f2-8e81-d29d633c04ea",
    "samir_khalid":    "ad7f71eb-2f6e-4166-8745-cb3409fb37c1",
    "stelios_avramidis":"f6a384c3-8519-488c-9221-e27bc8295c96",
    "stan_walters":    "a8534ea8-d2fc-45b6-b36e-54f448922ac4",
}

# ---------------------------------------------------------------------------
# New users to create
# ---------------------------------------------------------------------------
NEW_USERS = [
    # Wealth Management
    dict(givenName="Linda",  surname="Hartwell",  upn="liharwell",    title="Chief Wealth Management Officer",        dept="Wealth Management", city="New York",     state="NY", zip="10001"),
    dict(givenName="Marcus", surname="Okafor",    upn="maokafor",     title="Director of Private Banking",            dept="Wealth Management", city="New York",     state="NY", zip="10001"),
    dict(givenName="Diane",  surname="Chu",       upn="dichu",        title="Director of Trust and Investment Services", dept="Wealth Management", city="New York",  state="NY", zip="10001"),
    dict(givenName="Nathan", surname="Briggs",    upn="nabriggs",     title="Senior Wealth Advisor",                  dept="Wealth Management", city="New York",     state="NY", zip="10001"),
    dict(givenName="Tom",    surname="Gallagher", upn="togallagher",  title="Wealth Advisor",                         dept="Wealth Management", city="Boston",       state="MA", zip="02101"),
    dict(givenName="Sofia",  surname="Reyes",     upn="soreyes",      title="Senior Wealth Advisor",                  dept="Wealth Management", city="Hartford",     state="CT", zip="06101"),
    dict(givenName="Priya",  surname="Nair",      upn="prnair",       title="Portfolio Analyst",                      dept="Wealth Management", city="New York",     state="NY", zip="10001"),
    # Retail Banking
    dict(givenName="Robert", surname="Faulkner",  upn="rofaulkner",   title="Chief Retail Banking Officer",           dept="Retail Banking",    city="New York",     state="NY", zip="10001"),
    dict(givenName="Angela", surname="Moss",      upn="anmoss",       title="Director of Branch Operations",          dept="Retail Banking",    city="New York",     state="NY", zip="10001"),
    dict(givenName="Kevin",  surname="Tran",      upn="ketran",       title="Director of Consumer Lending",           dept="Retail Banking",    city="Philadelphia", state="PA", zip="19101"),
    dict(givenName="Sandra", surname="Osei",      upn="saosei",       title="Branch Manager",                         dept="Retail Banking",    city="New York",     state="NY", zip="10001"),
    dict(givenName="Derek",  surname="Novak",     upn="denovak",      title="Branch Manager",                         dept="Retail Banking",    city="Hartford",     state="CT", zip="06101"),
    dict(givenName="Lucia",  surname="Fernandez", upn="lufernandez",  title="Senior Personal Banker",                 dept="Retail Banking",    city="New York",     state="NY", zip="10001"),
    dict(givenName="James",  surname="Whitfield", upn="jawhitfield",  title="Consumer Lending Analyst",               dept="Retail Banking",    city="Philadelphia", state="PA", zip="19101"),
]

# ---------------------------------------------------------------------------
# Existing user location + metadata fixes
# ---------------------------------------------------------------------------
EXISTING_UPDATES = [
    dict(id=EXISTING["julie_parker"],     city="New York",     state="NY", zip="10001", title="Chief Executive Officer",                    dept="Executive"),
    dict(id=EXISTING["marin_devine"],     city="New York",     state="NY", zip="10001", title="Chief Financial Officer",                    dept="Executive"),
    dict(id=EXISTING["pim_vandenderen"],  city="New York",     state="NY", zip="10001", title="Chief Information Officer",                  dept="Executive"),
    dict(id=EXISTING["jonson_tsai"],      city="New York",     state="NY", zip="10001", title="Information Technology Director",            dept="Information Technology"),
    dict(id=EXISTING["drew_lewis"],       city="New York",     state="NY", zip="10001", title="Senior Director of Application Development", dept="Application Development"),
    dict(id=EXISTING["prita_khedoe"],     city="New York",     state="NY", zip="10001", title="Manager Information Technology",             dept="Information Technology"),
    dict(id=EXISTING["hank_stram"],       city="New York",     state="NY", zip="10001", title="Manager Application Development",            dept="Application Development"),
    dict(id=EXISTING["david_rodgers"],    city="Boston",       state="MA", zip="02101", title="Director of Application Development",        dept="Application Development"),
    dict(id=EXISTING["cal_johnson"],      city="New York",     state="NY", zip="10001", title="Site Reliability Engineer",                  dept="Information Technology"),
    dict(id=EXISTING["jake_lamotta"],     city="Boston",       state="MA", zip="02101", title="Information Technology Architect",           dept="Information Technology"),
    dict(id=EXISTING["jason_moy"],        city="New York",     state="NY", zip="10001", title="Information Technology Architect",           dept="Information Technology"),
    dict(id=EXISTING["jim_plunkett"],     city="New York",     state="NY", zip="10001", title="Information Technology System Administrator",dept="Information Technology"),
    dict(id=EXISTING["mary_smith"],       city="Philadelphia", state="PA", zip="19101", title="Information Technology Architect",           dept="Information Technology"),
    dict(id=EXISTING["ravi_penmetsa"],    city="Hartford",     state="CT", zip="06101", title="Senior Information Technology Advisor",      dept="Information Technology"),
    dict(id=EXISTING["samir_khalid"],     city="Boston",       state="MA", zip="02101", title="Application Developer",                     dept="Application Development"),
    dict(id=EXISTING["stelios_avramidis"],city="Boston",       state="MA", zip="02101", title="Senior Application Developer",              dept="Application Development"),
    dict(id=EXISTING["stan_walters"],     city="Philadelphia", state="PA", zip="19101", title="Application Developer",                     dept="Application Development"),
]


def get_token():
    cred = DefaultAzureCredential()
    token = cred.get_token("https://graph.microsoft.com/.default")
    return token.token


async def patch_user(client, headers, user_id, body):
    r = await client.patch(f"{GRAPH_BASE}/users/{user_id}", headers=headers, json=body)
    if r.status_code not in (200, 204):
        print(f"  ❌ PATCH {user_id}: {r.status_code} {r.text[:200]}")
        return False
    return True


async def set_manager(client, headers, user_id, manager_id):
    body = {"@odata.id": f"{GRAPH_BASE}/users/{manager_id}"}
    r = await client.put(f"{GRAPH_BASE}/users/{user_id}/manager/$ref", headers=headers, json=body)
    if r.status_code not in (200, 204):
        print(f"  ❌ SET MANAGER {user_id} → {manager_id}: {r.status_code} {r.text[:200]}")
        return False
    return True


async def create_user(client, headers, u):
    display_name = f"{u['givenName']} {u['surname']}"
    upn = f"{u['upn']}@{DOMAIN}"
    body = {
        "accountEnabled": True,
        "displayName": display_name,
        "givenName": u["givenName"],
        "surname": u["surname"],
        "userPrincipalName": upn,
        "mailNickname": u["upn"],
        "mail": upn,
        "jobTitle": u["title"],
        "department": u["dept"],
        "city": u["city"],
        "state": u["state"],
        "postalCode": u["zip"],
        "country": COUNTRY,
        "usageLocation": "US",
        "passwordProfile": {
            "forceChangePasswordNextSignIn": False,
            "password": "TempP@ss2026!"
        }
    }
    r = await client.post(f"{GRAPH_BASE}/users", headers=headers, json=body)
    if r.status_code == 201:
        new_id = r.json()["id"]
        print(f"  ✅ Created {display_name} ({upn}) → {new_id}")
        return new_id
    else:
        print(f"  ❌ Create {display_name}: {r.status_code} {r.text[:300]}")
        return None


async def main():
    print("🔑 Getting token...")
    token = await asyncio.to_thread(get_token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30) as client:

        # ── Step 1: Update existing users (location + title + dept) ─────────
        print("\n📝 Step 1: Updating existing users...")
        for upd in EXISTING_UPDATES:
            uid = upd["id"]
            body = {
                "city": upd["city"],
                "state": upd["state"],
                "postalCode": upd["zip"],
                "country": COUNTRY,
                "usageLocation": "US",
                "jobTitle": upd["title"],
                "department": upd["dept"],
            }
            ok = await patch_user(client, headers, uid, body)
            if ok:
                print(f"  ✅ Updated {upd['title']} ({uid[:8]}...)")

        # ── Step 2: Fix existing manager chains ──────────────────────────────
        print("\n🔗 Step 2: Fixing existing manager chains...")
        manager_fixes = [
            (EXISTING["pim_vandenderen"],  EXISTING["julie_parker"]),   # CIO → CEO
            (EXISTING["jonson_tsai"],      EXISTING["pim_vandenderen"]), # IT Dir → CIO
            (EXISTING["drew_lewis"],       EXISTING["pim_vandenderen"]), # Sr Dir AppDev → CIO
            (EXISTING["prita_khedoe"],     EXISTING["jonson_tsai"]),     # Mgr IT → IT Dir (was CEO)
            (EXISTING["hank_stram"],       EXISTING["drew_lewis"]),      # Mgr AppDev → Sr Dir (was CEO)
            (EXISTING["david_rodgers"],    EXISTING["drew_lewis"]),      # Dir AppDev → Sr Dir (was Hank)
        ]
        for user_id, mgr_id in manager_fixes:
            ok = await set_manager(client, headers, user_id, mgr_id)
            if ok:
                print(f"  ✅ Set manager {user_id[:8]}... → {mgr_id[:8]}...")

        # ── Step 3: Create new users ─────────────────────────────────────────
        print("\n👤 Step 3: Creating new users...")
        new_ids = {}
        for u in NEW_USERS:
            new_id = await create_user(client, headers, u)
            if new_id:
                new_ids[u["upn"]] = new_id
            await asyncio.sleep(0.3)  # gentle throttle

        # ── Step 4: Set manager chains for new users ─────────────────────────
        print("\n🔗 Step 4: Setting manager chains for new users...")
        await asyncio.sleep(2)  # allow users to propagate

        # Helper: look up id by upn key
        def nid(key):
            return new_ids.get(key)

        manager_assignments = [
            # Wealth Management
            ("liharwell",   EXISTING["julie_parker"]),       # Linda Hartwell → CEO
            ("maokafor",    nid("liharwell")),                # Marcus Okafor → Linda
            ("dichu",       nid("liharwell")),                # Diane Chu → Linda
            ("nabriggs",    nid("maokafor")),                 # Nathan Briggs → Marcus
            ("togallagher", nid("maokafor")),                 # Tom Gallagher → Marcus
            ("soreyes",     nid("dichu")),                    # Sofia Reyes → Diane
            ("prnair",      nid("dichu")),                    # Priya Nair → Diane
            # Retail Banking
            ("rofaulkner",  EXISTING["julie_parker"]),        # Robert Faulkner → CEO
            ("anmoss",      nid("rofaulkner")),               # Angela Moss → Robert
            ("ketran",      nid("rofaulkner")),               # Kevin Tran → Robert
            ("saosei",      nid("anmoss")),                   # Sandra Osei → Angela
            ("denovak",     nid("anmoss")),                   # Derek Novak → Angela
            ("lufernandez", nid("saosei")),                   # Lucia Fernandez → Sandra
            ("jawhitfield", nid("ketran")),                   # James Whitfield → Kevin
        ]

        for upn_key, mgr_id in manager_assignments:
            user_id = nid(upn_key)
            if not user_id:
                print(f"  ⚠️  Skipping {upn_key} — not created")
                continue
            if not mgr_id:
                print(f"  ⚠️  Skipping manager for {upn_key} — manager not created")
                continue
            ok = await set_manager(client, headers, user_id, mgr_id)
            if ok:
                print(f"  ✅ {upn_key} → manager set")
            await asyncio.sleep(0.2)

        print("\n🎉 Done!")
        print(f"   Created {len(new_ids)} new users")
        print(f"   IDs: {json.dumps(new_ids, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
