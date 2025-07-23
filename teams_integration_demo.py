#!/usr/bin/env python3
"""
Demonstration of Teams Meeting Integration in AI Calendar Assistant

This example shows how the AI agent can now create calendar events with actual Microsoft Teams meeting links.
The implementation automatically creates Teams meetings when requested and embeds them in calendar events.
"""

import asyncio
from operations.graph_operations import GraphOperations

class TeamsIntegrationDemo:
    def __init__(self):
        self.graph_ops = GraphOperations()
    
    async def demonstrate_teams_meeting_creation(self):
        """
        Demonstrates the new Teams meeting functionality.
        """
        print("🎥 Teams Meeting Integration Demo")
        print("=" * 50)
        
        # Example meeting parameters
        user_id = "example-user-id"  # Replace with actual user ID
        subject = "Q3 Strategic Planning - Teams Meeting"
        start = "2025-07-25T14:00:00Z"
        end = "2025-07-25T15:30:00Z"
        attendees = ["john.doe@company.com", "jane.smith@company.com"]
        optional_attendees = ["manager@company.com"]
        
        # Meeting agenda that will be enhanced with Teams info
        meeting_agenda = """
        <h3>Meeting Agenda</h3>
        <ol>
            <li><strong>Q3 Goals Review</strong> (15 minutes)
                <ul>
                    <li>Revenue targets and progress</li>
                    <li>Key performance indicators</li>
                </ul>
            </li>
            <li><strong>Strategic Initiatives</strong> (30 minutes)
                <ul>
                    <li>New product launches</li>
                    <li>Market expansion plans</li>
                    <li>Partnership opportunities</li>
                </ul>
            </li>
            <li><strong>Resource Planning</strong> (20 minutes)
                <ul>
                    <li>Team scaling requirements</li>
                    <li>Budget allocations</li>
                    <li>Technology investments</li>
                </ul>
            </li>
            <li><strong>Next Steps & Action Items</strong> (15 minutes)</li>
        </ol>
        
        <h3>Preparation Required</h3>
        <ul>
            <li>Review Q2 performance reports</li>
            <li>Prepare department update slides</li>
            <li>Bring budget proposals and justifications</li>
        </ul>
        """
        
        print("📋 Meeting Details:")
        print(f"   Subject: {subject}")
        print(f"   Date/Time: {start} to {end}")
        print(f"   Required Attendees: {', '.join(attendees)}")
        print(f"   Optional Attendees: {', '.join(optional_attendees)}")
        print("\n🔧 Creating Teams Meeting...")
        
        # This would create the actual Teams meeting in practice:
        # try:
        #     teams_event = await self.graph_ops.create_calendar_event_with_teams(
        #         user_id=user_id,
        #         subject=subject,
        #         start=start,
        #         end=end,
        #         body=meeting_agenda,
        #         attendees=attendees,
        #         optional_attendees=optional_attendees,
        #         create_teams_meeting=True
        #     )
        #     
        #     if teams_event:
        #         print("✅ Teams meeting created successfully!")
        #         print(f"   Event ID: {teams_event.id}")
        #         if hasattr(teams_event, '_teams_meeting_info'):
        #             teams_info = teams_event._teams_meeting_info
        #             print(f"   Teams Join URL: {teams_info['join_url']}")
        #             if teams_info.get('conference_id'):
        #                 print(f"   Conference ID: {teams_info['conference_id']}")
        #     else:
        #         print("❌ Failed to create Teams meeting")
        # 
        # except Exception as e:
        #     print(f"❌ Error creating Teams meeting: {e}")
        
        # For demo purposes, show what the enhanced body would look like:
        print("✅ Teams meeting would be created with enhanced body content:")
        print("\n📧 Enhanced Email Body Preview:")
        
        enhanced_body_preview = f"""
        <div style="background-color: #f3f2f1; padding: 15px; margin: 10px 0; border-left: 4px solid #6264a7;">
            <h3 style="color: #6264a7; margin-top: 0;">📱 Microsoft Teams Meeting</h3>
            <p><strong>Join the meeting:</strong></p>
            <p><a href="https://teams.microsoft.com/l/meetup-join/..." style="color: #6264a7; text-decoration: none; font-weight: bold;">Click here to join the meeting</a></p>
            <p><strong>Conference ID:</strong> 123 456 789#</p>
            <p><a href="https://dialin.teams.microsoft.com/...">Find local dial-in numbers</a></p>
            <p><em>By joining this meeting, you agree to not record or share content without consent.</em></p>
        </div>
        <br/>
        {meeting_agenda}
        """
        
        print(enhanced_body_preview)
        
        return True

    async def demonstrate_ai_integration(self):
        """
        Shows how the LLM can intelligently choose between regular and Teams meetings.
        """
        print("\n🤖 AI Integration Examples")
        print("=" * 40)
        
        examples = [
            {
                "user_request": "Schedule a video call with the remote team",
                "ai_decision": "create_teams_meeting",
                "reasoning": "User specifically mentioned 'video call' - perfect for Teams"
            },
            {
                "user_request": "Set up a virtual meeting for client presentation",
                "ai_decision": "create_teams_meeting", 
                "reasoning": "Virtual meeting indicates online collaboration needs"
            },
            {
                "user_request": "Book Conference Room A for team standup",
                "ai_decision": "create_calendar_event",
                "reasoning": "Physical location specified - regular meeting appropriate"
            },
            {
                "user_request": "Create a Teams meeting for project review",
                "ai_decision": "create_teams_meeting",
                "reasoning": "Explicitly requested Teams meeting"
            },
            {
                "user_request": "Schedule lunch meeting at the cafe",
                "ai_decision": "create_calendar_event",
                "reasoning": "Social meeting at external location - no Teams needed"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n📝 Example {i}:")
            print(f"   User Request: \"{example['user_request']}\"")
            print(f"   AI Decision: Use {example['ai_decision']}")
            print(f"   Reasoning: {example['reasoning']}")
        
        print("\n💡 Key AI Decision Factors:")
        print("   • Keywords: 'video', 'virtual', 'online', 'Teams', 'remote'")
        print("   • Context: External attendees, distributed teams")
        print("   • Location: Physical vs virtual meeting spaces")
        print("   • Purpose: Collaboration vs social meetings")

    async def show_permission_requirements(self):
        """
        Shows the required permissions for Teams meeting creation.
        """
        print("\n🔐 Required Permissions")
        print("=" * 30)
        
        permissions = [
            {
                "permission": "OnlineMeetings.ReadWrite",
                "scope": "Application",
                "purpose": "Create and manage Teams meetings"
            },
            {
                "permission": "Calendars.ReadWrite",
                "scope": "Application", 
                "purpose": "Create calendar events with Teams meetings"
            },
            {
                "permission": "User.Read.All",
                "scope": "Application",
                "purpose": "Access user information for meeting creation"
            }
        ]
        
        print("Required Microsoft Graph API Permissions:")
        for perm in permissions:
            print(f"   • {perm['permission']} ({perm['scope']})")
            print(f"     Purpose: {perm['purpose']}")
        
        print("\n📋 Setup Checklist:")
        print("   ✓ Azure AD app registration with required permissions")
        print("   ✓ Admin consent granted for application permissions")
        print("   ✓ Users have Microsoft Teams licenses")
        print("   ✓ Users have Exchange Online licenses")
        print("   ✓ Teams meeting policies configured")

async def main():
    """Run the Teams integration demonstration."""
    demo = TeamsIntegrationDemo()
    
    await demo.demonstrate_teams_meeting_creation()
    await demo.demonstrate_ai_integration()
    await demo.show_permission_requirements()
    
    print("\n🎯 Implementation Summary:")
    print("=" * 40)
    print("✅ Added create_online_meeting() method")
    print("✅ Enhanced create_calendar_event_with_teams() method")
    print("✅ Added create_teams_meeting() plugin function")
    print("✅ Enhanced existing create_calendar_event() with Teams option")
    print("✅ Automatic Teams meeting link generation")
    print("✅ Professional meeting invitation templates")
    print("✅ Dial-in number integration")
    print("✅ Conference ID for phone participants")
    
    print("\n🚀 Next Steps:")
    print("   1. Configure Azure AD permissions")
    print("   2. Test with real user accounts")
    print("   3. Customize meeting templates")
    print("   4. Add meeting recording options")
    print("   5. Integrate with Teams channels")

if __name__ == "__main__":
    asyncio.run(main())
