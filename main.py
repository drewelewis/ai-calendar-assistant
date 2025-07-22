import re
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize telemetry early
from telemetry.config import initialize_telemetry, get_logger
from telemetry.console_output import console_info, console_warning, console_error

if __name__ == "__main__":
    # Initialize OpenTelemetry
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant")
    service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")
    uvicorn_timeout = os.getenv("UVICORN_TIMEOUT", "60")

    # Initialize telemetry - it reads connection_string from environment
    telemetry_success = initialize_telemetry(
        service_name=service_name,
        service_version=service_version
    )
    
    if telemetry_success:
        logger = get_logger()
        logger.info(f"Starting {service_name} v{service_version}")
        console_info(f"Starting {service_name} v{service_version}")
    else:
        console_warning("Telemetry initialization failed, continuing without telemetry")
    
    try:
        import uvicorn
        console_info("Starting uvicorn server...", "MAIN")
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8989,
            log_level="debug",
            reload=False,
            timeout_keep_alive=int(uvicorn_timeout),
            timeout_graceful_shutdown=30,
            access_log=True)
    except Exception as e:
        console_error(f"Unable to start the uvicorn server: {e}", "MAIN")
        if telemetry_success:
            logger = get_logger()
            logger.error(f"Failed to start uvicorn server: {e}")