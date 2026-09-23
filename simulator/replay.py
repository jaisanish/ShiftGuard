"""
ShiftGuard Telemetry Replay Simulator
=====================================

CLI entrypoint to stream deterministic synthetic CAT machinery telemetry
over WebSockets into the ShiftGuard Edge backend.

Usage:
    python simulator/replay.py --scenario normal
    python simulator/replay.py --scenario seatbelt_violation --speed 2.0
    python simulator/replay.py --scenario proximity_critical --machine-id CAT-797F-101
    python simulator/replay.py --scenario excessive_idle --loop
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

# Ensure workspace root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from simulator.client import SimulatorClient
from simulator.generator import TelemetryGenerator
from simulator.scenarios import SCENARIO_DESCRIPTIONS, SCENARIO_TASK_MAP


def parse_args():
    parser = argparse.ArgumentParser(
        description="ShiftGuard Live Telemetry Replay Simulator",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        choices=list(SCENARIO_TASK_MAP.keys()),
        help=(
            "Operational scenario to replay:\n"
            "  normal             : Nominal loaded hauling (TSK-DEMO-01)\n"
            "  seatbelt_violation : Unfastened seatbelt in motion (TSK-DEMO-02)\n"
            "  proximity_warning  : Spotting close to crusher 15m -> 8m (TSK-DEMO-03)\n"
            "  proximity_critical : Severe collision risk <3m & emergency stop (TSK-DEMO-04)\n"
            "  excessive_idle     : Engine idling >30 minutes (TSK-DEMO-05)\n"
            "  repeated_safety    : Multi-hazard: belt violation + proximity critical (TSK-DEMO-06)\n"
            "  eta_delay          : Severe ramp incline & muddy traction slip (TSK-DEMO-07)"
        ),
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Replay speed multiplier (default: 1.0 = 1 tick/sec; 2.0 = 2 ticks/sec)",
    )
    parser.add_argument(
        "--machine-id",
        type=str,
        default=None,
        help="Override machinery ID (e.g. CAT-797F-101)",
    )
    parser.add_argument(
        "--operator-id",
        type=str,
        default=None,
        help="Override operator ID (e.g. OP-101)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="ws://127.0.0.1:8000/ws/telemetry?role=simulator",
        help="Target WebSocket endpoint URL",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Continuously loop the scenario sequence until interrupted",
    )
    return parser.parse_args()


async def run_simulation(args):
    # Calculate sleep interval
    tick_delay = max(0.05, 1.0 / max(0.1, args.speed))

    generator = TelemetryGenerator(
        scenario=args.scenario,
        machine_id=args.machine_id,
        operator_id=args.operator_id,
        loop=args.loop,
        base_step_seconds=tick_delay,
    )

    client = SimulatorClient(url=args.url)

    print("\n" + "=" * 70)
    print(" SHIFTGUARD TELEMETRY REPLAY SIMULATOR")
    print("=" * 70)
    print(f" Scenario    : {args.scenario.upper()}")
    print(f" Description : {SCENARIO_DESCRIPTIONS.get(args.scenario, '')}")
    print(f" Target URL  : {args.url}")
    print(f" Speed Multi : {args.speed}x (interval: {tick_delay:.2f}s per tick)")
    print(f" Total Frames: {generator.total_records} frames per sequence")
    print(f" Loop Mode   : {'ENABLED (Press Ctrl+C to stop)' if args.loop else 'SINGLE-PASS'}")
    print("=" * 70 + "\n")

    connected = await client.connect()
    if not connected:
        print("[SIMULATOR] Failed to establish initial connection. Exiting.")
        return

    frame_counter = 0
    try:
        for frame in generator.generate_frames():
            frame_counter += 1
            ack = await client.send_frame(frame)
            if ack is None:
                # Reconnect attempt
                connected = await client.connect()
                if not connected:
                    print("[SIMULATOR] Reconnect failed. Aborting stream.")
                    break
                await client.send_frame(frame)

            await asyncio.sleep(tick_delay)

        print(f"\n[SIMULATOR] Simulation completed. Total frames streamed: {frame_counter}")

    except asyncio.CancelledError:
        print("\n[SIMULATOR] Simulation interrupted by user.")
    finally:
        await client.close()


def main():
    args = parse_args()
    try:
        asyncio.run(run_simulation(args))
    except KeyboardInterrupt:
        print("\n[SIMULATOR] Exited cleanly on KeyboardInterrupt.")


if __name__ == "__main__":
    main()
