import yfinance as yf

symbol = "^NSEBANK"
data = yf.download(symbol, period="7d", interval="1h")

# Safety check for empty data
if data.empty:
    raise ValueError("No data received for Bank Nifty. Check symbol or internet access.")

# Reset index in case it's a MultiIndex
data = data.reset_index()

# Extract scalar values safely
close_last = float(data["Close"].iloc[-1])
open_first = float(data["Open"].iloc[0])

# Determine trend
trend = "Bullish" if close_last > open_first else "Bearish"
entry_price = round(close_last, 2)

print(f"Trend: {trend}")
print(f"Entry Price: ₹{entry_price}")
