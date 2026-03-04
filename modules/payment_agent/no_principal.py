from modules.core_financial.common import (
    CoreFinancialCommonMixin,
)


class NoPrincipalPaymentMixin(CoreFinancialCommonMixin):
    """Marker mixin for non-redeemable products (no pay_principal ABI)."""

    pass
