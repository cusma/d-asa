"""Unit conversion utilities for ACTUS to AVM normalization."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from .. import constants as cst
from ..errors import ActusNormalizationError


def to_asa_units(amount: int | float | Decimal, asa_decimals: int) -> int:
    """
    Convert a decimal amount to ASA base units (uint64).

    Scales the amount by 10^asa_decimals to represent fractional values as integers.

    Example:
        >>> to_asa_units(100.42, 3)  # 100.42 with 3 decimals
        100420
        >>> to_asa_units(100, 2)  # 100 with 2 decimals
        10000

    Args:
        amount: The numeric value to convert.
        asa_decimals: Number of decimal places for the ASA.

    Returns:
        The amount in ASA base units as an integer.

    Raises:
        TypeError: If value is not int, float, or Decimal.
        ActusNormalizationError: If result exceeds uint64 bounds.
    """
    if isinstance(amount, (int, float, Decimal)):
        scale = cast(int, 10**asa_decimals)
        amount_decimal = Decimal(str(amount))
        scale_decimal = Decimal(scale)
        result = int(amount_decimal * scale_decimal)
    else:
        raise TypeError(f"Unsupported value type: {type(amount)}")

    if result < 0 or result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Value {amount} results in {result} which exceeds uint64 bounds"
        )

    return result


def rate_to_fp(value: int | float | Decimal) -> int:
    """
    Convert decimal rates to fixed-point integer representation.

    Scales decimal rates by FIXED_POINT_SCALE for AVM-compatible uint64 storage.

    Example:
        >>> rate_to_fp(0.05)  # 5% rate with FIXED_POINT_SCALE=1_000_000_000
        50000000

    Args:
        value: The rate value (e.g., 0.05 for 5%).

    Returns:
        Fixed-point scaled rate as uint64 integer.

    Raises:
        TypeError: If value is not int, float, or Decimal.
        ActusNormalizationError: If result exceeds uint64 bounds.
    """
    if isinstance(value, (int, float, Decimal)):
        value_decimal = Decimal(str(value))
        scale_decimal = Decimal(cst.FIXED_POINT_SCALE)
        result = int(value_decimal * scale_decimal)
    else:
        raise TypeError(f"Unsupported value type: {type(value)}")

    if result < 0 or result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Value {value} results in {result} which exceeds uint64 bounds"
        )

    return result


def compute_initial_exchange_amount(
    notional: int | float | Decimal,
    premium_discount_at_ied: int | float | Decimal,
    asa_decimals: int,
) -> int:
    """
    Calculate the initial exchange amount adjusted for premium/discount.

    Returns the net notional after subtracting any premium/discount at IED
    (Initial Exchange Date).

    Args:
        notional: The notional principal amount.
        premium_discount_at_ied: Premium/discount adjustment at IED.
            Positive value = discount (reduces notional)
            Negative value = premium (increases notional)
        asa_decimals: Number of decimal places for the ASA.

    Returns:
        Net initial exchange amount in ASA base units.

    Raises:
        ActusNormalizationError: If result is negative or exceeds uint64 bounds.
    """
    notional = to_asa_units(notional, asa_decimals)

    # Handle premium (negative) and discount (positive) separately
    # to avoid to_asa_units rejecting negative values
    scale = cast(int, 10**asa_decimals)
    notional_display = notional / scale
    if premium_discount_at_ied >= 0:
        pdied = to_asa_units(premium_discount_at_ied, asa_decimals)
        # Validate that discount doesn't exceed notional (would result in negative amount)
        if pdied > notional:
            raise ActusNormalizationError(
                f"Premium/discount at IED ({premium_discount_at_ied}) exceeds notional "
                f"({notional_display}), which would result in a negative "
                f"initial exchange amount. This is invalid for uint64 encoding."
            )
        result = notional - pdied
    else:
        # For negative premium_discount (premium), convert absolute value and add
        pdied = to_asa_units(-premium_discount_at_ied, asa_decimals)
        result = notional + pdied

    # Validate uint64 bounds for AVM encoding
    if result > cst.MAX_UINT64:
        raise ActusNormalizationError(
            f"Initial exchange amount {result} exceeds uint64 maximum ({cst.MAX_UINT64}). "
            f"Notional={notional_display}, "
            f"premium_discount_at_ied={premium_discount_at_ied}"
        )

    return result
