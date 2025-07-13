"""
PostgreSQL checkpoint utilities for LangGraph conversation state management.
"""

import os
import psycopg2
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv

load_dotenv(override=True)

class PostgresCheckpointManager:
    """Manages PostgreSQL checkpointing for LangGraph."""
    
    def __init__(self):
        self.connection = None
        self.checkpointer = None
        
    def create_connection_string(self):
        """Create PostgreSQL connection string from environment variables."""
        return f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    
    def connect(self):
        """Create and return a PostgreSQL checkpointer."""
        try:
            connection_string = self.create_connection_string()
            self.checkpointer = PostgresSaver.from_conn_string(connection_string)
            
            # Setup the checkpoint tables if they don't exist
            self.checkpointer.setup()
            
            return self.checkpointer
            
        except Exception as e:
            print(f"❌ Error connecting to PostgreSQL: {e}")
            print("📋 Please ensure PostgreSQL is running and connection details are correct.")
            print("🔧 Check your .env file for correct POSTGRES_* variables.")
            raise
    
    def disconnect(self):
        """Close the PostgreSQL connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.checkpointer = None
                print("✓ PostgreSQL connection closed.")
        except Exception as e:
            print(f"⚠ Error closing PostgreSQL connection: {e}")
    
    def reset(self):
        """Reset the checkpointer by creating a new connection."""
        self.disconnect()
        return self.connect()

def create_postgres_checkpointer():
    """Convenience function to create a PostgreSQL checkpointer."""
    manager = PostgresCheckpointManager()
    return manager.connect()
