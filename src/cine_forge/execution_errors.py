"""Typed incurred-cost evidence retained when module execution fails."""

from cine_forge.schemas.media_cost import CostReceipt


class ModuleCostError(RuntimeError):
    """A failed module whose already incurred calls must still be accounted."""

    def __init__(self, message: str, *, cost_receipts: list[CostReceipt]) -> None:
        super().__init__(message)
        self.cost_receipts = list(cost_receipts)
