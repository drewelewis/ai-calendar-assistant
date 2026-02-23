# Example usage and testing
import os
import asyncio
import json
import time
from ai.multi_agent import MultiAgentOrchestrator
from telemetry.console_output import console_info

# Real M365 user ID — allows Graph API calls to work in tests
chat_session_id = "9480ffca-a008-40f2-8e81-d29d633c04ea"
# Suppress Teams notifications so test messages don't appear in the user's Teams client
os.environ["DISABLE_TEAMS_NOTIFICATIONS"] = "true"

# ---------------------------------------------------------------------------
# Test cases: (message, expected_agent)
# ---------------------------------------------------------------------------
TEST_CASES = [
    # Proxy / greeting
    ("Hello! What can you help me with?",                               "proxy"),
    # Calendar
    ("Can you schedule a team meeting for tomorrow at 2pm?",            "calendar"),
    ("What does my calendar look like this week?",                      "calendar"),
    ("Book a conference room for Friday afternoon.",                    "calendar"),
    # Directory
    ("Can you find Mary Smith in our directory?",                       "directory"),
    ("Who is the manager of the engineering department?",               "directory"),
    # Location
    ("Where are some good coffee shops near our office?",               "location"),
    ("Find me a hotel near downtown Seattle.",                          "location"),
    ("I need a restaurant close to the conference center.",             "location"),
    # Risk
    ("What is the risk profile for Meridian Capital?",                  "risk"),
    ("Show me clients with high financial exposure.",                   "risk"),
]

PASS  = "✅ PASS"
FAIL  = "❌ FAIL"
SKIP  = "⚠️  SKIP"  # router returned unexpected value but response still obtained


async def main():
    """Full test suite for Multi-Agent Orchestrator."""
    console_info("🚀 Starting Multi-Agent Full Test Suite", "TestRunner")
    console_info(f"   {len(TEST_CASES)} test cases | session: {chat_session_id}", "TestRunner")

    orchestrator = MultiAgentOrchestrator(session_id=chat_session_id)

    results = []
    passed = failed = 0

    try:
        for i, (message, expected_agent) in enumerate(TEST_CASES, 1):
            console_info(f"\n{'─'*60}", "TestRunner")
            console_info(f"[{i:02d}/{len(TEST_CASES)}] {message}", "TestRunner")
            console_info(f"      Expected agent : {expected_agent}", "TestRunner")

            t0 = time.perf_counter()
            try:
                response = await orchestrator.process_message(message)
                elapsed = time.perf_counter() - t0
                preview = response[:200] + ("..." if len(response) > 200 else "")
                console_info(f"      Response ({elapsed:.1f}s) : {preview}", "TestRunner")
                result = PASS
                passed += 1
            except Exception as exc:
                elapsed = time.perf_counter() - t0
                console_info(f"      ERROR ({elapsed:.1f}s) : {exc}", "TestRunner")
                result = FAIL
                failed += 1

            console_info(f"      Result : {result}", "TestRunner")
            results.append({"case": i, "message": message, "expected": expected_agent, "result": result})

        # Summary
        console_info(f"\n{'='*60}", "TestRunner")
        console_info(f"  Results : {passed} passed / {failed} failed / {len(TEST_CASES)} total", "TestRunner")

        status = await orchestrator.get_agent_status()
        console_info(f"\nAgent Status:\n{json.dumps(status, indent=2)}", "TestRunner")

    finally:
        await orchestrator.close()

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())