import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import asyncio

# CRITICAL: Check telemetry disable flag BEFORE any other imports
TELEMETRY_EXPLICITLY_DISABLED = os.environ.get('TELEMETRY_EXPLICITLY_DISABLED', '').lower() in ('true', '1', 'yes')

if TELEMETRY_EXPLICITLY_DISABLED:
    print("🚫 Telemetry explicitly disabled via environment variable")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without loading .env file
    pass

# Production-grade telemetry import with timeout and graceful fallback
import threading
import time
import concurrent.futures

TELEMETRY_AVAILABLE = False
TELEMETRY_IMPORT_TIMEOUT = 5  # Reduced timeout for faster feedback

def _safe_import_telemetry():
    """
    Safely import telemetry components with timeout to prevent hanging.
    Uses threading to avoid blocking the main application.
    """
    global TELEMETRY_AVAILABLE
    
    try:
        # Check if telemetry is explicitly disabled FIRST
        if TELEMETRY_EXPLICITLY_DISABLED:
            print("🚫 Telemetry disabled - skipping import")
            return False
            
        print(f"🔄 Attempting telemetry import with {TELEMETRY_IMPORT_TIMEOUT}s timeout...")
        
        # Use ThreadPoolExecutor to import with timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_import_telemetry_modules)
            try:
                # Wait for import with timeout
                return future.result(timeout=TELEMETRY_IMPORT_TIMEOUT)
            except concurrent.futures.TimeoutError:
                print(f"⏰ Telemetry import timed out after {TELEMETRY_IMPORT_TIMEOUT} seconds")
                print("🔄 Continuing with fallback implementations")
                return False
            except Exception as e:
                print(f"⚠️  Telemetry import failed: {e}")
                print("🔄 Using fallback implementations")
                return False
                
    except Exception as e:
        print(f"⚠️  Error during telemetry import process: {e}")
        return False

def _import_telemetry_modules():
    """
    Internal function to import telemetry modules.
    This runs in a separate thread to enable timeout handling.
    """
    try:
        print("📦 Importing telemetry modules...")
        
        from telemetry import (
            trace_async_method,
            measure_performance,
            get_tracer,
            get_meter,
            get_logger
        )
        
        from telemetry.console_output import (
            console_info,
            console_debug,
            console_warning,
            console_error,
            console_telemetry_event
        )
        
        # Store in global namespace for main thread access
        globals().update({
            'trace_async_method': trace_async_method,
            'measure_performance': measure_performance,
            'get_tracer': get_tracer,
            'get_meter': get_meter,
            'get_logger': get_logger,
            'console_info': console_info,
            'console_debug': console_debug,
            'console_warning': console_warning,
            'console_error': console_error,
            'console_telemetry_event': console_telemetry_event
        })
        
        print("✅ Telemetry components loaded successfully")
        return True
        
    except ImportError as e:
        print(f"📦 Telemetry modules not available: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Unexpected error importing telemetry: {e}")
        return False

# Perform telemetry import with timeout
TELEMETRY_AVAILABLE = _safe_import_telemetry()

# Fallback implementations if telemetry import fails
if not TELEMETRY_AVAILABLE:
    print("🔄 Using fallback telemetry implementations")
    
    def trace_async_method(name, include_args=False):
        """Fallback decorator that does nothing"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def measure_performance(name):
        """Fallback decorator that does nothing"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_tracer():
        """Fallback tracer"""
        return None
    
    def get_meter():
        """Fallback meter"""
        return None
    
    def get_logger():
        """Fallback logger"""
        return None
    
    def console_info(message, service="RiskOps"):
        print(f"ℹ️  [{service}] {message}")
    
    def console_debug(message, service="RiskOps"):
        print(f"🐛 [{service}] {message}")
    
    def console_warning(message, service="RiskOps"):
        print(f"⚠️  [{service}] {message}")
    
    def console_error(message, service="RiskOps"):
        print(f"❌ [{service}] {message}")
    
    def console_telemetry_event(event_name, properties, service="RiskOps"):
        print(f"📊 [{service}] {event_name}: {properties}")

