"""
Adaptive Card operations for Teams bot responses.
Provides a CardOperations class whose methods build complete Adaptive Card
JSON structures for rich UI rendering in Microsoft Teams.
"""

from typing import List, Dict, Any, Optional


class CardOperations:
    """Builds Adaptive Card JSON structures for Microsoft Teams responses."""

    def build_conflict_card(self, conflicts: List[Dict[str, Any]], meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build an Adaptive Card warning about scheduling conflicts.

        Args:
            conflicts: List of conflict objects with attendee/time info
            meeting_data: Dictionary with proposed_start, proposed_end, organizer, subject

        Returns:
            Adaptive Card JSON
        """
        conflict_items = []
        for conflict in conflicts:
            conflict_items.append({
                "type": "TextBlock",
                "text": f"**{conflict.get('attendee_name', 'Unknown')}**",
                "weight": "bolder",
                "size": "medium",
                "spacing": "medium"
            })
            conflict_items.append({
                "type": "TextBlock",
                "text": f"{conflict.get('conflicting_event', 'Busy')} ({conflict.get('conflict_time', 'N/A')})",
                "color": "warning",
                "size": "small"
            })

        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {
                    "type": "Container",
                    "style": "warning",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Scheduling Conflicts Detected",
                            "weight": "bolder",
                            "size": "large",
                            "color": "warning"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Meeting: {meeting_data.get('subject', 'N/A')}",
                            "spacing": "medium",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Time: {meeting_data.get('proposed_start', 'N/A')} - {meeting_data.get('proposed_end', 'N/A')}",
                            "spacing": "small",
                            "size": "small"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "People with conflicts:",
                            "weight": "bolder",
                            "spacing": "medium"
                        },
                        *conflict_items
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Book Anyway",
                    "style": "positive",
                    "data": {
                        "action": "book_anyway",
                        "data": {
                            "meeting_subject": meeting_data.get("subject", ""),
                            "proposed_start": meeting_data.get("proposed_start", ""),
                            "proposed_end": meeting_data.get("proposed_end", "")
                        }
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "Find Another Time",
                    "data": {
                        "action": "find_another_time",
                        "data": {
                            "meeting_subject": meeting_data.get("subject", ""),
                            "proposed_start": meeting_data.get("proposed_start", ""),
                            "proposed_end": meeting_data.get("proposed_end", "")
                        }
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "Cancel",
                    "style": "destructive",
                    "data": {
                        "action": "cancel",
                        "data": {}
                    }
                }
            ]
        }

    def build_meeting_summary_card(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build an Adaptive Card confirming successful meeting creation.

        Args:
            meeting: Dictionary with subject, organizer, attendees, location, start_time, end_time, body

        Returns:
            Adaptive Card JSON
        """
        attendees = meeting.get('attendees', [])
        attendee_text = ", ".join([
            a.get('email_address', {}).get('address', a.get('name', 'Unknown'))
            for a in attendees
        ]) if attendees else "No attendees"

        body = [
            {
                "type": "Container",
                "style": "good",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "Meeting Created Successfully",
                        "weight": "bolder",
                        "size": "large",
                        "color": "good"
                    }
                ]
            },
            {
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": meeting.get('subject', 'N/A'),
                        "weight": "bolder",
                        "size": "large",
                        "spacing": "medium"
                    },
                    {
                        "type": "TextBlock",
                        "text": f"{meeting.get('start_time', 'N/A')} - {meeting.get('end_time', 'N/A')}",
                        "spacing": "small"
                    },
                    {
                        "type": "TextBlock",
                        "text": f"Location: {meeting.get('location', 'No location specified')}",
                        "spacing": "small"
                    },
                    {
                        "type": "TextBlock",
                        "text": f"**Attendees:** {attendee_text}",
                        "spacing": "medium",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": f"**Organizer:** {meeting.get('organizer', 'N/A')}",
                        "spacing": "small"
                    }
                ]
            }
        ]

        if meeting.get('body'):
            body.append({
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"**Agenda:** {meeting.get('body')}",
                        "spacing": "medium",
                        "wrap": True
                    }
                ]
            })

        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": body,
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View in Outlook",
                    "url": "https://outlook.office365.com/calendar/view/Month"
                },
                {
                    "type": "Action.Submit",
                    "title": "Edit",
                    "data": {
                        "action": "edit_meeting",
                        "data": {
                            "meeting_id": meeting.get("id", ""),
                            "meeting_subject": meeting.get("subject", "")
                        }
                    }
                }
            ]
        }

    def build_user_profile_card(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build an Adaptive Card displaying user profile information.

        Args:
            user: Dictionary with displayName, jobTitle, department, mail, mobilePhone, officeLocation

        Returns:
            Adaptive Card JSON
        """
        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": user.get('displayName', 'Unknown User'),
                            "weight": "bolder",
                            "size": "large"
                        },
                        {
                            "type": "TextBlock",
                            "text": user.get('jobTitle', 'Job title not specified'),
                            "spacing": "small",
                            "isSubtle": True
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "medium",
                    "items": [
                        {
                            "type": "FactSet",
                            "facts": [
                                {"name": "Email:", "value": user.get('mail', 'N/A')},
                                {"name": "Department:", "value": user.get('department', 'N/A')},
                                {"name": "Office:", "value": user.get('officeLocation', 'N/A')},
                                {"name": "Mobile:", "value": user.get('mobilePhone', 'N/A')}
                            ]
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Full Profile",
                    "url": f"https://outlook.office365.com/people/{user.get('mail', '')}"
                },
                {
                    "type": "Action.Submit",
                    "title": "Schedule Meeting",
                    "data": {
                        "action": "schedule_meeting",
                        "data": {
                            "attendee": user.get("mail", ""),
                            "attendee_name": user.get("displayName", "")
                        }
                    }
                }
            ]
        }

    def build_location_results_card(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Build an Adaptive Card displaying location/POI search results.

        Args:
            results: List of location results with name, address, rating, distance
            query: Search query string

        Returns:
            Adaptive Card JSON
        """
        location_items = []
        for idx, result in enumerate(results[:5]):  # Limit to 5 results
            location_items.append({
                "type": "Container",
                "separator": idx > 0,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"{idx + 1}. {result.get('name', 'Unknown')}",
                        "weight": "bolder"
                    },
                    {
                        "type": "TextBlock",
                        "text": result.get('address', 'Address not available'),
                        "spacing": "small",
                        "size": "small",
                        "isSubtle": True
                    },
                    {
                        "type": "ColumnSet",
                        "spacing": "small",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [{"type": "TextBlock", "text": f"Rating: {result.get('rating', 'N/A')}", "size": "small"}]
                            },
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [{"type": "TextBlock", "text": f"Dist: {result.get('distance', 'N/A')}", "size": "small"}]
                            }
                        ]
                    }
                ]
            })

        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Location Search Results",
                            "weight": "bolder",
                            "size": "large"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Search: \"{query}\"",
                            "spacing": "small",
                            "isSubtle": True,
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "medium",
                    "items": location_items
                }
            ],
            "actions": []
        }
