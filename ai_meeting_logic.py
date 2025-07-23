"""
AI Decision Logic for Teams Meeting Creation

This shows how the LLM can intelligently decide when to create Teams meetings
based on user requests and context.
"""

# Example prompts and AI responses for Teams meeting integration

TEAMS_MEETING_KEYWORDS = [
    "teams meeting", "video call", "video conference", "online meeting", 
    "virtual meeting", "remote meeting", "web conference", "zoom alternative",
    "screen share", "collaboration session", "hybrid meeting"
]

REGULAR_MEETING_KEYWORDS = [
    "conference room", "meeting room", "in-person", "face-to-face",
    "lunch meeting", "coffee meeting", "site visit", "walk and talk"
]

def ai_meeting_decision_logic():
    """
    Example logic the AI agent can use to decide between meeting types.
    """
    
    examples = [
        {
            "user_input": "Schedule a video call with the development team for sprint planning",
            "analysis": {
                "keywords_found": ["video call", "development team"],
                "context": "Development teams often distributed, sprint planning needs screen sharing",
                "decision": "create_teams_meeting",
                "confidence": 0.95
            },
            "ai_response": "I'll create a Teams meeting for your sprint planning session. This will include video, screen sharing capabilities, and allow remote team members to join easily."
        },
        
        {
            "user_input": "Book Conference Room B for the quarterly board meeting",
            "analysis": {
                "keywords_found": ["Conference Room B", "board meeting"],
                "context": "Physical location specified, formal board meeting typically in-person",
                "decision": "create_calendar_event", 
                "confidence": 0.90
            },
            "ai_response": "I'll book Conference Room B for your quarterly board meeting. Since you specified a physical location, I'll create a regular calendar event."
        },
        
        {
            "user_input": "Set up a meeting with external clients to demo our new product",
            "analysis": {
                "keywords_found": ["external clients", "demo"],
                "context": "External attendees, product demo needs screen sharing",
                "decision": "create_teams_meeting",
                "confidence": 0.85,
                "additional_params": {"include_dial_in": True}
            },
            "ai_response": "I'll create a Teams meeting for your product demo with external clients. This will include dial-in options for clients who prefer phone access and screen sharing for the demonstration."
        },
        
        {
            "user_input": "Schedule a lunch meeting with Sarah at the downtown cafe",
            "analysis": {
                "keywords_found": ["lunch meeting", "downtown cafe"],
                "context": "Social meeting at external location, no collaboration tools needed",
                "decision": "create_calendar_event",
                "confidence": 0.95
            },
            "ai_response": "I'll create a calendar event for your lunch meeting with Sarah at the downtown cafe. Since this is an in-person social meeting, a regular calendar invite will work perfectly."
        }
    ]
    
    return examples

# Enhanced prompt instructions for the AI agent
AI_MEETING_CREATION_PROMPT = """
When a user requests meeting creation, analyze the request to determine the appropriate meeting type:

**Create Teams Meeting When:**
- User mentions: video, virtual, online, Teams, remote, collaboration
- External attendees are involved
- Screen sharing or recording might be needed
- Distributed team members
- Demo or presentation context
- Hybrid meeting scenarios

**Create Regular Meeting When:**
- Physical location is specified (conference room, restaurant, office)
- In-person social meetings (lunch, coffee)
- Small local team meetings
- Site visits or field work
- Traditional board/executive meetings in formal spaces

**Auto-Enhancement Features:**
- Add professional Teams meeting template to body
- Include dial-in information for accessibility
- Add meeting etiquette guidelines
- Provide technical support contact information
- Include recording disclaimer when applicable

**Example AI Responses:**
- "I'll create a Teams meeting with video conference capabilities..."
- "Since you mentioned external clients, I'll set up a Teams meeting with dial-in options..."
- "I'll book Conference Room A for your in-person team meeting..."
"""

if __name__ == "__main__":
    examples = ai_meeting_decision_logic()
    
    print("🤖 AI Meeting Decision Logic Examples")
    print("=" * 50)
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Example {i}:")
        print(f"User Input: \"{example['user_input']}\"")
        print(f"Keywords Found: {example['analysis']['keywords_found']}")
        print(f"Context: {example['analysis']['context']}")
        print(f"Decision: {example['analysis']['decision']}")
        print(f"Confidence: {example['analysis']['confidence']*100}%")
        print(f"AI Response: \"{example['ai_response']}\"")
        
        if 'additional_params' in example['analysis']:
            print(f"Additional Parameters: {example['analysis']['additional_params']}")
    
    print(f"\n📋 AI Decision Prompt:")
    print(AI_MEETING_CREATION_PROMPT)
