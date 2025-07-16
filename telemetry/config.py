"""
OpenTelemetry configuration for Azure Monitor integration
Provides logging, metrics, and distributed tracing for the AI Calendar Assistant
"""

import os
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


class TelemetryConfig:
    """
    Configures OpenTelemetry for Azure Monitor integration with managed identity support.
    
    This class provides a simplified configuration that relies on azure-monitor-opentelemetry
    to handle the complex setup automatically.
    """
    
    def __init__(self, 
                 service_name: str = "ai-calendar-assistant",
                 service_version: str = "1.0.0",
                 log_level: int = logging.INFO):
        """
        Initialize telemetry configuration.
        
        Args:
            service_name: Name of the service for telemetry
            service_version: Version of the service
            log_level: Logging level for the application
        """
        self.service_name = service_name
        self.service_version = service_version
        self.log_level = log_level
        self.connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        self.is_configured = False
        
    def configure(self) -> bool:
        """
        Configure OpenTelemetry with Azure Monitor.
        
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            if not self.connection_string:
                print("⚠️  No Application Insights connection string found")
                print("   Set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable")
                return False
            
            print(f"🔧 Configuring telemetry for {self.service_name} v{self.service_version}")
            
            # Configure Azure Monitor with automatic setup
            configure_azure_monitor(
                connection_string=self.connection_string,
                resource=Resource.create({
                    SERVICE_NAME: self.service_name,
                    SERVICE_VERSION: self.service_version
                })
            )
            
            # Configure auto-instrumentation
            self._configure_auto_instrumentation()
            
            # Configure application logging
            self._configure_application_logging()
            
            self.is_configured = True
            print("✅ Telemetry configuration completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure telemetry: {e}")
            return False
    
    def _configure_auto_instrumentation(self):
        """Configure automatic instrumentation for common libraries."""
        try:
            # Instrument HTTP libraries
            RequestsInstrumentor().instrument()
            HTTPXClientInstrumentor().instrument()
            
            # Instrument logging
            LoggingInstrumentor().instrument(set_logging_format=True)
            
            print("✅ Auto-instrumentation configured")
            
        except Exception as e:
            print(f"⚠ Warning: Some auto-instrumentation failed: {e}")
    
    def _configure_application_logging(self):
        """Configure structured application logging."""
        # Set up root logger with appropriate level
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
        
        # Reduce noise from third-party libraries
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('opentelemetry').setLevel(logging.WARNING)
    
    def get_tracer(self, name: str = None):
        """Get a tracer instance."""
        tracer_name = name or self.service_name
        return trace.get_tracer(tracer_name)
    
    def get_meter(self, name: str = None):
        """Get a meter instance."""
        meter_name = name or self.service_name
        return metrics.get_meter(meter_name)
    
    def get_logger(self, name: str = None):
        """Get a logger instance."""
        logger_name = name or self.service_name
        return logging.getLogger(logger_name)
    
    def create_custom_metrics(self):
        """Create custom metrics for the application."""
        if not self.is_configured:
            return {}
        
        meter = self.get_meter()
        
        # Create metrics that the Agent class expects
        return {
            'chat_requests_total': meter.create_counter(
                name="chat_requests_total",
                description="Total number of chat requests processed",
                unit="1"
            ),
            'cosmosdb_operations_total': meter.create_counter(
                name="cosmosdb_operations_total", 
                description="Total number of CosmosDB operations",
                unit="1"
            ),
            'openai_api_calls_total': meter.create_counter(
                name="openai_api_calls_total",
                description="Total number of OpenAI API calls",
                unit="1"
            )
        }


# Global telemetry instance
_telemetry_config: Optional[TelemetryConfig] = None


def initialize_telemetry(service_name: str = "ai-calendar-assistant",
                        service_version: str = "1.0.0",
                        log_level: int = logging.INFO) -> bool:
    """
    Initialize OpenTelemetry configuration.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        log_level: Logging level
        
    Returns:
        bool: True if initialization was successful
    """
    global _telemetry_config
    
    if _telemetry_config is not None:
        print("✅ Telemetry already initialized")
        return _telemetry_config.is_configured
    
    _telemetry_config = TelemetryConfig(service_name, service_version, log_level)
    return _telemetry_config.configure()


def get_telemetry() -> Optional[TelemetryConfig]:
    """Get the global telemetry configuration instance."""
    return _telemetry_config


def get_tracer(name: str = None):
    """Get a tracer instance."""
    if _telemetry_config:
        return _telemetry_config.get_tracer(name)
    return trace.get_tracer(name or "default")


def get_meter(name: str = None):
    """Get a meter instance."""
    if _telemetry_config:
        return _telemetry_config.get_meter(name)
    return metrics.get_meter(name or "default")


def get_logger(name: str = None):
    """Get a logger instance."""
    if _telemetry_config:
        return _telemetry_config.get_logger(name)
    return logging.getLogger(name or "default")
