"""
Unified Market Configuration for Indian and International Markets
"""

INDIAN_LOT_SIZES_DEC_2025 = {
    'NIFTY50': 75, 'NIFTY': 75, 'BANKNIFTY': 35, 'FINNIFTY': 65,
    'SENSEX': 20, 'MIDCPNIFTY': 140, 'NIFTYNXT50': 25,
}

INDIAN_LOT_SIZES_JAN_2026 = {
    'NIFTY50': 65, 'NIFTY': 65, 'BANKNIFTY': 30, 
    'FINNIFTY': 60, 'SENSEX': 20, 'MIDCPNIFTY': 120,
}

INDIAN_STOCK_LOT_SIZES = {
    'RELIANCE': 500, 'TCS': 150, 'INFY': 300, 'HDFCBANK': 550,
    'ICICIBANK': 700, 'SBIN': 1500, 'BHARTIARTL': 475, 'ITC': 1600,
}

INDIAN_MARGIN_REQUIREMENTS = {
    'NIFTY': 0.14, 'NIFTY50': 0.14, 'BANKNIFTY': 0.18,
    'FINNIFTY': 0.16, 'SENSEX': 0.14,
}

INDIAN_CHARGES = {
    'STT_FUTURES_SELL_PCT': 0.0002,
    'TRANSACTION_CHARGES_NSE': 0.0000173,
    'SEBI_TURNOVER_FEES': 0.000001,
    'STAMP_DUTY_FUTURES': 0.00002,
    'GST_RATE': 0.18,
}

US_STOCKS = {
    'AAPL': 'Apple Inc.', 'GOOGL': 'Alphabet Inc.',
    'MSFT': 'Microsoft Corporation', 'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.', 'META': 'Meta Platforms Inc.',
    'NVDA': 'NVIDIA Corporation', 'JPM': 'JPMorgan Chase & Co.',
}

US_INDICES = {
    'SPY': 'S&P 500 ETF', 'QQQ': 'NASDAQ-100 ETF',
    'DIA': 'Dow Jones Industrial Average ETF', 'IWM': 'Russell 2000 ETF',
}

EU_STOCKS = {
    'SAP': 'SAP SE', 'ASML': 'ASML Holding N.V.',
    'NESN': 'Nestlé S.A.', 'NOVN': 'Novartis AG',
}

INTERNATIONAL_MARGIN_REQUIREMENTS = {
    'DEFAULT': 0.25, 'ETF': 0.25, 'INDEX': 0.15,
}

INTERNATIONAL_CHARGES = {
    'SEC_FEE': 0.0000278,
    'FINRA_TAF': 0.000166,
    'COMMISSION_PCT': 0.001,
}


class MarketType:
    INDIAN = 'INDIAN'
    INTERNATIONAL = 'INTERNATIONAL'


INDIAN_SYMBOLS = {
    'indices': ['NIFTY50', 'SENSEX', 'BANKNIFTY', 'FINNIFTY'],
    'stocks': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'],
}

INTERNATIONAL_SYMBOLS = {
    'us_indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
    'us_stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA'],
    'eu_stocks': ['SAP', 'ASML', 'NESN', 'NOVN'],
}


def get_market_type(symbol: str) -> str:
    symbol = symbol.upper()
    if symbol in INDIAN_LOT_SIZES_DEC_2025 or symbol in INDIAN_STOCK_LOT_SIZES:
        return MarketType.INDIAN
    if symbol in US_STOCKS or symbol in US_INDICES or symbol in EU_STOCKS:
        return MarketType.INTERNATIONAL
    return MarketType.INTERNATIONAL


def get_lot_size(symbol: str, expiry_month: str = 'DEC') -> int:
    market_type = get_market_type(symbol)
    symbol = symbol.upper()
    
    if market_type == MarketType.INDIAN:
        if expiry_month.upper() == 'JAN':
            return INDIAN_LOT_SIZES_JAN_2026.get(
                symbol, INDIAN_STOCK_LOT_SIZES.get(symbol, 1))
        return INDIAN_LOT_SIZES_DEC_2025.get(
            symbol, INDIAN_STOCK_LOT_SIZES.get(symbol, 1))
    return 1


def get_currency_symbol(symbol: str) -> str:
    return '₹' if get_market_type(symbol) == MarketType.INDIAN else '$'


def get_margin_requirement(symbol: str) -> float:
    market_type = get_market_type(symbol)
    symbol = symbol.upper()
    
    if market_type == MarketType.INDIAN:
        return INDIAN_MARGIN_REQUIREMENTS.get(symbol, 0.20)
    return INTERNATIONAL_MARGIN_REQUIREMENTS['ETF'] if symbol in US_INDICES else INTERNATIONAL_MARGIN_REQUIREMENTS['DEFAULT']


def calculate_trading_fees(value: float, symbol: str, side: str = 'BUY') -> float:
    market_type = get_market_type(symbol)
    
    if market_type == MarketType.INDIAN:
        charges = INDIAN_CHARGES
        stt = value * charges['STT_FUTURES_SELL_PCT'] if side.upper() == 'SELL' else 0
        stamp = value * charges['STAMP_DUTY_FUTURES'] if side.upper() == 'BUY' else 0
        txn = value * charges['TRANSACTION_CHARGES_NSE']
        sebi = value * charges['SEBI_TURNOVER_FEES']
        gst = (txn + sebi) * charges['GST_RATE']
        return stt + stamp + txn + sebi + gst
    
    charges = INTERNATIONAL_CHARGES
    return value * charges['SEC_FEE'] + value * charges['COMMISSION_PCT']


def get_all_symbols_by_category():
    return {
        'Indian Indices': INDIAN_SYMBOLS['indices'],
        'Indian Stocks': INDIAN_SYMBOLS['stocks'],
        'US Indices': INTERNATIONAL_SYMBOLS['us_indices'],
        'US Stocks': INTERNATIONAL_SYMBOLS['us_stocks'],
        'EU Stocks': INTERNATIONAL_SYMBOLS['eu_stocks'],
    }


def get_symbol_info(symbol: str) -> dict:
    market_type = get_market_type(symbol)
    description = US_STOCKS.get(symbol) or US_INDICES.get(symbol) or EU_STOCKS.get(symbol)
    
    return {
        'symbol': symbol,
        'market_type': market_type,
        'lot_size': get_lot_size(symbol),
        'currency': get_currency_symbol(symbol),
        'margin_requirement': get_margin_requirement(symbol),
        'description': description,
    }

