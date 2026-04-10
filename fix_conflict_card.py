"""One-time script to fix conflict card imBack buttons."""
path = r'c:\gitrepos\ai-calendar-assistant\operations\card_operations.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings for matching
content_n = content.replace('\r\n', '\n')

old_marker = '"msteams": {\n                            "type": "imBack",'
new_block = '''            "actions": [
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
            ]'''

# Find the start of the actions block
actions_start = content_n.find('\n            "actions": [')
if actions_start == -1:
    print("ERROR: could not find actions block start")
    exit(1)

# Find the closing bracket of the actions block
# It ends with:  ]
#         }
actions_end_marker = '\n            ]\n        }\n\n    def build_meeting_summary_card'
actions_end = content_n.find(actions_end_marker, actions_start)
if actions_end == -1:
    print("ERROR: could not find actions block end")
    # Show context
    print(repr(content_n[actions_start:actions_start+200]))
    exit(1)

actions_end += len('\n            ]')  # include the closing bracket

old_section = content_n[actions_start:actions_end]
print("Found old section:")
print(old_section[:100])

result = content_n[:actions_start] + '\n' + new_block + content_n[actions_end:]

with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(result.replace('\n', '\r\n'))
print("SUCCESS")
