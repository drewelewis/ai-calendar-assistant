#!/usr/bin/env python3
"""
Multi-Agent AI Calendar Assistant CLI
Interactive command-line interface for testing the multi-agent system.
"""

import asyncio
import uuid
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.multi_agent import MultiAgentOrchestrator
from telemetry.console_output import console_info, console_error, console_warning

load_dotenv()

class MultiAgentCLI:
    """Command-line interface for the multi-agent system."""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.orchestrator = None
        
    async def initialize(self):
        """Initialize the multi-agent orchestrator."""
        try:
            console_info("🤖 Initializing Multi-Agent AI Calendar Assistant...", "CLI")
            console_info(f"📋 Using session ID: {self.session_id}", "CLI")
            self.orchestrator = MultiAgentOrchestrator(session_id=self.session_id)
            console_info(f"✅ Multi-Agent system ready! Session: {self.session_id[:8]}...", "CLI")
            return True
        except Exception as e:
            console_error(f"❌ Failed to initialize multi-agent system: {e}", "CLI")
            return False
    
    async def show_welcome(self):
        """Display welcome message and agent information."""
        print("\n" + "="*70)
        print("🤖 Multi-Agent AI Calendar Assistant")
        print("="*70)
        print("Available specialized agents:")
        print("  📋 Proxy Agent     - Main conversation handler and task router")
        print("  📅 Calendar Agent  - Scheduling, events, and meeting rooms")
        print("  👥 Directory Agent - User searches and organizational data")
        print("  📍 Location Agent  - Location searches and nearby places")
        print("\nType your questions naturally - I'll route them to the right agent!")
        print("Commands: /status, /reset, /agents, /help, /quit")
        print("="*70)
        
        if self.orchestrator:
            status = await self.orchestrator.get_agent_status()
            console_info(f"System ready with {status['total_agents']} agents", "CLI")
    
    async def show_help(self):
        """Display help information."""
        help_text = """
🔧 Multi-Agent AI Calendar Assistant Commands:

Basic Commands:
  /help     - Show this help message
  /status   - Show system and agent status
  /agents   - List all available agents
  /reset    - Clear conversation history
  /quit     - Exit the application

Example Queries:
  📅 Calendar: "Schedule a meeting with John tomorrow at 2 PM"
  👥 Directory: "Find all managers in the Engineering department"
  📍 Location: "Find coffee shops near our office"
  📋 General: "What can you help me with?"

Tips:
  • Ask natural questions - the system will route to the right agent
  • Be specific about dates, times, and locations
  • Use @AgentName to directly address a specific agent
        """
        print(help_text)
    
    async def show_status(self):
        """Display system status."""
        if not self.orchestrator:
            console_warning("Orchestrator not initialized", "CLI")
            return
            
        try:
            status = await self.orchestrator.get_agent_status()
            print(f"\n📊 System Status (Session: {status['session_id'][:8]}...)")
            print(f"   Total Agents: {status['total_agents']}")
            print(f"   CosmosDB: {'✅ Available' if status['cosmos_available'] else '❌ Not configured'}")
            print(f"   Telemetry: {'✅ Enabled' if status['telemetry_enabled'] else '❌ Disabled'}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n🤖 Agent Status:")
            for name, agent_info in status['agents'].items():
                status_icon = "✅" if agent_info['available'] else "❌"
                print(f"   {status_icon} {agent_info['name']}")
        except Exception as e:
            console_error(f"Failed to get status: {e}", "CLI")
    
    async def show_agents(self):
        """Display detailed agent information."""
        print("\n🤖 Available Agents:")
        
        agent_descriptions = {
            "ProxyAgent": {
                "icon": "📋",
                "purpose": "Main conversation handler and intelligent task router",
                "specialties": ["General conversation", "Task routing", "Context management"]
            },
            "CalendarAgent": {
                "icon": "📅", 
                "purpose": "Calendar operations and meeting scheduling",
                "specialties": ["Create events", "Check availability", "Find rooms", "Manage attendees"]
            },
            "DirectoryAgent": {
                "icon": "👥",
                "purpose": "User searches and organizational data",
                "specialties": ["Find users", "Get profiles", "Org hierarchy", "Department info"]
            },
            "LocationAgent": {
                "icon": "📍",
                "purpose": "Location-based searches and mapping",
                "specialties": ["Nearby places", "Business search", "Categories", "Geographic areas"]
            }
        }
        
        for agent_name, info in agent_descriptions.items():
            print(f"\n{info['icon']} {agent_name}")
            print(f"   Purpose: {info['purpose']}")
            print(f"   Specialties: {', '.join(info['specialties'])}")
    
    async def process_command(self, user_input: str) -> bool:
        """
        Process special commands.
        
        Returns:
            bool: True if command was processed, False if it's a regular message
        """
        command = user_input.strip().lower()
        
        if command == "/quit":
            console_info("👋 Goodbye!", "CLI")
            return True
        elif command == "/help":
            await self.show_help()
        elif command == "/status":
            await self.show_status()
        elif command == "/agents":
            await self.show_agents()
        elif command == "/reset":
            if self.orchestrator:
                await self.orchestrator.reset_conversation()
                console_info("🔄 Conversation history cleared", "CLI")
            else:
                console_warning("No active session to reset", "CLI")
        else:
            return False
        
        return True
    
    async def chat_loop(self):
        """Main chat interaction loop."""
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith('/'):
                    should_quit = await self.process_command(user_input)
                    if should_quit and user_input.lower() == "/quit":
                        break
                    continue
                
                # Process with multi-agent system
                if not self.orchestrator:
                    console_error("Multi-agent system not initialized", "CLI")
                    continue
                
                console_info("🤔 Processing with multi-agent system...", "CLI")
                response = await self.orchestrator.process_message(user_input)
                
                print(f"\n🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                console_info("\n👋 Interrupted by user. Goodbye!", "CLI")
                break
            except EOFError:
                console_info("\n👋 EOF received. Goodbye!", "CLI")
                break
            except Exception as e:
                console_error(f"Error in chat loop: {e}", "CLI")
                print("❌ Sorry, I encountered an error. Please try again.")
    
    async def run(self):
        """Run the multi-agent CLI application."""
        # Initialize the system
        success = await self.initialize()
        if not success:
            console_error("Failed to initialize. Exiting.", "CLI")
            return
        
        # Show welcome and start chat
        await self.show_welcome()
        await self.chat_loop()

async def main():
    """Main entry point for the CLI application."""
    cli = MultiAgentCLI()
    await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        console_error(f"Application error: {e}", "CLI")
        sys.exit(1)
