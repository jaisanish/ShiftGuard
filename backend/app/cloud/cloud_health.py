"""
Cloud Service Health
====================
"""

import logging
from typing import Dict, Any

from backend.app.cloud.cloud_db import check_cloud_db_health
from backend.app.config import settings

logger = logging.getLogger("shiftguard.cloud.health")


def get_cloud_health() -> Dict[str, Any]:
    """Check connectivity and health of the cloud backend database."""
    is_db_ok = check_cloud_db_health()
    return {
        "service": "shiftguard-cloud",
        "status": "healthy" if is_db_ok else "degraded",
        "database": "connected" if is_db_ok else "disconnected",
        "database_url_type": "postgresql" if "postgresql" in settings.CLOUD_DATABASE_URL else "sqlite",
    }
