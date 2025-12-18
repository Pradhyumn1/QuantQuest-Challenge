"""
RSI Strategy - Mean reversion using Relative Strength Index
"""
import pandas as pd
import numpy as np
from typing import Optional
from .base_strategy import BaseStrategy, Signal, TradeSignal


class RSIStrategy(BaseStrategy):
    """
    RSI-based mean reversion strategy.
    - Buy when RSI < oversold threshold (default 30)
    - Sell when RSI > overbought threshold (default 70)
    - Close positions when RSI returns to neutral (50)
    """
    
    def __init__(self, 
                 period: int = 14,
                 oversold: float = 30,
                 overbought: float = 70,
                 neutral: float = 50):
        """
        Initialize RSI strategy.
        
        Args:
            period: RSI calculation period
            oversold: Oversold threshold (buy signal)
            overbought: Overbought threshold (sell signal)
            neutral: Neutral level for exits
        """
        super().__init__(name="RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.neutral = neutral
    
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate RSI indicator.
        
        Args:
            prices: Series of closing prices
            period: Lookback period
            
        Returns:
            Series of RSI values
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period, min_periods=period).mean()
        avg_losses = losses.rolling(window=period, min_periods=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self,
                       data: pd.DataFrame,
                       symbol: str,
                       current_position: Optional[int] = None) -> TradeSignal:
        """
        Generate trading signal based on RSI.
        
        Args:
            data: Historical price data with 'close' column
            symbol: Asset symbol
            current_position: Current position size
            
        Returns:
            TradeSignal with buy/sell/hold/close action
        """
        if len(data) < self.period + 1:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=data['close'].iloc[-1],
                timestamp=data['timestamp'].iloc[-1],
                reason="Insufficient data for RSI calculation"
            )
        
        # Calculate RSI
        rsi = self.calculate_rsi(data['close'], self.period)
        current_rsi = rsi.iloc[-1]
        current_price = data['close'].iloc[-1]
        current_time = data['timestamp'].iloc[-1]
        
        # Check for NaN
        if pd.isna(current_rsi):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=current_price,
                timestamp=current_time,
                reason="RSI calculation returned NaN"
            )
        
        # Generate signals based on RSI levels
        if current_position is None or current_position == 0:
            # No position - look for entry
            if current_rsi < self.oversold:
                return TradeSignal(
                    signal=Signal.BUY,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=(self.oversold - current_rsi) / self.oversold,
                    reason=f"RSI oversold: {current_rsi:.2f} < {self.oversold}"
                )
            elif current_rsi > self.overbought:
                return TradeSignal(
                    signal=Signal.SELL,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=(current_rsi - self.overbought) / (100 - self.overbought),
                    reason=f"RSI overbought: {current_rsi:.2f} > {self.overbought}"
                )
        
        elif current_position > 0:
            # Long position - look for exit
            if current_rsi > self.neutral or current_rsi > self.overbought:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"RSI exit long: {current_rsi:.2f}"
                )
        
        elif current_position < 0:
            # Short position - look for exit
            if current_rsi < self.neutral or current_rsi < self.oversold:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"RSI exit short: {current_rsi:.2f}"
                )
        
        # Default: hold
        return TradeSignal(
            signal=Signal.HOLD,
            symbol=symbol,
            price=current_price,
            timestamp=current_time,
            reason=f"RSI neutral: {current_rsi:.2f}"
        )

