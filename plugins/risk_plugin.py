from datetime import datetime
import os
import asyncio
import json
from typing import List, Optional, Annotated, Dict, Any
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

# Import telemetry components first
from telemetry.decorators import TelemetryContext
from telemetry.console_output import console_info, console_debug, console_telemetry_event, console_error, console_warning

# Try to import the real RiskOperations, fallback to mock if it fails
try:
    from operations.risk_operations import RiskOperations
    console_info("✓ Using Risk Management Operations", module="RiskPlugin")
except Exception as e:
    console_error(f"⚠ Could not import RiskOperations: {e}", module="RiskPlugin")
    raise

try:
    from utils.teams_utilities import TeamsUtilities
    # Initialize TeamsUtilities for sending messages
    teams_utils = TeamsUtilities()
    TEAMS_UTILS_AVAILABLE = True
except ImportError as e:
    console_error(f"⚠ Teams utilities not available: {e}", module="RiskPlugin")
    TEAMS_UTILS_AVAILABLE = False
    
    # Fallback TeamsUtilities that does nothing
    class MockTeamsUtilities:
        def send_friendly_notification(self, message, session_id=None, debug=False):
            if debug:
                session_info = f"[session: {session_id}] " if session_id else ""
                print(f"TEAMS: {session_info}{message}")
    
    teams_utils = MockTeamsUtilities()

# Initialize risk operations
risk_operations = RiskOperations()

