# 🧭 When Should Events Be Rendered as Cards in a Teams Bot

This document defines **which events should (and should not) be surfaced as Adaptive Cards** in Microsoft Teams bots.

---

## 🎯 Core Principle

> **Render an event as an Adaptive Card when the user is expected to _decide, act, or confirm_ something.**

Cards are **interaction surfaces**, not conversation substitutes.

---

## ✅ Event Categories That SHOULD Be Cards

### 1. Action‑Required Events (Highest Priority)

**Definition**  
Events where progress is blocked until a user responds.

**Examples**
- Approval / rejection required
- Confirmation needed
- Exception handling
- Manual override required
- Policy decision needed

---

### 2. State Change Notifications That Invite a Response

**Definition**  
Important state transitions where the user may need to take a follow‑up action.

**Examples**
- Job completed / failed
- Deployment finished
- SLA breached
- Incident status changed

---

### 3. Structured Input Collection (Form‑Like Interactions)

**Definition**  
Events that require multiple known inputs from a user.

**Examples**
- Create / update ticket
- Assign task
- Capture metadata (priority, owner, due date)

---

### 4. Choice or Branching Decisions

**Definition**  
Events where the user must choose one of several predefined paths.

**Examples**
- Approve / Reject / Escalate
- Proceed / Pause / Roll back
- Select workflow path

---

### 5. High‑Signal Notifications

**Definition**  
Events important enough to visually stand out from normal chat traffic.

**Examples**
- Security alerts
- Compliance issues
- Production failures

---

### 6. Summaries That Offer a Next Step

**Definition**  
Summarized information paired with optional actions.

**Examples**
- Daily summary with follow‑ups
- Incident recap with acknowledgment

---

## 🚫 Events That SHOULD NOT Be Cards

- Purely informational messages
- Conversational or exploratory dialogue
- High‑frequency / low‑importance events
- Content‑heavy interactions

---

## 🧠 Decision Checklist

Use a card if **any** of the following are true:
- User must take action
- User must choose from known options
- User must provide structured input
- Event represents a meaningful state change

---

## ✅ Recommended Interaction Pattern

| Interaction Type | Surface |
|------------------|---------|
| Explanation / chat | Text |
| Decision / confirmation | Adaptive Card |
| Structured input | Adaptive Card |
| Complex workflow | Dialog / Task Module |
| Deep content | Tab |

---

## 🏁 Final Rule

> **If the bot is talking _at_ the user → use text.  
> If the bot is asking the user to _do something_ → use a card.**
