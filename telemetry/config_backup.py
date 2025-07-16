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
    
    Features:
    - Distributed tracing for all HTTP requests and Azure service calls
    - Application metrics (performance counters, custom metrics)
    - Structured logging with correlation IDs
    - Azure service instrumentation (OpenAI, CosmosDB, Microsoft Graph)
    - Managed Identity authentication for secure credential-less setup
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 service_name: str = "ai-calendar-assistant",
                 service_version: str = "1.0.0",
                 enable_logging: bool = True,
                 enable_metrics: bool = True,
                 enable_tracing: bool = True,
                 log_level: str = "INFO"):
        """
        Initialize telemetry configuration.
        
        Args:
            connection_string: Application Insights connection string (optional if using managed identity)
            service_name: Name of the service for telemetry
            service_version: Version of the service
            enable_logging: Whether to enable logging export
            enable_metrics: Whether to enable metrics export
            enable_tracing: Whether to enable tracing export
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.connection_string = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.service_name = service_name
        self.service_version = service_version
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self.enable_tracing = enable_tracing
        self.log_level = getattr(logging, log_level.upper())
        
        self.tracer_provider = None
        self.meter_provider = None
        self.logger_provider = None
        self.tracer = None
        self.meter = None
        self.logger = None
        
    def configure(self) -> bool:
        """
        Configure OpenTelemetry with Azure Monitor.
        
        Returns:
            bool: True if configuration succeeded, False otherwise
        """
        try:
            # Create resource identification
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                SERVICE_VERSION: self.service_version,
                "service.instance.id": os.getenv("HOSTNAME", "local"),
                "azure.resource.group": os.getenv("AZURE_RESOURCE_GROUP", "unknown"),
                "deployment.environment": os.getenv("ENVIRONMENT", "development")
            })
            
            # Configure Azure Monitor if connection string is available
            if self.connection_string:
                print("✅ Configuring Azure Monitor with connection string")
                configure_azure_monitor(
                    connection_string=self.connection_string,
                    resource=resource,
                    enable_live_metrics=True,
                    logger_name=self.service_name
                )
            else:
                print("⚠ No Application Insights connection string found, configuring manual exporters")
                self._configure_manual_exporters(resource)
            
            # Configure auto-instrumentation for common libraries
            self._configure_instrumentation()
            
            # Get providers for custom telemetry
            self.tracer_provider = trace.get_tracer_provider()
            self.meter_provider = metrics.get_meter_provider()
            
            # Create tracer and meter for custom telemetry
            self.tracer = trace.get_tracer(self.service_name, self.service_version)
            self.meter = metrics.get_meter(self.service_name, self.service_version)
            
            # Configure application logging
            self._configure_application_logging()
            
            print(f"✅ OpenTelemetry configured successfully for {self.service_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure OpenTelemetry: {e}")
            return False
    
    def _configure_manual_exporters(self, resource: Resource):
        """Configure exporters manually when not using configure_azure_monitor."""
        credential = self._get_azure_credential()
        
        if self.enable_tracing:
            # Configure tracing
            trace_exporter = AzureMonitorTraceExporter(
                credential=credential,
                connection_string=self.connection_string
            )
            tracer_provider = TracerProvider(resource=resource)
            tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
            trace.set_tracer_provider(tracer_provider)
        
        if self.enable_metrics:
            # Configure metrics
            metric_exporter = AzureMonitorMetricExporter(
                credential=credential,
                connection_string=self.connection_string
            )
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=60000  # Export every 60 seconds
            )
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(meter_provider)
        
        if self.enable_logging:
            # Configure logging
            log_exporter = AzureMonitorLogExporter(
                credential=credential,
                connection_string=self.connection_string
            )
            logger_provider = LoggerProvider(resource=resource)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
            set_logger_provider(logger_provider)
    
    def _get_azure_credential(self):
        """Get Azure credential with fallback from managed identity to default."""
        try:
            # Try managed identity first (for production Azure environments)
            managed_identity_id = os.getenv("AZURE_CONTAINER_APP_MANAGED_IDENTITY_ID")
            if managed_identity_id:
                return ManagedIdentityCredential(client_id=managed_identity_id)
            else:
                return ManagedIdentityCredential()
        except Exception:
            # Fallback to default credential chain (for local development)
            return DefaultAzureCredential()
    
    def _configure_instrumentation(self):
        """Configure auto-instrumentation for common libraries."""
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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s]',
            handlers=[
                logging.StreamHandler(),
            ]
        )
        
        # Create application logger
        self.logger = logging.getLogger(self.service_name)
        
        # Suppress noisy loggers
        logging.getLogger("azure.core").setLevel(logging.WARNING)
        logging.getLogger("azure.identity").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
    
    def get_tracer(self) -> trace.Tracer:
        """Get the configured tracer for custom spans."""
        return self.tracer
    
    def get_meter(self) -> metrics.Meter:
        """Get the configured meter for custom metrics."""
        return self.meter
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger for application logging."""
        return self.logger
    
    def create_custom_metrics(self):
        """Create custom metrics for the application."""
        if not self.meter:
            return {}
        
        return {
            'chat_requests_total': self.meter.create_counter(
                name="chat_requests_total",
                description="Total number of chat requests processed",
                unit="1"
            ),
            'chat_request_duration': self.meter.create_histogram(
                name="chat_request_duration_ms",
                description="Duration of chat request processing",
                unit="ms"
            ),
            'openai_api_calls_total': self.meter.create_counter(
                name="openai_api_calls_total",
                description="Total number of OpenAI API calls",
                unit="1"
            ),
            'cosmosdb_operations_total': self.meter.create_counter(
                name="cosmosdb_operations_total",
                description="Total number of CosmosDB operations",
                unit="1"
            ),
            'graph_api_calls_total': self.meter.create_counter(
                name="graph_api_calls_total",
                description="Total number of Microsoft Graph API calls",
                unit="1"
            ),
            'active_sessions': self.meter.create_up_down_counter(
                name="active_sessions",
                description="Number of active chat sessions",
                unit="1"
            ),
            'memory_usage_bytes': self.meter.create_observable_gauge(
                name="memory_usage_bytes",
                description="Current memory usage in bytes",
                unit="By"
            )
        }


# Global telemetry instance
_telemetry_config: Optional[TelemetryConfig] = None


def initialize_telemetry(connection_string: Optional[str] = None, 
                        service_name: str = "ai-calendar-assistant",
                        service_version: str = "1.0.0") -> TelemetryConfig:
    """
    Initialize global telemetry configuration.
    
    Args:
        connection_string: Application Insights connection string
        service_name: Name of the service
        service_version: Version of the service
    
    Returns:
        TelemetryConfig: Configured telemetry instance
    """
    global _telemetry_config
    
    if _telemetry_config is None:
        _telemetry_config = TelemetryConfig(
            connection_string=connection_string,
            service_name=service_name,
            service_version=service_version
        )
        
        success = _telemetry_config.configure()
        if not success:
            print("⚠ Telemetry configuration failed, continuing without observability")
    
    return _telemetry_config


def get_telemetry() -> Optional[TelemetryConfig]:
    """Get the global telemetry configuration."""
    return _telemetry_config


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer."""
    return _telemetry_config.get_tracer() if _telemetry_config else None


def get_meter() -> Optional[metrics.Meter]:
    """Get the global meter."""
    return _telemetry_config.get_meter() if _telemetry_config else None


def get_logger() -> Optional[logging.Logger]:
    """Get the global logger."""
    return _telemetry_config.get_logger() if _telemetry_config else logging.getLogger(__name__)
