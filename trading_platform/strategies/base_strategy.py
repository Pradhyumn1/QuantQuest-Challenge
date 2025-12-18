"""
Base Strategy - Abstract interface for all trading strategies
"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
import pandas as pd
from typing import Optional


class Signal(Enum):
    """Trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"  # Close existing position


@dataclass
class TradeSignal:
    """Complete trade signal with metadata"""
    signal: Signal
    symbol: str
    price: float
    timestamp: pd.Timestamp
    strength: float = 1.0  # Signal strength (0-1)
    reason: str = ""  # Why this signal was generated


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    All strategies must implement generate_signal method.
    """
    
    def __init__(self, name: str):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name for identification
        """
        self.name = name
        self.positions = {}  # Track current positions per symbol
    
    @abstractmethod
    def generate_signal(self, 
                       data: pd.DataFrame, 
                       symbol: str,
                       current_position: Optional[int] = None) -> TradeSignal:
        """
        Generate trading signal based on market data.
        
        Args:
            data: Historical price data (OHLCV)
            symbol: Asset symbol
            current_position: Current position size (positive=long, negative=short, 0/None=flat)
            
        Returns:
            TradeSignal with action and metadata
        """
        pass
    
    def calculate_position_size(self, 
                               capital: float, 
                               price: float,
                               risk_per_trade: float = 0.02) -> int:
        """
        Calculate position size based on available capital and risk.
        
        Args:
            capital: Available trading capital
            price: Current asset price
            risk_per_trade: Fraction of capital to risk per trade
            
        Returns:
            Number of shares/units to trade
        """
        position_value = capital * risk_per_trade
        shares = int(position_value / price)
        return max(shares, 1)  # At least 1 share
    
    def __str__(self):
        return f"{self.name} Strategy"
