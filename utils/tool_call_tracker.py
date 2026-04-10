import datetime
import threading
from typing import Any, Dict, List, Optional


class ToolCallTracker:
    _lock = threading.Lock()
    _tool_calls_by_session: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def add_call(
        cls,
        session_id: Optional[str],
        function_name: str,
        plugin_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not session_id or not function_name:
            return

        tool_call = {
            "type": "function_call",
            "function_name": function_name,
            "plugin_name": plugin_name,
            "arguments": arguments or {},
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        with cls._lock:
            cls._tool_calls_by_session.setdefault(session_id, []).append(tool_call)

    @classmethod
    def add_result(
        cls,
        session_id: Optional[str],
        function_name: str,
        plugin_name: Optional[str] = None,
        result: Optional[Any] = None,
    ) -> None:
        if not session_id or not function_name:
            return

        tool_result = {
            "type": "function_result",
            "function_name": function_name,
            "plugin_name": plugin_name,
            "result": str(result)[:500] if result is not None else None,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        with cls._lock:
            cls._tool_calls_by_session.setdefault(session_id, []).append(tool_result)

    @classmethod
    def consume(cls, session_id: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        if not session_id:
            return None

        with cls._lock:
            tool_calls = cls._tool_calls_by_session.pop(session_id, [])

        return tool_calls or None
