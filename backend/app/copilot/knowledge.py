"""Small, versioned local knowledge base for the offline cab copilot."""

KNOWLEDGE_VERSION = "cab-guidance-v1"
DOCUMENTS = [
    {"id": "safety-proximity", "title": "Proximity clearance", "text": "Follow the deterministic in-cab proximity alert. Stop and follow site procedure when directed. The copilot cannot clear, acknowledge, or override safety interlocks."},
    {"id": "safety-seatbelt", "title": "Seatbelt procedure", "text": "Fasten the seatbelt before operating. If the edge system reports an unfastened seatbelt, stop safely and correct it. Only the operator can acknowledge an alert after the condition is addressed."},
    {"id": "machine-health", "title": "Machine health check", "text": "Check engine RPM, load, coolant temperature, hydraulic oil temperature, fault code, and operating state. Treat displayed edge warnings and critical alerts as the source of truth."},
    {"id": "dispatch-eta", "title": "Dispatch and ETA", "text": "Planned time is the dispatch baseline. The ETA model gives advisory duration, remaining minutes, and an uncertainty band. Synthetic validation metrics do not establish real-world accuracy."},
    {"id": "offline-operation", "title": "Offline operation", "text": "The edge node stores safety and telemetry locally before synchronization. Loss of cloud connectivity must not disable deterministic edge safety behavior."},
]
