"""
Position - Track trading positions and calculate P&L
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """
    Represents a trading position (long or short).
    """
    symbol: str
    quantity: int  # Positive = long, Negative = short
    entry_price: float
    entry_timestamp: datetime
    leverage: float = 1.0
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized profit/loss.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized P&L in dollars
        """
        price_diff = current_price - self.entry_price
        return price_diff * self.quantity
    
    def calculate_unrealized_pnl_percentage(self, current_price: float) -> float:
        """
        Calculate unrealized P&L as percentage.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized P&L as percentage
        """
        if self.entry_price == 0:
            return 0.0
        
        price_diff = current_price - self.entry_price
        pnl_pct = (price_diff / self.entry_price) * 100
        
        # For short positions, invert the percentage
        if self.quantity < 0:
            pnl_pct = -pnl_pct
        
        # Apply leverage multiplier
        pnl_pct *= self.leverage
        
        return pnl_pct
    
    def get_position_value(self, current_price: float) -> float:
        """
        Get current position value.
        
        Args:
            current_price: Current market price
            
        Returns:
            Position value in dollars
        """
        return abs(self.quantity) * current_price
    
    def get_margin_required(self, current_price: float) -> float:
        """
        Calculate margin required for this position.
        
        Args:
            current_price: Current market price
            
        Returns:
            Margin required in dollars
        """
        position_value = self.get_position_value(current_price)
        # Margin = position value / leverage
        margin = position_value / self.leverage
        return margin
    
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0
    
    def close(self, exit_price: float, exit_timestamp: datetime) -> 'ClosedPosition':
        """
        Close position and create closed position record.
        
        Args:
            exit_price: Exit price
            exit_timestamp: Exit timestamp
            
        Returns:
            ClosedPosition object with P&L details
        """
        realized_pnl = self.calculate_unrealized_pnl(exit_price)
        realized_pnl_pct = self.calculate_unrealized_pnl_percentage(exit_price)
        
        return ClosedPosition(
            symbol=self.symbol,
            quantity=self.quantity,
            entry_price=self.entry_price,
            exit_price=exit_price,
            entry_timestamp=self.entry_timestamp,
            exit_timestamp=exit_timestamp,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct,
            leverage=self.leverage
        )
    
    def __str__(self):
        side = "LONG" if self.is_long() else "SHORT"
        qty = abs(self.quantity)
        leverage_str = f" [{self.leverage}x]" if self.leverage > 1 else ""
        return f"{side} {qty} {self.symbol} @ ${self.entry_price:.2f}{leverage_str}"


@dataclass
class ClosedPosition:
    """
    Represents a closed position with realized P&L.
    """
    symbol: str
    quantity: int
    entry_price: float
    exit_price: float
    entry_timestamp: datetime
    exit_timestamp: datetime
    realized_pnl: float
    realized_pnl_pct: float
    leverage: float = 1.0
    
    def get_hold_duration(self) -> float:
        """
        Calculate holding duration in seconds.
        
        Returns:
            Duration in seconds
        """
        duration = self.exit_timestamp - self.entry_timestamp
        return duration.total_seconds()
    
    def is_profitable(self) -> bool:
        """Check if trade was profitable"""
        return self.realized_pnl > 0
    
    def __str__(self):
        side = "LONG" if self.quantity > 0 else "SHORT"
        qty = abs(self.quantity)
        pnl_sign = "+" if self.realized_pnl >= 0 else ""
        duration = self.get_hold_duration()
        
        return (f"{side} {qty} {self.symbol}: "
                f"${self.entry_price:.2f} -> ${self.exit_price:.2f} | "
                f"P&L: {pnl_sign}${self.realized_pnl:.2f} ({pnl_sign}{self.realized_pnl_pct:.2f}%) | "
                f"Duration: {duration:.0f}s")

