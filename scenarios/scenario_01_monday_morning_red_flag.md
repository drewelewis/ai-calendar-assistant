# Scenario 1 — "Monday Morning, Red Flag"

**Expected Demo Time:** ~12–15 minutes

---

## 🏢 Company Context

**Contoso Bank** is a regional bank focused on two core business lines: Wealth Management and Commercial Banking. With a client book spanning high-net-worth individuals, family offices, and mid-market commercial borrowers, the firm operates across multiple metro markets and manages a significant leveraged finance portfolio.

Contoso is in the middle of a firm-wide AI enablement initiative — the strategic bet is that AI-empowered employees will outperform competitors who built AI for customers first. The program covers productivity tooling, internal knowledge access, risk workflows, and client relationship support.

The current pilot is a **custom Microsoft Teams app and M365 Copilot extension**, built on Azure AI Foundry, that puts intelligent agents directly inside the tools employees already use. No new portal. No training. Just smarter conversations inside Teams.

---

## 👤 Persona

| Field | Value |
|-------|-------|
| **Name** | Catherine Brooks |
| **Title** | Chief Operating Officer |
| **Login** | cabrooks@MngEnvMCAP623732.onmicrosoft.com |
| **Password** | TempP@ss2026! |
| **User ID** | 967eb41e-163d-4a02-be26-fde3bbafd662 |

Catherine Brooks is the COO, overseeing three divisions: **Wealth Management**, **Commercial Banking**, and **Information Technology**. She is one of the executive sponsors of the AI pilot.

---

## 📖 Story

Catherine gets in Monday morning to an email from the CFO: weekend stress-testing flagged three names in the wealth book with elevated covenant exposure given Friday's rate move. **Harbor View Private Equity** is at the top of the list.

Catherine needs her arms around the full org before she digs into the risk, then needs to get the right people on a call — all before her 10am with the CEO.

She also needs to address a conversation she had via Teams Chat with Julie Parker about the AI rollout. It's on track to be **6 months late**. Competitors have already created efficiencies that enhance employee capabilities and are now expanding into customer-facing agentic systems. Catherine needs a daily standup series with IT and App Dev leadership to get things back on track.

She's also planning a visit to the Contoso Philadelphia office and wants to arrange a casual lunch near the Art Museum with the local team.

Finally, it's been a while since Catherine had real face time with Julie Parker, the CEO. Julie loves coffee. Catherine wants to find a cozy spot in Midtown for an off-the-clock catch-up at 6pm — low key, no agenda, just the two of them.

**She does it all without leaving the chat window.**

---

## 🔄 Turn-by-Turn Flow

### Turn 1 — Directory Agent

> **Prompt:** *"Show me my team."*

**What happens:**
- Fetches live M365 org data — no questions asked
- Returns Catherine's full cross-divisional hierarchy in tree format

```
Catherine Brooks — Chief Operating Officer
├── Linda Hartwell — Chief Wealth Management Officer
│   ├── Marcus Okafor — Director of Private Banking
│   │   ├── Nathan Briggs — Senior Wealth Advisor (New York)
│   │   └── Tom Gallagher — Wealth Advisor (Boston)
│   └── Diane Chu — Director of Trust and Investment Services
│       ├── Sofia Reyes — Senior Wealth Advisor (Hartford)
│       └── Priya Nair — Portfolio Analyst (New York)
├── Robert Faulkner — Chief Retail Banking Officer
│   ├── Angela Moss — Director of Branch Operations
│   │   └── Sandra Osei — Branch Manager
│   │       └── Lucia Fernandez — Senior Personal Banker
│   └── Kevin Tran — Director of Consumer Lending (Philadelphia)
│       └── James Whitfield — Consumer Lending Analyst (Philadelphia)
└── Pim van Denderen — Chief Information Officer
    ├── Drew Lewis — Sr. Director of Application Development
    │   └── David Rodgers — Director of Application Development
    └── Jonson Tsai — IT Director
        ├── Jim Plunkett — IT System Administrator
        └── Prita Khedoe — Manager IT
```

> 💡 **Wow factor:** One prompt. Three divisions. Twenty people. All live from Entra. No spreadsheet. No org chart tool. No HR system. Just ask.

---

### Turn 2 — Risk Agent

> **Prompt:** *"Pull up the risk profile for Harbor View Private Equity."*

**What happens:**
- Finds **HARBOR VIEW PRIVATE EQUITY** (client ID: 9004716253)
- Returns structured risk data with analyst-grade commentary:

| Field | Value |
|-------|-------|
| Risk Rating | **HIGH ⚠️** |
| Status | **UNDER REVIEW 🚨** |
| Primary Exposure | $924,000,000 |
| Total Commitment | $3,500,000,000 |
| Industry | Private Equity — Leveraged Buyout |
| Key Risk | Rising interest rate sensitivity; multiple portfolio companies near covenant breach |

Agent commentary: *"This is a significant concern — Harbor View carries a High risk rating and is currently Under Review. With $3.5B in commitment and multiple portfolio companies near covenant breach, this warrants immediate attention."*

