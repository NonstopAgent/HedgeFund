"""Broker adapter protocol and shared types."""

from typing import List, Protocol

from octane_capital.models import (
    AccountSnapshot,
    PositionSnapshot,
    OrderRequest,
    OrderPreview,
    TradeResult,
)


class BrokerAdapter(Protocol):
    def get_account(self) -> AccountSnapshot: ...
    def get_positions(self) -> List[PositionSnapshot]: ...
    def preview_order(self, order: OrderRequest) -> OrderPreview: ...
    def place_order(self, order: OrderRequest) -> TradeResult: ...
