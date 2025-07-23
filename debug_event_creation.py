#!/usr/bin/env python3
"""
Simple test to debug the calendar event creation issue.
"""

import asyncio
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.item_body import ItemBody

def test_event_creation():
    """Test creating an Event object to see if there are any issues."""
    try:
        print("Testing Event object creation...")
        
        # Create a simple event
        event = Event(
            subject="Test Meeting",
            start=DateTimeTimeZone(date_time="2025-07-25T14:00:00Z", time_zone="UTC"),
            end=DateTimeTimeZone(date_time="2025-07-25T15:00:00Z", time_zone="UTC"),
            location=Location(display_name="Test Room"),
            body=ItemBody(content_type="html", content="<p>Test meeting body</p>"),
            attendees=[]
        )
        print("✅ Event created successfully")
        
        # Test creating attendee
        email_address = EmailAddress(address="test@example.com")
        attendee_obj = Attendee(email_address=email_address)
        attendee_obj.type = "required"
        print("✅ Attendee created successfully")
        
        event.attendees.append(attendee_obj)
        print("✅ Attendee added to event successfully")
        
        print(f"Event subject: {event.subject}")
        print(f"Event start: {event.start.date_time}")
        print(f"Event attendees count: {len(event.attendees)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_event_creation()
    if success:
        print("\n🎉 Event creation test passed!")
    else:
        print("\n💥 Event creation test failed!")