> 💡 **Wow factor:** The AI reads structured financial data and gives you an analyst-grade plain-English interpretation, not just raw numbers.

---

### Turn 3 — Calendar Agent

> **Prompt:** *"This is a red flag. I need Linda and Robert on a Teams call this afternoon at 2pm. Title it 'Harbor View Risk Review.'"*

**What happens:**
- Immediately fetches current datetime
- Validates Linda Hartwell and Robert Faulkner mailboxes in parallel
- Checks all three calendars for 2pm availability
- Presents meeting summary for confirmation:

| Field | Value |
|-------|-------|
| Subject | Harbor View Risk Review |
| When | Today at 2:00 PM |
| Attendees | Linda Hartwell, Robert Faulkner |
| Type | Microsoft Teams |

- On **"confirm"** → creates the Teams meeting, returns join link

> 💡 **Wow factor:** COO pulls her two division chiefs into a meeting in one sentence. No switching apps. No copy-pasting email addresses.

---

### Turn 4 — Calendar Agent

> **Prompt:** *"I need to set up a daily standup with the IT and App Dev leadership — Jonson, Jim, Prita, Drew, and David. Every weekday at 9am, starting tomorrow. Call it 'AI Pilot Daily Standup.'"*

**What happens:**
- Resolves all five names to mailboxes from the org directory
- Presents meeting summary for confirmation:

| Field | Value |
|-------|-------|
| Subject | AI Pilot Daily Standup |
| Recurrence | Every weekday (Mon–Fri) |
| Start Date | Tomorrow |
| Time | 9:00 AM |
| Attendees | Jonson Tsai, Jim Plunkett, Prita Khedoe, Drew Lewis, David Rodgers |
| Type | Microsoft Teams |

- On **"confirm"** → creates the recurring Teams meeting, returns join link

> 💡 **Wow factor:** Five people across two teams, recurring series, booked in one sentence. The kind of thing that normally takes 10 minutes of calendar wrangling.

---

### Turn 5 — Location Agent

> **Prompt:** *"I'm planning a visit to our Philadelphia office. Find somewhere good for a casual lunch near the Philadelphia Museum of Art."*

**What happens:**
- Azure Maps real-time search — restaurants near Philadelphia Museum of Art
- Returns 5–8 options: name, address, phone number, distance
- Numbered list, ready to share

> 💡 **Wow factor:** Azure Maps delivering live, geocoded results anchored to a landmark — directly in chat. No Yelp tab. No Google Maps. Just ask.

---

### Turn 6 — Location Agent

> **Prompt:** *"Find me a cozy coffee shop in Midtown Manhattan — somewhere quiet enough to have a real conversation."*

**What happens:**
- Azure Maps real-time search — coffee shops in Midtown Manhattan
- Returns 5–8 options: name, address, phone number, distance
- Numbered list, ready to choose from

> 💡 **Wow factor:** From a casual idea to a shortlist of real venues in seconds. No app-switching. No Yelp. No typing an address into Google Maps.

---

### Turn 7 — Calendar Agent

> **Prompt:** *"Book a coffee with Julie Parker tonight at 6pm. Just the two of us. Call it 'Catch Up — Catherine & Julie.'"*

**What happens:**
- Looks up Julie Parker's mailbox from the org directory
- Checks both calendars for 6pm availability
- Presents meeting summary for confirmation:

| Field | Value |
|-------|-------|
| Subject | Catch Up — Catherine & Julie |
| When | Today at 6:00 PM |
| Attendees | Julie Parker |
| Type | In-person (no Teams link) |

- On **"confirm"** → creates the calendar hold, sends invite to Julie

> 💡 **Wow factor:** CEO coffee booked in one sentence. No email thread. No assistant. The AI handles the who, the when, and the invite.

---

### Optional Closer — Directory Agent

> **Prompt:** *"Who do I have in Philadelphia and what are their emails?"*

**What happens:**
- Directory Agent scans the org for `city = Philadelphia`
- Returns:

| Name | Title | Email |
|------|-------|-------|
| Kevin Tran | Director of Consumer Lending | ketran@... |
| James Whitfield | Consumer Lending Analyst | jawhitfield@... |

> 💡 **Wow factor:** Live from Entra — no list to maintain, no lookup needed.

---

## 📊 Agent Scoreboard

| Turn | Agent | Task |
|------|-------|------|
| Turn 1 | **Directory Agent** | Live M365 org chart — 3 divisions, 20 people |
| Turn 2 | **Risk Agent** | Harbor View risk profile + AI commentary |
| Turn 3 | **Calendar Agent** | Urgent Teams meeting — Linda + Robert |
| Turn 4 | **Calendar Agent** | Recurring standup — 5 attendees (IT + App Dev) |
| Turn 5 | **Location Agent** | Azure Maps — Philly, near Art Museum |
| Turn 6 | **Location Agent** | Azure Maps — cozy coffee, Midtown Manhattan |
| Turn 7 | **Calendar Agent** | 1:1 coffee with CEO — in-person, no Teams |
| Optional | **Directory Agent** | Philadelphia team + emails |
