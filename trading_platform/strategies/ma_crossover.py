"""
Moving Average Crossover Strategy - Trend following using MA crossovers
"""
import pandas as pd
import numpy as np
from typing import Optional
from .base_strategy import BaseStrategy, Signal, TradeSignal


class MACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average (SMA) crossover strategy.
    - Buy when short MA crosses above long MA (golden cross)
    - Sell when short MA crosses below long MA (death cross)
    """
    
    def __init__(self,
                 short_period: int = 20,
                 long_period: int = 50):
        """
        Initialize MA Crossover strategy.
        
        Args:
            short_period: Short moving average period
            long_period: Long moving average period
        """
        super().__init__(name="MA_Crossover")
        self.short_period = short_period
        self.long_period = long_period
    
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Series of prices
            period: MA period
            
        Returns:
            Series of MA values
        """
        return prices.rolling(window=period, min_periods=period).mean()
    
    def generate_signal(self,
                       data: pd.DataFrame,
                       symbol: str,
                       current_position: Optional[int] = None) -> TradeSignal:
        """
        Generate trading signal based on MA crossover.
        
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
                reason="Insufficient data for MA calculation"
            )
        
        # Calculate MAs
        short_ma = self.calculate_ma(data['close'], self.short_period)
        long_ma = self.calculate_ma(data['close'], self.long_period)
        
        # Get current and previous values
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        current_price = data['close'].iloc[-1]
        current_time = data['timestamp'].iloc[-1]
        
        # Check for NaN
        if pd.isna(current_short) or pd.isna(current_long):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=current_price,
                timestamp=current_time,
                reason="MA calculation returned NaN"
            )
        
        # Detect crossovers
        golden_cross = (prev_short <= prev_long) and (current_short > current_long)
        death_cross = (prev_short >= prev_long) and (current_short < current_long)
        
        # Current trend
        bullish_trend = current_short > current_long
        bearish_trend = current_short < current_long
        
        # Generate signals
        if current_position is None or current_position == 0:
            # No position - look for entry
            if golden_cross:
                return TradeSignal(
                    signal=Signal.BUY,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=abs(current_short - current_long) / current_long,
                    reason=f"Golden cross: MA{self.short_period} crossed above MA{self.long_period}"
                )
            elif death_cross:
                return TradeSignal(
                    signal=Signal.SELL,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=abs(current_short - current_long) / current_long,
                    reason=f"Death cross: MA{self.short_period} crossed below MA{self.long_period}"
                )
        
        elif current_position > 0:
            # Long position - exit on death cross
            if death_cross:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit long: Death cross detected"
                )
        
        elif current_position < 0:
            # Short position - exit on golden cross
            if golden_cross:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit short: Golden cross detected"
                )
        
        # Default: hold current position
        trend_desc = "bullish" if bullish_trend else "bearish"
        return TradeSignal(
            signal=Signal.HOLD,
            symbol=symbol,
            price=current_price,
            timestamp=current_time,
            reason=f"No crossover, trend: {trend_desc}"
        )

