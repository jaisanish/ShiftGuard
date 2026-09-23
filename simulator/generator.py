"""
ShiftGuard Telemetry Frame Generator
====================================

Generates live, paced telemetry frames based on deterministic scenario sequences.
Advances timestamps to live UTC time while preserving exact physical relationships.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Generator, List, Optional

from simulator.scenarios import get_scenario_records


class TelemetryGenerator:
    """
    Paced telemetry stream generator.
    Translates static CSV scenario slices into a continuous live stream
    with real-time UTC timestamps.
    """

    def __init__(
        self,
        scenario: str = "normal",
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        loop: bool = False,
        base_step_seconds: float = 1.0,
    ):
        self.scenario = scenario
        self.machine_id = machine_id
        self.operator_id = operator_id
        self.loop = loop
        self.base_step_seconds = base_step_seconds

        # Load deterministic baseline rows
        self._base_records = get_scenario_records(
            scenario_name=scenario,
            machine_id=machine_id,
            operator_id=operator_id,
        )
        self._current_index = 0
        self._iteration_count = 0

    @property
    def total_records(self) -> int:
        return len(self._base_records)

    def generate_frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yield telemetry frames sequentially with fresh ISO 8601 UTC timestamps.
        If loop=True, loops continuously, advancing cumulative meters.
        """
        start_time = datetime.now(timezone.utc)
        cumulative_hours_offset = 0.0
        cumulative_fuel_offset = 0.0

        while True:
            for idx, raw_record in enumerate(self._base_records):
                frame = dict(raw_record)

                # Assign current real-time timestamp paced by sequence index
                frame_time = start_time + timedelta(
                    seconds=(self._iteration_count * len(self._base_records) + idx) * self.base_step_seconds
                )
                frame["timestamp"] = frame_time.isoformat().replace("+00:00", "Z")

                # Accumulate monotonic offsets across loops
                frame["engine_hours"] = round(frame["engine_hours"] + cumulative_hours_offset, 3)
                frame["fuel_used_l"] = round(frame["fuel_used_l"] + cumulative_fuel_offset, 2)

                yield frame

            if not self.loop:
                break

            self._iteration_count += 1
            # Add small monotonic progression on loop repeats
            cumulative_hours_offset += 0.02
            cumulative_fuel_offset += 1.5
