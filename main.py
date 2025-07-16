import re
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize telemetry early
from telemetry.config import initialize_telemetry, get_logger

if __name__ == "__main__":
    # Initialize OpenTelemetry
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    service_name = os.getenv("TELEMETRY_SERVICE_NAME", "ai-calendar-assistant")
    service_version = os.getenv("TELEMETRY_SERVICE_VERSION", "1.0.0")
    
    # Initialize telemetry - it reads connection_string from environment
    telemetry_success = initialize_telemetry(
        service_name=service_name,
        service_version=service_version
    )
    
    if telemetry_success:
        logger = get_logger()
        logger.info(f"Starting {service_name} v{service_version}")
    else:
        print(f"⚠️ Telemetry initialization failed, continuing without telemetry")
    
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8989,
            log_level="debug",
            reload=False,)
    except Exception as e:
        print("Unable to start the uvicorn server")
        print(e)
        if telemetry_success:
            logger = get_logger()
            logger.error(f"Failed to start uvicorn server: {e}")