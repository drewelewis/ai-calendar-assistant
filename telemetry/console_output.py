"""
Smart console output for telemetry events
Provides configurable console printing without code littering
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ConsoleLevel(Enum):
    """Console output levels"""
    DISABLED = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    TRACE = 5


class TelemetryConsole:
    """
    Smart console output for telemetry events that can be configured
    via environment variables without littering the codebase.
    """
    
    def __init__(self):
        # Read configuration from environment
        console_level = os.getenv('TELEMETRY_CONSOLE_LEVEL', 'INFO').upper()
        self.enabled = os.getenv('TELEMETRY_CONSOLE_ENABLED', 'true').lower() == 'true'
        self.use_colors = os.getenv('TELEMETRY_CONSOLE_COLORS', 'true').lower() == 'true'
        self.include_timestamp = os.getenv('TELEMETRY_CONSOLE_TIMESTAMP', 'true').lower() == 'true'
        self.include_module = os.getenv('TELEMETRY_CONSOLE_MODULE', 'false').lower() == 'true'
        
        # Set level
        try:
            self.level = ConsoleLevel[console_level]
        except KeyError:
            self.level = ConsoleLevel.INFO
        
        # Color codes (if enabled)
        self.colors = {
            'RESET': '\033[0m' if self.use_colors else '',
            'BOLD': '\033[1m' if self.use_colors else '',
            'RED': '\033[91m' if self.use_colors else '',
            'YELLOW': '\033[93m' if self.use_colors else '',
            'GREEN': '\033[92m' if self.use_colors else '',
            'BLUE': '\033[94m' if self.use_colors else '',
            'CYAN': '\033[96m' if self.use_colors else '',
            'MAGENTA': '\033[95m' if self.use_colors else '',
            'GRAY': '\033[90m' if self.use_colors else '',
        }
    
    def _should_print(self, level: ConsoleLevel) -> bool:
        """Check if we should print at this level"""
        return self.enabled and level.value <= self.level.value
    
    def _format_message(self, level: str, message: str, module: Optional[str] = None) -> str:
        """Format a console message"""
        parts = []
        
        # Add timestamp
        if self.include_timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # milliseconds
            parts.append(f"{self.colors['GRAY']}[{timestamp}]{self.colors['RESET']}")
        
        # Add level with color
        level_colors = {
            'ERROR': self.colors['RED'],
            'WARN': self.colors['YELLOW'],
            'INFO': self.colors['GREEN'],
            'DEBUG': self.colors['BLUE'],
            'TRACE': self.colors['CYAN'],
        }
        color = level_colors.get(level, '')
        parts.append(f"{color}{level:5}{self.colors['RESET']}")
        
        # Add module if requested
        if self.include_module and module:
            parts.append(f"{self.colors['GRAY']}[{module}]{self.colors['RESET']}")
        
        # Add message
        parts.append(message)
        
        return ' '.join(parts)
    
    def error(self, message: str, module: Optional[str] = None, **kwargs):
        """Print error level message"""
        if self._should_print(ConsoleLevel.ERROR):
            formatted = self._format_message('ERROR', message, module)
            print(formatted, file=sys.stderr, **kwargs)
    
    def warning(self, message: str, module: Optional[str] = None, **kwargs):
        """Print warning level message"""
        if self._should_print(ConsoleLevel.WARNING):
            formatted = self._format_message('WARN', message, module)
            print(formatted, **kwargs)
    
    def info(self, message: str, module: Optional[str] = None, **kwargs):
        """Print info level message"""
        if self._should_print(ConsoleLevel.INFO):
            formatted = self._format_message('INFO', message, module)
            print(formatted, **kwargs)
    
    def debug(self, message: str, module: Optional[str] = None, **kwargs):
        """Print debug level message"""
        if self._should_print(ConsoleLevel.DEBUG):
            formatted = self._format_message('DEBUG', message, module)
            print(formatted, **kwargs)
    
    def trace(self, message: str, module: Optional[str] = None, **kwargs):
        """Print trace level message"""
        if self._should_print(ConsoleLevel.TRACE):
            formatted = self._format_message('TRACE', message, module)
            print(formatted, **kwargs)
    
    def telemetry_event(self, event_type: str, details: Dict[str, Any], module: Optional[str] = None):
        """Print a telemetry event with structured information"""
        if not self._should_print(ConsoleLevel.INFO):
            return
        
        # Format event details
        detail_parts = []
        for key, value in details.items():
            if isinstance(value, (int, float)) and key.endswith(('_tokens', '_cost', '_duration', '_ms')):
                # Format numeric values nicely
                if key.endswith('_cost'):
                    detail_parts.append(f"{key}=${value:.4f}")
                elif key.endswith(('_duration', '_ms')):
                    detail_parts.append(f"{key}={value:.1f}ms")
                else:
                    detail_parts.append(f"{key}={value}")
            else:
                detail_parts.append(f"{key}={value}")
        
        detail_str = ' '.join(detail_parts)
        
        # Use different icons for different event types
        icons = {
            'openai_call': '🤖',
            'cosmosdb_op': '🌐',
            'token_usage': '📊',
            'chat_request': '💬',
            'error': '❌',
            'warning': '⚠️',
            'success': '✅',
            'span_start': '🔵',
            'span_end': '🟢',
        }
        
        icon = icons.get(event_type, '📡')
        message = f"{icon} {event_type.upper()}: {detail_str}"
        
        formatted = self._format_message('INFO', message, module)
        print(formatted)
    
    def span_start(self, span_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Print span start event"""
        if not self._should_print(ConsoleLevel.DEBUG):
            return
        
        details = {'span': span_name}
        if attributes:
            details.update(attributes)
        
        self.telemetry_event('span_start', details)
    
    def span_end(self, span_name: str, duration_ms: float, status: str = 'OK', attributes: Optional[Dict[str, Any]] = None):
        """Print span end event"""
        if not self._should_print(ConsoleLevel.DEBUG):
            return
        
        details = {
            'span': span_name,
            'duration_ms': duration_ms,
            'status': status
        }
        if attributes:
            details.update(attributes)
        
        self.telemetry_event('span_end', details)
    
    def token_usage(self, model: str, input_tokens: int, output_tokens: int, total_cost: float, operation: str = 'chat'):
        """Print token usage event"""
        if not self._should_print(ConsoleLevel.INFO):
            return
        
        details = {
            'model': model,
            'operation': operation,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'estimated_cost': total_cost
        }
        
        self.telemetry_event('token_usage', details)


