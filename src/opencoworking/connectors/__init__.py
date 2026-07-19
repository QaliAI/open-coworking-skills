"""Read-only connector prototypes (Mode 3).

Status: **mock-tested** - implemented against current official API
documentation (fetched 2026-07-18, recorded in docs/research/SOURCES.yaml)
and exercised only against mocked transports with sanitized fixtures.
NO live or sandbox validation has been performed; do not represent these
as live-tested. Offline Modes 1-2 never require these modules.

Design rules (enforced here and tested):
- credentials come from environment variables or explicit arguments,
  are never logged, and never appear in error messages
- read-only: no method issues anything but GET (token fetch uses POST to
  the auth endpoint only)
- pagination, retry with backoff on 429/5xx, timeouts, structured errors
- output rows use the vendor-neutral canonical schema
"""

from .base import ConnectorError, HttpTransport, Transport
from .hubspot import HubSpotClient
from .officernd import OfficeRnDClient

__all__ = ["ConnectorError", "HttpTransport", "Transport",
           "HubSpotClient", "OfficeRnDClient"]
