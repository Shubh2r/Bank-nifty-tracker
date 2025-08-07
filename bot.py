import datetime
import yfinance as yf

# Parameters
budget_per_share = 600
max_days_to_expiry = 7
symbol = "^NSEBANK"  # Bank Nifty Index

# Fetch Bank Nifty data
data = yf.download(symbol, period="7d", interval="1h")

if data.empty:
    raise ValueError("No data received for Bank Nifty. Check symbol or internet access.")

trend = "Bullish" if data["Close"].iloc[-1] > data["Open"].iloc[0] else "Bearish"
entry_price = round(data["Close"].iloc[-1], 2)

# Simple analysis: trend direction
trend = "Bullish" if data["Close"].iloc[-1] > data["Open"].iloc[0] else "Bearish"

# Generate a mock recommendation
entry_price = round(data["Close"].iloc[-1], 2)
target1 = round(entry_price * 1.02, 2)
target2 = round(entry_price * 1.04, 2)
target3 = round(entry_price * 1.06, 2)
stop_loss = round(entry_price * 0.98, 2)
risk_level = "Low Risk" if trend == "Bullish" else "High Risk"

# Save to Markdown
report = f"""
# 📈 Bank Nifty Trading Call

**Trend:** {trend}  
**Entry Price:** ₹{entry_price}  
**Targets:**  
- 🎯 Target 1: ₹{target1}  
- 🎯 Target 2: ₹{target2}  
- 🎯 Target 3: ₹{target3}  
**Stop Loss:** ₹{stop_loss}  
**Risk Level:** {risk_level}  

_Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""

with open("report.md", "w") as f:
    f.write(report)
