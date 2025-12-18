"""Stochastic Oscillator Strategy for Sideways Markets"""

import numpy as np
import pandas as pd
from .base_strategy import BaseStrategy, Signal, TradeSignal


class StochasticStrategy(BaseStrategy):
    
    def __init__(self, k_period=14, d_period=3, oversold=20, overbought=80):
        super().__init__("Stochastic_Oscillator")
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, data: pd.DataFrame, symbol: str, current_position: float):
        if len(data) < self.k_period + self.d_period:
            return TradeSignal(Signal.HOLD, symbol, data['close'].iloc[-1], 
                             data['timestamp'].iloc[-1], 0, "Insufficient data")
        
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        k_values = []
        for i in range(len(data) - self.k_period + 1):
            window_high = highs[i:i + self.k_period]
            window_low = lows[i:i + self.k_period]
            close_price = closes[i + self.k_period - 1]
            
            highest = np.max(window_high)
            lowest = np.min(window_low)
            
            if highest == lowest:
                k_values.append(50.0)
            else:
                k = 100 * (close_price - lowest) / (highest - lowest)
                k_values.append(k)
        
        if len(k_values) < self.d_period:
            return TradeSignal(Signal.HOLD, symbol, data['close'].iloc[-1],
                             data['timestamp'].iloc[-1], 0, "Insufficient K values")
        
        d_values = pd.Series(k_values).rolling(self.d_period).mean().values
        
        current_k = k_values[-1]
        current_d = d_values[-1]
        prev_k = k_values[-2] if len(k_values) > 1 else current_k
        prev_d = d_values[-2] if len(d_values) > 1 else current_d
        
        if np.isnan(current_d) or np.isnan(prev_d):
            return TradeSignal(Signal.HOLD, symbol, data['close'].iloc[-1],
                             data['timestamp'].iloc[-1], 0, "Invalid D values")
        
        current_price = data['close'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]
        
        if current_position == 0:
            if current_k < self.oversold and prev_k < prev_d and current_k > current_d:
                return TradeSignal(Signal.BUY, symbol, current_price, timestamp, 1.0,
                    f"Stochastic oversold crossover: K={current_k:.1f}, D={current_d:.1f}")
            
            if current_k > self.overbought and prev_k > prev_d and current_k < current_d:
                return TradeSignal(Signal.SELL, symbol, current_price, timestamp, 1.0,
                    f"Stochastic overbought crossover: K={current_k:.1f}, D={current_d:.1f}")
        
        elif current_position > 0:
            if current_k > 60 or (current_k < current_d and current_k > self.oversold):
                return TradeSignal(Signal.CLOSE, symbol, current_price, timestamp, 1.0,
                    f"Exit long: K={current_k:.1f}, D={current_d:.1f}")
        
        elif current_position < 0:
            if current_k < 40 or (current_k > current_d and current_k < self.overbought):
                return TradeSignal(Signal.CLOSE, symbol, current_price, timestamp, 1.0,
                    f"Exit short: K={current_k:.1f}, D={current_d:.1f}")
        
        return TradeSignal(Signal.HOLD, symbol, current_price, timestamp, 0,
            f"Stochastic neutral: K={current_k:.1f}, D={current_d:.1f}")
