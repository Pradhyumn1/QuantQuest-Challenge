"""
EMA Strategy - Exponential Moving Average crossover for faster trend detection
"""
import pandas as pd
import numpy as np
from typing import Optional
from .base_strategy import BaseStrategy, Signal, TradeSignal


class EMAStrategy(BaseStrategy):
    """
    Exponential Moving Average (EMA) crossover strategy.
    Similar to MA crossover but more responsive to recent prices.
    - Buy when short EMA crosses above long EMA
    - Sell when short EMA crosses below long EMA
    """
    
    def __init__(self,
                 short_period: int = 12,
                 long_period: int = 26):
        """
        Initialize EMA strategy.
        
        Args:
            short_period: Short EMA period (default: 12)
            long_period: Long EMA period (default: 26)
        """
        super().__init__(name="EMA_Crossover")
        self.short_period = short_period
        self.long_period = long_period
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Series of prices
            period: EMA period
            
        Returns:
            Series of EMA values
        """
        return prices.ewm(span=period, adjust=False, min_periods=period).mean()
    
    def generate_signal(self,
                       data: pd.DataFrame,
                       symbol: str,
                       current_position: Optional[int] = None) -> TradeSignal:
        """
        Generate trading signal based on EMA crossover.
        
        Args:
            data: Historical price data with 'close' column
            symbol: Asset symbol
            current_position: Current position size
            
        Returns:
            TradeSignal with buy/sell/hold/close action
        """
        if len(data) < self.long_period + 1:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=data['close'].iloc[-1],
                timestamp=data['timestamp'].iloc[-1],
                reason="Insufficient data for EMA calculation"
            )
        
        # Calculate EMAs
        short_ema = self.calculate_ema(data['close'], self.short_period)
        long_ema = self.calculate_ema(data['close'], self.long_period)
        
        # Get current and previous values
        current_short = short_ema.iloc[-1]
        current_long = long_ema.iloc[-1]
        prev_short = short_ema.iloc[-2]
        prev_long = long_ema.iloc[-2]
        
        current_price = data['close'].iloc[-1]
        current_time = data['timestamp'].iloc[-1]
        
        # Check for NaN
        if pd.isna(current_short) or pd.isna(current_long):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=current_price,
                timestamp=current_time,
                reason="EMA calculation returned NaN"
            )
        
        # Detect crossovers
        bullish_crossover = (prev_short <= prev_long) and (current_short > current_long)
        bearish_crossover = (prev_short >= prev_long) and (current_short < current_long)
        
        # Current trend
        bullish_trend = current_short > current_long
        bearish_trend = current_short < current_long
        
        # Calculate signal strength based on EMA separation
        separation = abs(current_short - current_long) / current_long
        
        # Generate signals
        if current_position is None or current_position == 0:
            # No position - look for entry
            if bullish_crossover:
                return TradeSignal(
                    signal=Signal.BUY,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=min(separation * 10, 1.0),  # Scale strength
                    reason=f"Bullish EMA crossover: EMA{self.short_period} > EMA{self.long_period}"
                )
            elif bearish_crossover:
                return TradeSignal(
                    signal=Signal.SELL,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=min(separation * 10, 1.0),
                    reason=f"Bearish EMA crossover: EMA{self.short_period} < EMA{self.long_period}"
                )
        
        elif current_position > 0:
            # Long position - exit on bearish crossover
            if bearish_crossover:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit long: Bearish EMA crossover"
                )
        
        elif current_position < 0:
            # Short position - exit on bullish crossover
            if bullish_crossover:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit short: Bullish EMA crossover"
                )
        
        # Default: hold current position
        trend_desc = "bullish" if bullish_trend else "bearish"
        return TradeSignal(
            signal=Signal.HOLD,
            symbol=symbol,
            price=current_price,
            timestamp=current_time,
            reason=f"No crossover, trend: {trend_desc} (sep: {separation:.4f})"
        )

