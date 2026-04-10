# Adaptive Cards — Complete Reference

This document covers everything about how Adaptive Cards work in the AI Calendar Assistant: design principles, when to use them, what cards exist, how they are built and delivered, and how button interactions are handled end-to-end.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [When to Use a Card vs. Plain Text](#2-when-to-use-a-card-vs-plain-text)
3. [Card Catalogue](#3-card-catalogue)
4. [Architecture — How Cards Flow End-to-End](#4-architecture--how-cards-flow-end-to-end)
5. [Card Construction Layer (`card_operations.py`)](#5-card-construction-layer-card_operationspy)
6. [Card Plugin Layer (`card_plugin.py`)](#6-card-plugin-layer-card_pluginpy)
7. [Structured Response Schema](#7-structured-response-schema)
8. [API Response Model](#8-api-response-model)
9. [Card Button Interactions](#9-card-button-interactions)
10. [Agent Prompt Conventions](#10-agent-prompt-conventions)
11. [Adding a New Card Type](#11-adding-a-new-card-type)

---

## 1. Design Philosophy

> **Cards are interaction surfaces, not conversation substitutes.**

The bot uses plain text when it is talking *at* the user (explaining, confirming, summarising).  
The bot uses an Adaptive Card when it is asking the user to *do something* — decide, confirm, choose, or provide structured input.

A second guiding rule: **card JSON is always produced by code, never by the LLM.** The LLM supplies structured data (meeting subject, attendee list, conflict details, etc.); `CardPlugin` passes that data to `CardOperations`, which assembles the card deterministically. This prevents hallucinated card schemas and keeps card structure auditable in one place.

---

## 2. When to Use a Card vs. Plain Text

| Situation | Surface |
|-----------|---------|
| Explaining something / answering a question | Text |
| Confirming an action that was just completed | Text or Card |
| Asking the user to decide between options | **Card** |
| Scheduling conflict — proceed or reschedule? | **Card** |
| Meeting created successfully | **Card** (confirmation) |
| Displaying a user profile | **Card** |
| Showing location / POI search results | **Card** |
| Platform capabilities / "what can you do" | **Card** |
| Conversational follow-up questions | Text |
| Error messages | Text |
| High-frequency or low-importance notifications | Text |

### Decision checklist

Use a card if **any** of the following apply:

- The user must choose from known options (Approve / Reject / Escalate)
- The user must confirm before a destructive or irreversible action
- A meaningful state change has occurred and a follow-up action is possible
- Structured information (a profile, a meeting, a set of results) will be clearer as a visual layout than as a prose paragraph

---

## 3. Card Catalogue

### 3.1 Capabilities Overview Card

**Trigger:** User says "show cards", "demo", "help", "what can you do", "show capabilities"  
**Agent:** ProxyAgent (via `build_capabilities_card`)  
**Description:** Renders a set of cards — one per major platform domain — listing what the assistant can do.  
**Actions:** None (informational only)

---

### 3.2 Meeting Confirmation Card

**Trigger:** A meeting has just been created successfully  
**Agent:** CalendarAgent (via `build_meeting_card`)  
**Description:** Green-accented card showing the new meeting's subject, time, location, attendees, organiser, and optional agenda.  
**Actions:**
- `View in Outlook` — opens Outlook calendar (Action.OpenUrl)
- `Edit` — submits `edit_meeting` action with meeting ID

**Required data fields:**
| Field | Description |
|-------|-------------|
| `subject` | Meeting title |
| `organizer` | Organiser display name or email |
| `attendees` | List of attendee objects (`email_address.address` or `name`) |
| `location` | Room or location string |
| `start_time` | Human-readable start (e.g. "Mon 9 Mar 10:00 AM") |
| `end_time` | Human-readable end |
| `body` | Agenda / description (optional) |
| `id` | Calendar event ID |

---

### 3.3 Scheduling Conflict Warning Card

**Trigger:** Conflict checking reveals one or more busy attendees before the meeting is created  
**Agent:** CalendarAgent (via `build_conflict_warning_card`)  
**Description:** Warning-styled card listing each attendee with a conflict and their conflicting event. Gives the user three choices.  
**Actions:**
- `Book Anyway` → submits `book_anyway` action
- `Find Another Time` → submits `find_another_time` action
- `Cancel` → submits `cancel` action (destructive style)

**Required data:**

*conflicts_json* — array of objects:
| Field | Description |
|-------|-------------|
| `attendee_name` | Display name of the busy attendee |
| `conflicting_event` | Title of their conflicting event |
| `conflict_time` | Time range string of the conflict |

*meeting_json* — object:
| Field | Description |
|-------|-------------|
| `subject` | Proposed meeting title |
| `proposed_start` | Human-readable proposed start |
| `proposed_end` | Human-readable proposed end |
| `organizer` | Organiser name |

---

### 3.4 User Profile Card

**Trigger:** A user profile lookup returns results  
**Agent:** DirectoryAgent (via `build_profile_card`)  
**Description:** Card showing a person's name, job title, department, email, mobile, and office location using a `FactSet` layout.  
**Actions:**
- `View Full Profile` — opens the person's Outlook People page (Action.OpenUrl)
- `Schedule Meeting` → submits `schedule_meeting` action with attendee email

**Required data fields (`user_json`):**
| Field | Description |
|-------|-------------|
| `displayName` | Full name |
| `jobTitle` | Job title |
| `department` | Department |
| `mail` | Email address |
| `mobilePhone` | Mobile number (optional) |
| `officeLocation` | Office / building (optional) |

---

### 3.5 Location Results Card

**Trigger:** Azure Maps search returns nearby places  
**Agent:** LocationAgent (via `build_location_card`)  
**Description:** Lists up to 5 nearby places with name, address, rating, and distance.  
**Actions:** None (informational; users continue conversation to get directions or book)

**Required data:**

*results_json* — array of objects (up to 5 rendered):
| Field | Description |
|-------|-------------|
| `name` | Place name |
| `address` | Formatted address |
| `rating` | Rating string e.g. "4.5" (optional) |
| `distance` | Distance string e.g. "0.3 km" (optional) |

*query* — the original search string the user typed

---

## 4. Architecture — How Cards Flow End-to-End

```
User message
    │
    ▼
MultiAgentOrchestrator          (ai/multi_agent.py)
    │  LLM router selects specialist agent
    ▼
Specialist Agent                (agents/calendar_agent.py, etc.)
    │  Agent calls CardPlugin kernel function
    ▼
CardPlugin                      (plugins/card_plugin.py)
    │  Deserialises LLM-supplied JSON data, calls CardOperations
    ▼
CardOperations                  (operations/card_operations.py)
    │  Builds deterministic Adaptive Card JSON dict
    │  Returns {"cards": [...]} envelope back to agent
    ▼
Agent structured response       {"message": "...", "cards": [...]}
    │  Enforced by json_schema Structured Outputs
    ▼
MultiAgentOrchestrator          Extracts message + cards from JSON
    ▼
FastAPI endpoint                (api/main.py  POST /chat)
    │  Returns ChatResponse(response=..., cards=[...])
    ▼
Teams Bot / Client              Renders text + Adaptive Cards
    │  User clicks a card button
    ▼
FastAPI endpoint                POST /chat  (card_action in Message)
    │  handle_card_action() dispatches to specific handler
    ▼
MultiAgentOrchestrator          Re-enters conversation with action context
```

---

## 5. Card Construction Layer (`card_operations.py`)

`CardOperations` is a plain Python class with no AI dependencies. Every method accepts Python dicts/lists and returns a complete Adaptive Card JSON dict.

| Method | Card produced |
|--------|--------------|
| `build_conflict_card(conflicts, meeting_data)` | Scheduling conflict warning |
| `build_meeting_summary_card(meeting)` | Meeting created confirmation |
| `build_user_profile_card(user)` | Directory profile |
| `build_location_results_card(results, query)` | Location / POI results |

All cards target **Adaptive Card schema version 1.5**.

---

## 6. Card Plugin Layer (`card_plugin.py`)

`CardPlugin` is a Semantic Kernel plugin registered on every specialist agent. It wraps each `CardOperations` method as a `@kernel_function` so the LLM can call it by name during a turn.

| Kernel function | Wraps |
|----------------|-------|
| `build_capabilities_card()` | Hard-coded capabilities set |
| `build_meeting_card(meeting_json)` | `build_meeting_summary_card` |
| `build_conflict_warning_card(conflicts_json, meeting_json)` | `build_conflict_card` |
| `build_profile_card(user_json)` | `build_user_profile_card` |
| `build_location_card(results_json, query)` | `build_location_results_card` |

Each function:
1. Deserialises the LLM's JSON string arguments
2. Calls the corresponding `CardOperations` method
3. Returns a JSON string envelope `{"cards": [...]}` (or `{"message": "...", "cards": [...]}`)

The LLM is instructed to pass the card envelope directly into its own structured response — it does **not** re-serialise or modify the card.

---

## 7. Structured Response Schema

Every agent response is constrained to this JSON schema via OpenAI Structured Outputs (`json_schema` response format):

```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "Natural language response. Empty string when a card is the entire response."
    },
    "cards": {
      "type": "array",
      "description": "Zero or more Adaptive Card objects to render in Teams.",
      "items": { "type": "object" }
    }
  },
  "required": ["message", "cards"]
}
```

`strict` is set to `false` because Adaptive Card objects are deeply nested and variable — `strict: true` would require exhaustively enumerating every possible card property.

This schema is configured in `MultiAgentOrchestrator._configure_openai_settings()` (`ai/multi_agent.py`).

---

## 8. API Response Model

The FastAPI endpoint returns a `ChatResponse` Pydantic model (`models/chat_models.py`):

```python
class ChatResponse(BaseModel):
    response: str                          # text from "message" field
    card:  Optional[Dict[str, Any]]        # single card (legacy)
    cards: Optional[List[Dict[str, Any]]] # list of cards (preferred)
    session_id: Optional[str]
```

The Teams bot / calling client should:
1. Display `response` as the chat message text (may be empty string if cards tell the full story)
2. Render each item in `cards` as a separate Adaptive Card attachment

---

## 9. Card Button Interactions

When a user clicks a button on an Adaptive Card in Teams, the bot framework submits a new message with the `card_action` field populated.

### Incoming message shape

```json
{
  "session_id": "abc123",
  "message": "",
  "card_action": {
    "action": "book_anyway",
    "data": {
      "meeting_subject": "Q1 Review",
      "proposed_start": "2026-04-14T14:00:00"
    }
  }
}
```

### Action routing

`handle_card_action()` in `api/main.py` dispatches to a dedicated handler function based on the `action` string:

| Action string | Handler | Behaviour |
|--------------|---------|-----------|
| `book_anyway` | `handle_book_anyway` | Re-submits booking request to orchestrator ignoring conflicts |
| `find_another_time` | `handle_reschedule` | Asks orchestrator to find an alternate slot |
| `reschedule` | `handle_reschedule` | Same as above (alias) |
| `confirm` | `handle_confirm` | Generic confirmation flow |
| `cancel` | `handle_cancel` | Cancels the pending operation |
| `view_profile` | `handle_view_profile` | Fetches and displays a user profile card |
| `edit_meeting` | `handle_edit_meeting` | Opens edit flow for an existing meeting |
| `schedule_meeting` | `handle_schedule_meeting` | Starts scheduling flow with a pre-filled attendee |

### Card button data conventions

Each `Action.Submit` button embeds its payload under a `data` key:

```json
{
  "type": "Action.Submit",
  "title": "Book Anyway",
  "style": "positive",
  "data": {
    "action": "book_anyway",
    "data": {
      "meeting_subject": "...",
      "proposed_start": "..."
    }
  }
}
```

The outer `action` key is the routing discriminator; the inner `data` object carries context passed to the handler.

---

## 10. Agent Prompt Conventions

Each specialist agent's system prompt instructs the LLM how and when to use cards:

- **CalendarAgent** — call `build_meeting_card` immediately after a meeting is created; call `build_conflict_warning_card` when conflict checking finds busy attendees. Pass the card JSON from the tool result verbatim into the `cards` array of the response.
- **DirectoryAgent** — call `build_profile_card` whenever a user profile lookup completes.
- **LocationAgent** — call `build_location_card` with the Azure Maps results.
- **ProxyAgent** — call `build_capabilities_card` in response to any "what can you do / help / demo" intent.

The universal rule encoded in every prompt: **never hand-write card JSON; always call the plugin and include its output in `cards`.**

---

## 11. Adding a New Card Type

1. **Add a builder method** to `CardOperations` in `operations/card_operations.py`:
   ```python
   def build_my_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
       return {
           "type": "AdaptiveCard",
           "version": "1.5",
           "schema": "http://adaptivecards.io/schemas/adaptive-card.json",
           "body": [...],
           "actions": [...]
       }
   ```

2. **Expose it as a kernel function** in `CardPlugin` (`plugins/card_plugin.py`):
   ```python
   @kernel_function(description="Build a my-card when ...")
   def build_my_card(self, data_json: Annotated[str, "JSON with ..."]) -> Annotated[str, "JSON envelope"]:
       data = json.loads(data_json)
       card = card_operations.build_my_card(data)
       return json.dumps({"cards": [card]}, ensure_ascii=False)
   ```

3. **Update the relevant agent prompt** (`agents/<agent>.py`) to tell the LLM when to call the new function.

4. **If the card has buttons**, add a handler function in `api/main.py` and register it in the `action_handlers` dict inside `handle_card_action()`.

5. No changes needed to the structured response schema or `ChatResponse` model — the `cards` array accepts any card object.