class RiskPlugin:
    def __init__(self, debug=False, session_id=None):
        self.debug = debug
        self.session_id = session_id

    # Helper method to log function calls if debug is enabled
    def _log_function_call(self, function_name, **kwargs):
        if self.debug:
            params_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            session_info = f"[session: {self.session_id}] " if self.session_id else ""
            print(f"DEBUG: {session_info}Calling kernel function '{function_name}' with parameters: {params_str}")
    
    # Helper method to send friendly notifications to the user
    def _send_friendly_notification(self, message: str):
        """Send a friendly notification to the user via Teams about what we're working on."""
        teams_utils.send_friendly_notification(message, self.session_id, self.debug)

    ############################## KERNEL FUNCTION START #####################################
    @kernel_function(
        description="""
        Retrieve comprehensive client risk profile and summary information by client ID.
        
        USE THIS WHEN:
        - User asks for "client information", "client profile", or "client summary"
        - Need to lookup specific client details by ID
        - User mentions client names like "LCOLE", "MERIDIAN", "QUANTUM" and needs their data
        - Requesting risk assessment or exposure information for a specific client
        - User asks "What do you know about client [ID/NAME]?"
        
        CAPABILITIES:
        - Returns complete client profile including financial exposures
        - Provides parent relationship information
        - Shows risk ratings and compliance status
        - Includes exposure amounts and credit risk metrics
        - Displays regional and industry information
        
        COMMON USE CASES:
        - "Show me information about client 5008373037"
        - "What's the risk profile for LCOLE?"
        - "Get client summary for MERIDIAN CAPITAL"
        - "Tell me about client exposures for ID 8009547821"
        - "What are the risk metrics for QUANTUM HEDGE?"
        
        Returns detailed JSON with client information including:
        - Basic client info (ID, name, parent relationships)
        - Financial data (exposure amounts, commitments, adjustments)
        - Risk assessment (ratings, compliance status)
        - Geographic and industry classification
        """
    )
    async def get_client_summary_by_id(self, client_id: Annotated[str, "The unique client ID to retrieve summary information for"]) -> Annotated[Dict[str, Any], "Returns comprehensive client summary with risk profile, exposures, and relationship data."]:
        self._log_function_call("get_client_summary_by_id", client_id=client_id)
        self._send_friendly_notification(f"🔍 Looking up client risk profile for ID: {client_id}...")
        
        if not client_id:
            raise ValueError("Error: client_id parameter is required")
        
        try:
            result = await risk_operations.get_client_summary_by_id(client_id)
            if result:
                console_info(f"✓ Client summary retrieved for {client_id}: {result.get('client_name', 'Unknown')}", module="RiskPlugin")
                self._send_friendly_notification(f"✅ Found client profile for {result.get('client_name', client_id)}")
                return result
            else:
                console_warning(f"⚠ Client not found for ID: {client_id}", module="RiskPlugin")
                self._send_friendly_notification(f"❌ No client found with ID: {client_id}")
                return {"error": f"Client not found for ID: {client_id}", "client_id": client_id}
                
        except Exception as e:
            console_error(f"❌ Error retrieving client summary for {client_id}: {str(e)}", module="RiskPlugin")
            self._send_friendly_notification(f"❌ Error looking up client {client_id}")
            return {"error": str(e), "client_id": client_id}

    @kernel_function(
        description="""
        Retrieve detailed risk metrics and financial exposure data for a specific client.
        
        USE THIS WHEN:
        - User asks specifically about "risk metrics", "exposure data", or "financial risk"
        - Need focused financial risk information without full client profile
        - User wants to analyze credit risk metrics or exposure amounts
        - Requesting specific financial data for risk assessment
        
        CAPABILITIES:
        - Returns focused risk and exposure data
        - Provides credit risk metrics and calculations
        - Shows exposure amounts and adjustments
        - Includes risk ratings and exposure types
        - Displays commitment amounts and changes
        
        COMMON USE CASES:
        - "What are the risk metrics for client 5008373037?"
        - "Show me exposure data for LCOLE"
        - "Get financial risk information for MERIDIAN"
        - "What's the credit risk for client 6007892341?"
        - "Show exposure amounts and adjustments"
        
        Returns focused financial risk data including:
        - Exposure amounts and types
        - Credit risk metrics
        - Adjustments and changes
        - Risk ratings and commitments
        """
    )
    async def get_client_risk_metrics(self, client_id: Annotated[str, "The unique client ID to retrieve risk metrics for"]) -> Annotated[Dict[str, Any], "Returns detailed risk metrics including exposures, credit risk data, and financial assessments."]:
        self._log_function_call("get_client_risk_metrics", client_id=client_id)
        self._send_friendly_notification(f"📊 Analyzing risk metrics for client: {client_id}...")
        
        if not client_id:
            raise ValueError("Error: client_id parameter is required")
        
        try:
            result = await risk_operations.get_client_risk_metrics(client_id)
            if result:
                console_info(f"✓ Risk metrics retrieved for client {client_id}", module="RiskPlugin")
                self._send_friendly_notification(f"✅ Risk analysis complete for client {client_id}")
                return result
            else:
                console_warning(f"⚠ Risk metrics not found for client ID: {client_id}", module="RiskPlugin")
                self._send_friendly_notification(f"❌ No risk data found for client: {client_id}")
                return {"error": f"Risk metrics not found for client ID: {client_id}", "client_id": client_id}
                
        except Exception as e:
            console_error(f"❌ Error retrieving risk metrics for {client_id}: {str(e)}", module="RiskPlugin")
            self._send_friendly_notification(f"❌ Error analyzing risk for client {client_id}")
            return {"error": str(e), "client_id": client_id}

    @kernel_function(
        description="""
        List all available clients in the risk management system.
        
        USE THIS WHEN:
        - User asks "what clients do you have?", "list clients", or "show all clients"
        - Need to display available client options
        - User wants to browse or discover available client data
        - Providing an overview of the client portfolio
        
        CAPABILITIES:
        - Returns mapping of client IDs to client names
        - Shows all clients currently in the system
        - Helps users discover available data
        - Provides client identification information
        
        COMMON USE CASES:
        - "What clients are available?"
        - "List all clients in the system"
        - "Show me the client directory"
        - "Which companies do you have data for?"
        - "What's in your client database?"
        
        Returns dictionary mapping client IDs to names.
        """
    )
    async def list_all_clients(self) -> Annotated[Dict[str, str], "Returns a dictionary mapping client IDs to client names for all available clients."]:
        self._log_function_call("list_all_clients")
        self._send_friendly_notification("📋 Retrieving client directory...")
        
        try:
            result = await risk_operations.list_all_clients()
            client_count = len(result)
            console_info(f"✓ Retrieved {client_count} clients from directory", module="RiskPlugin")
            self._send_friendly_notification(f"✅ Found {client_count} clients in the system")
            return result
                
        except Exception as e:
            console_error(f"❌ Error retrieving client list: {str(e)}", module="RiskPlugin")
            self._send_friendly_notification("❌ Error retrieving client directory")
            return {"error": str(e)}

    @kernel_function(
        description="""
        Search for clients by name or partial name match.
        
        USE THIS WHEN:
        - User provides a client name but not the ID
        - Need to find client ID from a company name
        - User says "find LCOLE", "lookup MERIDIAN", "search for QUANTUM"
        - Converting client names to IDs for further operations
        
        CAPABILITIES:
        - Case-insensitive name searching
        - Partial name matching
        - Returns client ID and full name
        - Helps bridge name-to-ID lookups
        
        COMMON USE CASES:
        - "Find client LCOLE"
        - "What's the ID for MERIDIAN CAPITAL?"
        - "Search for QUANTUM"
        - "Lookup James Financial"
        - "Find clients with 'Capital' in the name"
        
        Returns matching clients with their IDs and names.
        """
    )
    async def search_clients_by_name(self, search_term: Annotated[str, "The client name or partial name to search for"]) -> Annotated[Dict[str, Any], "Returns matching clients with their IDs and names."]:
        self._log_function_call("search_clients_by_name", search_term=search_term)
        self._send_friendly_notification(f"🔍 Searching for clients matching: {search_term}...")
        
        if not search_term:
            raise ValueError("Error: search_term parameter is required")
        
        try:
            all_clients = await risk_operations.list_all_clients()
            search_term_lower = search_term.lower()
            
            matching_clients = {}
            for client_id, client_name in all_clients.items():
                if search_term_lower in client_name.lower():
                    matching_clients[client_id] = client_name
            
            match_count = len(matching_clients)
            if match_count > 0:
                console_info(f"✓ Found {match_count} clients matching '{search_term}'", module="RiskPlugin")
                self._send_friendly_notification(f"✅ Found {match_count} matching clients")
                return {
                    "search_term": search_term,
                    "matches_found": match_count,
                    "matching_clients": matching_clients
                }
            else:
                console_warning(f"⚠ No clients found matching '{search_term}'", module="RiskPlugin")
                self._send_friendly_notification(f"❌ No clients found matching '{search_term}'")
                return {
                    "search_term": search_term,
                    "matches_found": 0,
                    "matching_clients": {},
                    "message": f"No clients found matching '{search_term}'"
                }
                
        except Exception as e:
            console_error(f"❌ Error searching for clients with term '{search_term}': {str(e)}", module="RiskPlugin")
            self._send_friendly_notification(f"❌ Error searching for '{search_term}'")
            return {"error": str(e), "search_term": search_term}

    @kernel_function(
        description="""
        Get risk rating summary and statistics across all clients.
        
        USE THIS WHEN:
        - User asks about "risk overview", "risk distribution", or "overall risk"
        - Need portfolio-level risk analysis
        - User wants to understand risk patterns across clients
        - Requesting risk dashboard or summary statistics
        
        CAPABILITIES:
        - Analyzes risk ratings across all clients
        - Provides risk distribution statistics
        - Shows client counts by risk level
        - Gives overall portfolio risk overview
        
        COMMON USE CASES:
        - "What's the overall risk profile?"
        - "Show me risk distribution across clients"
        - "How many high-risk clients do we have?"
        - "Give me a risk overview"
        - "What's our portfolio risk exposure?"
        
        Returns risk analysis and distribution data.
        """
    )
    async def get_portfolio_risk_overview(self) -> Annotated[Dict[str, Any], "Returns risk analysis and distribution across all clients in the portfolio."]:
        self._log_function_call("get_portfolio_risk_overview")
        self._send_friendly_notification("📊 Analyzing portfolio risk distribution...")
        
        try:
            all_clients = await risk_operations.list_all_clients()
            risk_summary = {
                "total_clients": len(all_clients),
                "risk_distribution": {
                    "High": 0,
                    "Medium-High": 0,
                    "Medium": 0,
                    "Low": 0,
                    "Not Rated": 0
                },
                "client_details": []
            }
            
            # Analyze each client's risk rating
            for client_id in all_clients.keys():
                try:
                    client_data = await risk_operations.get_client_summary_by_id(client_id)
                    if client_data:
                        risk_rating = client_data.get('risk_rating', 'Not Rated')
                        if risk_rating in risk_summary["risk_distribution"]:
                            risk_summary["risk_distribution"][risk_rating] += 1
                        else:
                            risk_summary["risk_distribution"]["Not Rated"] += 1
                        
                        risk_summary["client_details"].append({
                            "client_id": client_id,
                            "client_name": client_data.get('client_name', 'Unknown'),
                            "risk_rating": risk_rating,
                            "region": client_data.get('region', 'Unknown'),
                            "large_commitment_amount": client_data.get('large_commitment_amount', 0)
                        })
                except Exception as e:
                    console_warning(f"⚠ Could not analyze client {client_id}: {str(e)}", module="RiskPlugin")
            
            console_info(f"✓ Portfolio risk analysis complete for {risk_summary['total_clients']} clients", module="RiskPlugin")
            self._send_friendly_notification("✅ Portfolio risk analysis complete")
            return risk_summary
                
        except Exception as e:
            console_error(f"❌ Error generating portfolio risk overview: {str(e)}", module="RiskPlugin")
            self._send_friendly_notification("❌ Error analyzing portfolio risk")
            return {"error": str(e)}

    @kernel_function(
        description="""
        Get current date and time for risk analysis and reporting context.
        
        USE THIS WHEN:
        - Need current timestamp for risk reports
        - User asks "what time is it?" or "what's the current date?"
        - Providing context for risk data timestamps
        - Generating time-sensitive risk analysis
        
        Returns current date and time in ISO 8601 format.
        """
    )
    async def get_current_datetime(self) -> Annotated[str, "Returns the current date and time in ISO 8601 format."]:
        self._log_function_call("get_current_datetime")
        
        try:
            current_time = datetime.now().isoformat()
            console_debug(f"Current datetime: {current_time}", module="RiskPlugin")
            return current_time
        except Exception as e:
            console_error(f"❌ Error getting current datetime: {str(e)}", module="RiskPlugin")
            return {"error": str(e)}

    async def close(self):
        """
        Clean up resources when the plugin is no longer needed.
        """
        try:
            await risk_operations.close()
            console_info("Risk plugin resources cleaned up", module="RiskPlugin")
        except Exception as e:
            console_warning(f"Error during risk plugin cleanup: {e}", module="RiskPlugin")

