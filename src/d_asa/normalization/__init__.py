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

from .core import normalize_contract_attributes

__all__ = [
    "normalize_contract_attributes",
]
