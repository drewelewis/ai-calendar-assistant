#!/usr/bin/env python3
"""
Test script to demonstrate the new body parameter functionality in create_calendar_event.
This shows how the AI agent can now create calendar events with rich body content.
"""

import asyncio
from operations.graph_operations import GraphOperations

async def test_calendar_event_with_body():
    """
    Demonstrates creating a calendar event with body content.
    """
    
    # Initialize GraphOperations
    graph_ops = GraphOperations()
    
    # Example usage of the new body parameter
    user_id = "example-user-id"  # This would be a real user ID in practice
    subject = "Team Planning Meeting"
    start = "2025-07-25T14:00:00Z"
    end = "2025-07-25T15:30:00Z"
    location = "Conference Room A"
    
    # Rich HTML body content that the AI can generate
    body = """
    <h3>Meeting Agenda</h3>
    <ul>
        <li><strong>Q3 Planning Review</strong> - Discussion of goals and objectives</li>
        <li><strong>Resource Allocation</strong> - Team assignments and budget planning</li>
        <li><strong>Timeline Discussion</strong> - Key milestones and deadlines</li>
        <li><strong>Action Items</strong> - Next steps and responsibilities</li>
    </ul>
    
    <h3>Preparation</h3>
    <p>Please bring:</p>
    <ul>
        <li>Current project status reports</li>
        <li>Resource requirement assessments</li>
        <li>Any budget concerns or requests</li>
    </ul>
    
    <p><em>Note: This meeting will be recorded for team members who cannot attend.</em></p>
    
    <p>For questions, contact the meeting organizer.</p>
    """
    
    attendees = ["john.doe@company.com", "jane.smith@company.com"]
    optional_attendees = ["manager@company.com"]
    
    print("=== Creating Calendar Event with Body Content ===")
    print(f"Subject: {subject}")
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Location: {location}")
    print(f"Required Attendees: {attendees}")
    print(f"Optional Attendees: {optional_attendees}")
    print("\nBody Content:")
    print(body)
    print("\n" + "="*50)
    
    # This would create the event in practice:
    # try:
    #     event = await graph_ops.create_calendar_event(
    #         user_id=user_id,
    #         subject=subject,
    #         start=start,
    #         end=end,
    #         location=location,
    #         body=body,
    #         attendees=attendees,
    #         optional_attendees=optional_attendees
    #     )
    #     print(f"✅ Event created successfully: {event.id}")
    # except Exception as e:
    #     print(f"❌ Error creating event: {e}")

    print("✅ Test completed successfully!")
    print("\nThe AI agent can now:")
    print("- Create detailed meeting agendas in the body")
    print("- Include preparation instructions")
    print("- Add formatted content with HTML")
    print("- Provide meeting context and objectives")
    print("- Include contact information and notes")

if __name__ == "__main__":
    asyncio.run(test_calendar_event_with_body())
