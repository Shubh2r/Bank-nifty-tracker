import yfinance as yf
from nsepython import *
import datetime

def get_index_change(ticker):
    data = yf.download(ticker, period="2d")
    if data.empty:
        return "N/A", "N/A"
    change = round(data["Close"].iloc[-1] - data["Close"].iloc[-2], 2)
    percent = round((change / data["Close"].iloc[-2]) * 100, 2)
    return change, percent

def get_global_sentiment():
    dow, dow_pct = get_index_change("^DJI")
    nasdaq, nasdaq_pct = get_index_change("^IXIC")
    sp500, sp500_pct = get_index_change("^GSPC")
    sgx, sgx_pct = get_index_change("^NSEI")

    sentiment_score = sum([
        float(dow_pct) if dow_pct != "N/A" else 0,
        float(nasdaq_pct) if nasdaq_pct != "N/A" else 0,
        float(sp500_pct) if sp500_pct != "N/A" else 0,
        float(sgx_pct) if sgx_pct != "N/A" else 0
    ])

    print("🌐 Global Indices Sentiment")
    print(f"📊 Dow: {dow_pct}%")
    print(f"📊 Nasdaq: {nasdaq_pct}%")
    print(f"📊 S&P 500: {sp500_pct}%")
    print(f"📊 SGX Nifty: {sgx_pct}%")
    print(f"🧭 Sentiment Score: {sentiment_score}")
    return sentiment_score

def analyze_banknifty():
    chain = nse_optionchain_scrapper("BANKNIFTY")
    pcr = round(chain["records"]["underlyingValue"] / 1000, 2)
    expiry_list = chain["records"]["expiryDates"]
    today = datetime.date.today()

    # Filter nearest expiry that's at least 3 days away
    valid_expiry = next((e for e in expiry_list if (datetime.datetime.strptime(e, "%d-%b-%Y").date() - today).days >= 3), expiry_list[0])
    strikes = chain["records"]["data"]

    # Find top PE strike by open interest
    top_pe = max(strikes, key=lambda x: x.get("PE", {}).get("openInterest", 0))
    strike_price = top_pe["strikePrice"]

    entry = 628.4
    target = round(entry * 1.5, 2)
    stop_loss = round(entry * 0.7, 2)

    print("\n📘 BANKNIFTY Option Chain Analysis")
    print(f"📈 PCR: {pcr}")
    print(f"🔢 Top PE Strike: {strike_price}")
    print(f"📆 Expiry: {valid_expiry}")
    print(f"🎫 Symbol: OPTIDXBANKNIFTY{valid_expiry.replace('-', '')}PE{strike_price}.00")
    print(f"💰 Entry: ₹{entry}")
    print(f"🎯 Target: ₹{target}")
    print(f"⛔ Stop-Loss: ₹{stop_loss}")
    return pcr, strike_price, valid_expiry

def generate_trade_signal(pcr, sentiment_score):
    print("\n📍 Trade Signal")
    if sentiment_score < 0 and pcr > 1:
        print("✅ Signal: PUT Option — Bearish Bias")
    elif sentiment_score > 0 and pcr < 1:
        print("✅ Signal: CALL Option — Bullish Bias")
    else:
        print("⚠️ Signal: Neutral — Wait for confirmation")

def main():
    print(f"# 📅 Report - {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}\n")
    sentiment_score = get_global_sentiment()
    pcr, strike_price, expiry = analyze_banknifty()
    generate_trade_signal(pcr, sentiment_score)

if __name__ == "__main__":
    main()
