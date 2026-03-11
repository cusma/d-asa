"""ACTUS Contract normalization to AVM.

This package provides functionality to normalize ACTUS contract attributes
into AVM-compatible representations with proper separation of concerns:

- conversions: Unit and rate conversion utilities
- calculations: Financial calculations (interest, principal payments)
- event_seeds: Event seed management and utilities
- schedules: Schedule resolution for various event types
- annuity: Annuity-specific calculations
- builders: Contract-type specific schedule builders
- ann_builder: ANN contract schedule builder
- core: Main normalization logic

Public API:
- normalize_contract_attributes: Main normalization function
- Helper utilities for testing and advanced use cases
"""

from .conversions import (
    compute_initial_exchange_amount as _compute_initial_exchange_amount,
)
from .conversions import (
    rate_to_fp as _rate_to_fp,
)
from .conversions import (
    to_asa_units as _to_asa_units,
)
from .core import normalize_contract_attributes
from .event_seeds import (
    EventSeed as _EventSeed,
)
from .event_seeds import (
    deduplicate_timestamps as _deduplicate_timestamps,
)

__all__ = [
    # Expose private utilities for backward compatibility with tests
    "_EventSeed",
    "_compute_initial_exchange_amount",
    "_deduplicate_timestamps",
    "_rate_to_fp",
    "_to_asa_units",
    "normalize_contract_attributes",
]
