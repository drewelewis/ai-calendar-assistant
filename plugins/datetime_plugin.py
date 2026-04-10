# Copyright (c) Microsoft. All rights reserved.
from datetime import datetime, timezone, timedelta
from typing import Annotated

from semantic_kernel.functions import kernel_function


def _eastern_offset(dt_utc: datetime) -> tuple[timedelta, str]:
    """Return the UTC offset and abbreviation for US Eastern time at the given UTC moment."""
    year = dt_utc.year
    # DST starts: 2nd Sunday of March at 02:00 local (= 07:00 UTC)
    march_1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    first_sunday_march = march_1 + timedelta(days=(6 - march_1.weekday()) % 7)
    dst_start = first_sunday_march + timedelta(weeks=1, hours=7)  # 2nd Sunday 07:00 UTC
    # DST ends: 1st Sunday of November at 02:00 local (= 06:00 UTC)
    nov_1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    first_sunday_nov = nov_1 + timedelta(days=(6 - nov_1.weekday()) % 7)
    dst_end = first_sunday_nov + timedelta(hours=6)  # 1st Sunday 06:00 UTC

    if dst_start <= dt_utc < dst_end:
        return timedelta(hours=-4), "EDT"
    return timedelta(hours=-5), "EST"


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
    async def get_current_datetime(self) -> Annotated[str, "Current UTC date and time in ISO 8601 format with Eastern local time and offset"]:
        now = datetime.now(timezone.utc)
        offset, abbr = _eastern_offset(now)
        local = now + offset
        offset_hours = int(offset.total_seconds() // 3600)
        offset_str = f"{offset_hours:+03d}:00"
        return (
            f"{now.strftime('%Y-%m-%dT%H:%M:%S+00:00')} UTC ({now.strftime('%A')}) | "
            f"Eastern: {local.strftime('%Y-%m-%dT%H:%M:%S')}{offset_str} {abbr} | "
            f"Current Eastern offset: {offset_str} (for reference only — pass meeting times as Eastern local, no Z, no UTC conversion)"
        )
