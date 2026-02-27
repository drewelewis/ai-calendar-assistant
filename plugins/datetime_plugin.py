# Copyright (c) Microsoft. All rights reserved.
from datetime import datetime, timezone
from typing import Annotated

from semantic_kernel.functions import kernel_function


class DateTimePlugin:
    """Provides the current UTC date and time to agents as a kernel function."""

    @kernel_function(
        description="""
        Returns the current date and time in UTC (ISO 8601 format).

        USE THIS WHEN:
        - You need to know today's date before creating or querying calendar events
        - User refers to relative dates such as "tomorrow", "next Monday", "end of the month"
        - You need to compute a start or end time for a new event
        - Any date arithmetic is required

        ALWAYS call this first before any date-related calendar operation.
        Never assume or hard-code the current date.
        """
    )
    async def get_current_datetime(self) -> Annotated[str, "Current UTC date and time in ISO 8601 format, e.g. '2026-03-15T14:32:00+00:00 (Sunday)'"]:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S+00:00 (%A)")
