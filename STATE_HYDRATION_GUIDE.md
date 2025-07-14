# State Hydration Guide

This guide explains how to use the state hydration feature in the AI Calendar Assistant to restore previous conversation sessions.

## Overview

The state hydration feature allows the AI Calendar Assistant to restore previous conversations from Azure CosmosDB, maintaining context across multiple sessions.

## How It Works

1. **Storage**: Chat history is automatically saved to Azure CosmosDB after each conversation turn
2. **Loading**: When a session ID is provided, the system loads previous messages from CosmosDB
3. **Hydration**: The loaded messages are converted to Semantic Kernel format and added to a new chat thread
4. **Continuation**: The conversation continues with full context from the previous session

## Setup

### Environment Variables

To enable state hydration, set these environment variables:

```bash
# Required for CosmosDB connection
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DATABASE=AIAssistant
COSMOS_CONTAINER=ChatHistory

# Required to load a specific session (optional)
CHAT_SESSION_ID=your-session-id-here
```

### Azure CosmosDB Setup

1. Create an Azure CosmosDB account
2. Create a database (default: `AIAssistant`)
3. Create a container (default: `ChatHistory`) with partition key `/sessionId`
4. Configure Azure Identity authentication (see CosmosDB authentication guide)

## Usage

### Starting a New Session

Simply run the application without setting `CHAT_SESSION_ID`:

```bash
python chat.py
```

A new session will be created automatically.

### Continuing a Previous Session

Set the `CHAT_SESSION_ID` environment variable to the session you want to continue:

```bash
set CHAT_SESSION_ID=your-session-id-here
python chat.py
```

### Testing State Hydration

Run the built-in test to verify everything is working:

```bash
python chat.py test
```

This will:
1. Create test messages
2. Save them to CosmosDB
3. Load and hydrate them into a new thread
4. Report success or failure

## Troubleshooting

### Common Issues

1. **"No chat history found for session ID"**
   - The session ID doesn't exist in the database
   - Check that the session ID is correct
   - Verify the database and container names

2. **Authentication errors**
   - Ensure Azure Identity is configured correctly
   - Check that your account has access to the CosmosDB instance
   - Verify the CosmosDB endpoint URL

3. **Thread hydration failures**
   - Check that messages are in the correct format
   - Verify that the Semantic Kernel is initialized properly
   - Look for error messages in the console output

### Debug Information

The system provides detailed logging during state hydration:

- `💾 Saving test messages to session: [session-id]`
- `🔄 Loading messages from session: [session-id]`
- `📝 Added user message X: [preview]`
- `🤖 Added assistant message X: [preview]`
- `⚙️ Added system message X: [preview]`

## Message Format

Messages are stored in CosmosDB with this structure:

```json
{
  "id": "unique-document-id",
  "sessionId": "session-identifier",
  "timestamp": "2025-01-01T12:00:00.000Z",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "message content",
      "timestamp": "2025-01-01T12:00:00.000Z"
    }
  ]
}
```

## Implementation Details

### Key Components

1. **CosmosDBChatHistoryManager**: Handles saving and loading chat history
2. **create_hydrated_thread()**: Converts stored messages to Semantic Kernel format
3. **State restoration**: Adds messages to thread in chronological order

### Error Handling

- Gracefully handles missing sessions
- Continues with empty thread if hydration fails
- Provides detailed error messages for debugging
- Skips malformed or empty messages

## Tips

1. **Session Management**: Save the session ID from successful conversations to continue later
2. **Testing**: Use the test command to verify CosmosDB connectivity before important sessions
3. **Debugging**: Enable debug modes to see detailed message processing information
4. **Cleanup**: Consider implementing cleanup for old sessions to manage CosmosDB costs

## Security Considerations

- Use Azure Identity for authentication (no connection strings in code)
- Configure appropriate access controls on the CosmosDB instance
- Consider encrypting sensitive conversation data
- Implement proper session management and cleanup policies