# Global console instance
_console: Optional[TelemetryConsole] = None


def get_telemetry_console() -> TelemetryConsole:
    """Get the global telemetry console instance"""
    global _console
    if _console is None:
        _console = TelemetryConsole()
    return _console


# Convenience functions for direct use
def console_error(message: str, module: Optional[str] = None, **kwargs):
    """Print error to console if enabled"""
    get_telemetry_console().error(message, module, **kwargs)


def console_warning(message: str, module: Optional[str] = None, **kwargs):
    """Print warning to console if enabled"""
    get_telemetry_console().warning(message, module, **kwargs)


def console_info(message: str, module: Optional[str] = None, **kwargs):
    """Print info to console if enabled"""
    get_telemetry_console().info(message, module, **kwargs)


def console_debug(message: str, module: Optional[str] = None, **kwargs):
    """Print debug to console if enabled"""
    get_telemetry_console().debug(message, module, **kwargs)


def console_trace(message: str, module: Optional[str] = None, **kwargs):
    """Print trace to console if enabled"""
    get_telemetry_console().trace(message, module, **kwargs)


def console_telemetry_event(event_type: str, details: Dict[str, Any], module: Optional[str] = None):
    """Print telemetry event to console if enabled"""
    get_telemetry_console().telemetry_event(event_type, details, module)


def console_span_start(span_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Print span start to console if enabled"""
    get_telemetry_console().span_start(span_name, attributes)


def console_span_end(span_name: str, duration_ms: float, status: str = 'OK', attributes: Optional[Dict[str, Any]] = None):
    """Print span end to console if enabled"""
    get_telemetry_console().span_end(span_name, duration_ms, status, attributes)


def console_token_usage(model: str, input_tokens: int, output_tokens: int, total_cost: float, operation: str = 'chat'):
    """Print token usage to console if enabled"""
    get_telemetry_console().token_usage(model, input_tokens, output_tokens, total_cost, operation)
