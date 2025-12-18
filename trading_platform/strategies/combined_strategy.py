"""
Combined Strategy - Multi-indicator strategy using RSI + MA + EMA
"""
import pandas as pd
import numpy as np
from typing import Optional
from .base_strategy import BaseStrategy, Signal, TradeSignal
from .rsi_strategy import RSIStrategy
from .ma_crossover import MACrossoverStrategy
from .ema_strategy import EMAStrategy


class CombinedStrategy(BaseStrategy):
    """
    Combined multi-indicator strategy.
    Uses RSI for entry timing and MA/EMA for trend confirmation.
    Only takes trades when multiple indicators align.
    
    Buy conditions:
    - RSI shows oversold (<30)
    - MA/EMA shows bullish trend (short > long)
    
    Sell conditions:
    - RSI shows overbought (>70)
    - MA/EMA shows bearish trend (short < long)
    """
    
    def __init__(self,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30,
                 rsi_overbought: float = 70,
                 ema_short: int = 12,
                 ema_long: int = 26,
                 confirmation_threshold: int = 2):
        """
        Initialize combined strategy.
        
        Args:
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            ema_short: Short EMA period
            ema_long: Long EMA period
            confirmation_threshold: Minimum number of indicators that must agree (2-3)
        """
        super().__init__(name="Combined_RSI_EMA")
        
        # Initialize sub-strategies
        self.rsi = RSIStrategy(
            period=rsi_period,
            oversold=rsi_oversold,
            overbought=rsi_overbought
        )
        self.ema = EMAStrategy(
            short_period=ema_short,
            long_period=ema_long
        )
        
        self.confirmation_threshold = confirmation_threshold
    
    def generate_signal(self,
                       data: pd.DataFrame,
                       symbol: str,
                       current_position: Optional[int] = None) -> TradeSignal:
        """
        Generate trading signal based on combined indicators.
        
        Args:
            data: Historical price data
            symbol: Asset symbol
            current_position: Current position size
            
        Returns:
            TradeSignal based on multi-indicator consensus
        """
        if len(data) < max(self.rsi.period, self.ema.long_period) + 1:
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=data['close'].iloc[-1],
                timestamp=data['timestamp'].iloc[-1],
                reason="Insufficient data for combined strategy"
            )
        
        # Get signals from each strategy
        rsi_signal = self.rsi.generate_signal(data, symbol, current_position)
        ema_signal = self.ema.generate_signal(data, symbol, current_position)
        
        current_price = data['close'].iloc[-1]
        current_time = data['timestamp'].iloc[-1]
        
        # Calculate RSI and EMA values for analysis
        rsi_values = self.rsi.calculate_rsi(data['close'], self.rsi.period)
        current_rsi = rsi_values.iloc[-1]
        
        short_ema = self.ema.calculate_ema(data['close'], self.ema.short_period)
        long_ema = self.ema.calculate_ema(data['close'], self.ema.long_period)
        
        current_short_ema = short_ema.iloc[-1]
        current_long_ema = long_ema.iloc[-1]
        
        # Check for NaN
        if pd.isna(current_rsi) or pd.isna(current_short_ema) or pd.isna(current_long_ema):
            return TradeSignal(
                signal=Signal.HOLD,
                symbol=symbol,
                price=current_price,
                timestamp=current_time,
                reason="Indicator calculation returned NaN"
            )
        
        # Determine trend from EMA
        bullish_trend = current_short_ema > current_long_ema
        bearish_trend = current_short_ema < current_long_ema
        
        # Count bullish and bearish votes
        bullish_votes = 0
        bearish_votes = 0
        reasons = []
        
        # RSI vote
        if rsi_signal.signal == Signal.BUY:
            bullish_votes += 1
            reasons.append(f"RSI oversold ({current_rsi:.1f})")
        elif rsi_signal.signal == Signal.SELL:
            bearish_votes += 1
            reasons.append(f"RSI overbought ({current_rsi:.1f})")
        
        # EMA trend vote
        if bullish_trend:
            bullish_votes += 1
            reasons.append(f"EMA bullish trend")
        elif bearish_trend:
            bearish_votes += 1
            reasons.append(f"EMA bearish trend")
        
        # EMA crossover vote (stronger signal)
        if ema_signal.signal == Signal.BUY:
            bullish_votes += 1
            reasons.append(f"EMA bullish crossover")
        elif ema_signal.signal == Signal.SELL:
            bearish_votes += 1
            reasons.append(f"EMA bearish crossover")
        
        # Generate combined signal
        if current_position is None or current_position == 0:
            # No position - look for strong entry signal
            if bullish_votes >= self.confirmation_threshold:
                strength = bullish_votes / 3.0  # Max 3 votes
                return TradeSignal(
                    signal=Signal.BUY,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=strength,
                    reason=f"Buy confirmed by {bullish_votes}/3 indicators: " + ", ".join(reasons)
                )
            elif bearish_votes >= self.confirmation_threshold:
                strength = bearish_votes / 3.0
                return TradeSignal(
                    signal=Signal.SELL,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    strength=strength,
                    reason=f"Sell confirmed by {bearish_votes}/3 indicators: " + ", ".join(reasons)
                )
        
        elif current_position > 0:
            # Long position - exit if indicators turn bearish
            if bearish_votes >= 2 or rsi_signal.signal == Signal.CLOSE:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit long: {bearish_votes} bearish signals"
                )
        
        elif current_position < 0:
            # Short position - exit if indicators turn bullish
            if bullish_votes >= 2 or rsi_signal.signal == Signal.CLOSE:
                return TradeSignal(
                    signal=Signal.CLOSE,
                    symbol=symbol,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"Exit short: {bullish_votes} bullish signals"
                )
        
        # Default: hold
        return TradeSignal(
            signal=Signal.HOLD,
            symbol=symbol,
            price=current_price,
            timestamp=current_time,
            reason=f"Insufficient confirmation (bull:{bullish_votes}, bear:{bearish_votes})"
        )

