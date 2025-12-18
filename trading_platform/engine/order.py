"""
Order - Data structures for trading orders
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(Enum):
    """Order side (direction)"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """
    Represents a trading order.
    """
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    timestamp: datetime
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    fill_price: Optional[float] = None
    fill_timestamp: Optional[datetime] = None
    order_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate order ID if not provided"""
        if self.order_id is None:
            # Simple ID: timestamp + symbol + side
            ts = self.timestamp.strftime("%Y%m%d%H%M%S%f")
            self.order_id = f"{ts}_{self.symbol}_{self.side.value}"
    
    def fill(self, price: float, timestamp: datetime):
        """
        Mark order as filled.
        
        Args:
            price: Execution price
            timestamp: Execution timestamp
        """
        self.fill_price = price
        self.fill_timestamp = timestamp
        self.status = OrderStatus.FILLED
    
    def cancel(self):
        """Mark order as cancelled"""
        self.status = OrderStatus.CANCELLED
    
    def reject(self):
        """Mark order as rejected"""
        self.status = OrderStatus.REJECTED
    
    def __str__(self):
        status_str = f"[{self.status.value}]"
        if self.status == OrderStatus.FILLED:
            return f"{status_str} {self.side.value} {self.quantity} {self.symbol} @ ${self.fill_price:.2f}"
        else:
            price_str = f"${self.limit_price:.2f}" if self.limit_price else "MARKET"
            return f"{status_str} {self.side.value} {self.quantity} {self.symbol} @ {price_str}"

