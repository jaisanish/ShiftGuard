"""
ShiftGuard Telemetry Simulator Subsystem
Simulates high-fidelity CAN-bus/J1939 telemetry streaming over WebSockets.
"""

from simulator.client import SimulatorClient
from simulator.generator import TelemetryGenerator
from simulator.scenarios import (
    SCENARIO_TASK_MAP,
    SCENARIO_DESCRIPTIONS,
    get_scenario_records,
)

__all__ = [
    "SimulatorClient",
    "TelemetryGenerator",
    "SCENARIO_TASK_MAP",
    "SCENARIO_DESCRIPTIONS",
    "get_scenario_records",
]