class RiskOperations:
    def __init__(self):
        """
        Initialize the RiskOperations class.
        This class provides methods to interact with risk management data via mocked API.
        """
        
        # Load client data from CSV at startup - held in memory for fast lookups
        self._mock_client_data = self._load_client_data()
        
        console_info(f"Risk Operations initialized with {len(self._mock_client_data)} clients (telemetry: {'enabled' if TELEMETRY_AVAILABLE else 'disabled'})", "RiskOps")

    def _load_client_data(self) -> Dict[str, Any]:
        """
        Load client risk data from JSON file into memory at startup.
        Falls back to empty dict if file is missing or unreadable.
        """
        json_path = Path(__file__).parent / "risk_data.json"

        if not json_path.exists():
            console_warning(f"Risk data file not found: {json_path}", "RiskOps")
            return {}

        try:
            with open(json_path, encoding="utf-8-sig") as f:
                data: Dict[str, Any] = json.load(f)
            # Stamp last_updated at load time
            loaded_at = datetime.now().isoformat()
            for record in data.values():
                record["last_updated"] = loaded_at
            console_info(f"Loaded {len(data)} client records from {json_path.name}", "RiskOps")
            return data
        except Exception as e:
            console_error(f"Failed to load risk data JSON: {e}", "RiskOps")
            return {}

    @trace_async_method("get_client_summary_by_id", include_args=True)
    @measure_performance("risk_client_summary_lookup")
    async def get_client_summary_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client summary by client ID.
        
        Args:
            client_id (str): The client ID to lookup
            
        Returns:
            Optional[Dict[str, Any]]: Client summary data or None if not found
        """
        try:
            console_info(f"Looking up client summary for ID: {client_id}", "RiskOps")
            
            # Simulate API call delay (remove in real implementation)
            await asyncio.sleep(0.1)
            
            # Mock API lookup
            if client_id in self._mock_client_data:
                client_data = self._mock_client_data[client_id].copy()
                
                console_info(f"Client summary found for {client_id}: {client_data['client_name']}", "RiskOps")
                
                console_telemetry_event("client_summary_retrieved", {
                    "client_id": client_id,
                    "client_name": client_data['client_name'],
                    "parent_client": client_data['parent_client_relationship']['name'],
                    "country": client_data['country'],
                    "region": client_data['region']
                }, "RiskOps")
                
                return client_data
            else:
                console_warning(f"Client not found for ID: {client_id}", "RiskOps")
                console_telemetry_event("client_not_found", {
                    "client_id": client_id
                }, "RiskOps")
                return None
                
        except Exception as e:
            console_error(f"Error retrieving client summary for {client_id}: {str(e)}", "RiskOps")
            console_telemetry_event("client_summary_error", {
                "client_id": client_id,
                "error": str(e)
            }, "RiskOps")
            return None

    @trace_async_method("get_client_risk_metrics", include_args=True)
    @measure_performance("risk_metrics_lookup")
    async def get_client_risk_metrics(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed risk metrics for a client.
        
        Args:
            client_id (str): The client ID to lookup
            
        Returns:
            Optional[Dict[str, Any]]: Risk metrics data or None if not found
        """
        try:
            console_info(f"Looking up risk metrics for client ID: {client_id}", "RiskOps")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Mock API lookup
            if client_id in self._mock_client_data:
                client_data = self._mock_client_data[client_id]
                
                risk_metrics = {
                    "client_id": client_id,
                    "exposure_amounts": client_data['exposure_amounts'],
                    "adjustments_changes": client_data['adjustments_changes'],
                    "large_commitment_amount": client_data['large_commitment_amount'],
                    "additional_credit_risk_metrics": client_data['additional_credit_risk_metrics'],
                    "exposure_type": client_data['exposure_type'],
                    "risk_rating": client_data.get('risk_rating', 'Not Rated'),
                    "last_updated": client_data['last_updated']
                }
                
                console_info(f"Risk metrics found for {client_id}", "RiskOps")
                
                return risk_metrics
            else:
                console_warning(f"Risk metrics not found for ID: {client_id}", "RiskOps")
                return None
                
        except Exception as e:
            console_error(f"Error retrieving risk metrics for {client_id}: {str(e)}", "RiskOps")
            return None

    @trace_async_method("add_mock_client", include_args=True)
    async def add_mock_client(self, client_data: Dict[str, Any]) -> bool:
        """
        Add a new mock client to the data store (for testing purposes).
        
        Args:
            client_data (Dict[str, Any]): Client data to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if 'client_id' not in client_data:
                console_error("Client data missing required 'client_id' field", "RiskOps")
                return False
                
            client_id = client_data['client_id']
            client_data['last_updated'] = datetime.now().isoformat()
            
            self._mock_client_data[client_id] = client_data
            
            console_info(f"Mock client added: {client_id}", "RiskOps")
            console_telemetry_event("mock_client_added", {
                "client_id": client_id,
                "client_name": client_data.get('client_name', 'Unknown')
            }, "RiskOps")
            
            return True
            
        except Exception as e:
            console_error(f"Error adding mock client: {str(e)}", "RiskOps")
            return False

    @trace_async_method("list_all_clients")
    async def list_all_clients(self) -> Dict[str, str]:
        """
        List all available clients in the mock data store.
        
        Returns:
            Dict[str, str]: Dictionary mapping client IDs to client names
        """
        try:
            console_info("Listing all available clients", "RiskOps")
            
            clients = {
                client_id: data['client_name'] 
                for client_id, data in self._mock_client_data.items()
            }
            
            console_info(f"Found {len(clients)} clients", "RiskOps")
            return clients
            
        except Exception as e:
            console_error(f"Error listing clients: {str(e)}", "RiskOps")
            return {}

    async def close(self):
        """
        Clean up resources.
        """
        pass  # No persistent connections to close

