import yfinance as yf
from nsepython import *
import datetime
import csv
import pandas as pd
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# 🎯 Budget filter
def filter_by_budget(strike_data, option_type, budget_min=500, budget_max=600):
    oi_data = strike_data.get(option_type)
    if not oi_data:
        return False
    ltp = oi_data.get("lastPrice", 0)
    return budget_min <= ltp <= budget_max

# 🧠 Confidence score calculator
def calculate_confidence(sentiment_score, pcr, oi, premium):
    score = 0
    if abs(sentiment_score) > 1:
        score += 30
    if pcr < 0.9 or pcr > 1.1:
        score += 30
    if oi > 100000:
        score += 20
    if 500 <= premium <= 600:
        score += 20
    return score

# 📊 Weekly trade logger
def log_trade(symbol, entry, target, stop_loss, confidence):
    with open("weekly_trades.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.datetime.now().strftime("%d-%b-%Y"),
            symbol, entry, target, stop_loss, confidence
        ])

# 📅 Weekly summary
def weekly_summary():
    try:
        df = pd.read_csv("weekly_trades.csv", header=None)
        df.columns = ["Date", "Symbol", "Entry", "Target", "StopLoss", "Confidence"]
        avg_conf = df["Confidence"].mean()
        high_conf_trades = df[df["Confidence"] >= 80]
        print("\n📅 Weekly Summary")
        print(f"📈 Total Trades: {len(df)}")
        print(f"🧠 Avg Confidence: {round(avg_conf, 2)}")
        print(f"✅ High Confidence Trades: {len(high_conf_trades)}")
    except FileNotFoundError:
        print("\n📅 Weekly Summary: No trades logged yet.")

# 🌐 Global sentiment
def get_index_change(ticker):
    data = yf.download(ticker, period="2d", progress=False)
    if data.empty or len(data) < 2:
        return 0.0
    close_yesterday = data["Close"].iloc[-2]
    close_today = data["Close"].iloc[-1]
    change = round(close_today - close_yesterday, 2)
    percent = round((change / close_yesterday) * 100, 2)
    return percent

def get_global_sentiment():
    dow_pct = get_index_change("^DJI")
    nasdaq_pct = get_index_change("^IXIC")
    sp500_pct = get_index_change("^GSPC")
    sgx_pct = get_index_change("^NSEI")

    sentiment_score = dow_pct + nasdaq_pct + sp500_pct + sgx_pct

    print("🌐 Global Indices Sentiment")
    print(f"📊 Dow: {dow_pct}%")
    print(f"📊 Nasdaq: {nasdaq_pct}%")
    print(f"📊 S&P 500: {sp500_pct}%")
    print(f"📊 SGX Nifty: {sgx_pct}%")
    print(f"🧭 Sentiment Score: {sentiment_score}")
    return sentiment_score

# 📘 BankNifty analysis
def analyze_banknifty():
    chain = nse_optionchain_scrapper("BANKNIFTY")
    underlying = chain["records"].get("underlyingValue", 0)

    try:
        total_put_oi = chain["records"]["totalPutOpenInterest"]
        total_call_oi = chain["records"]["totalCallOpenInterest"]
        pcr = round(total_put_oi / total_call_oi, 2)
    except KeyError:
        print("⚠️ PCR data not available — using fallback value")
        pcr = 1.0  # Neutral fallback

    expiry_list = chain["records"].get("expiryDates", [])
    today = datetime.date.today()

    valid_expiry = next(
        (e for e in expiry_list if (datetime.datetime.strptime(e, "%d-%b-%Y").date() - today).days >= 3),
        expiry_list[0] if expiry_list else "N/A"
    )

    strikes = chain["records"].get("data", [])
    filtered = [s for s in strikes if s.get("CE") and s.get("PE") and s["strikePrice"] > 0]
    budget_ce = [s for s in filtered if filter_by_budget(s, "CE")]
    budget_pe = [s for s in filtered if filter_by_budget(s, "PE")]

    top_ce = max(budget_ce, key=lambda x: x["CE"]["openInterest"]) if budget_ce else None
    top_pe = max(budget_pe, key=lambda x: x["PE"]["openInterest"]) if budget_pe else None

    print("\n📘 BANKNIFTY Option Chain Analysis")
    print(f"📈 PCR: {pcr}")
    print(f"📆 Expiry: {valid_expiry}")
    print(f"💹 Underlying: ₹{underlying}")
    if top_ce:
        print(f"🔢 Top CE Strike: {top_ce['strikePrice']} (OI: {top_ce['CE']['openInterest']}, LTP: ₹{top_ce['CE']['lastPrice']})")
    if top_pe:
        print(f"🔢 Top PE Strike: {top_pe['strikePrice']} (OI: {top_pe['PE']['openInterest']}, LTP: ₹{top_pe['PE']['lastPrice']})")

    return {
        "pcr": pcr,
        "underlying": underlying,
        "expiry": valid_expiry,
        "top_ce": top_ce,
        "top_pe": top_pe
    }

# 📍 Trade signal generator
def generate_trade_signal(data, sentiment_score):
    pcr = data["pcr"]
    expiry = data["expiry"]
    top_ce = data["top_ce"]
    top_pe = data["top_pe"]

    print("\n📍 Trade Signal")

    if sentiment_score > 0 and pcr < 0.9 and top_ce:
        symbol = f"OPTIDXBANKNIFTY{expiry.replace('-', '')}CE{top_ce['strikePrice']}.00"
        entry = top_ce["CE"]["lastPrice"]
        target = round(entry * 1.5, 2)
        stop_loss = round(entry * 0.7, 2)
        confidence = calculate_confidence(sentiment_score, pcr, top_ce["CE"]["openInterest"], entry)
        print(f"✅ CALL Option Selected")
    elif sentiment_score < 0 and pcr > 1.1 and top_pe:
        symbol = f"OPTIDXBANKNIFTY{expiry.replace('-', '')}PE{top_pe['strikePrice']}.00"
        entry = top_pe["PE"]["lastPrice"]
        target = round(entry * 1.5, 2)
        stop_loss = round(entry * 0.7, 2)
        confidence = calculate_confidence(sentiment_score, pcr, top_pe["PE"]["openInterest"], entry)
        print(f"✅ PUT Option Selected")
    else:
        print("⚠️ Signal: Neutral — No clear trend or budget match")
        return

    print(f"🎫 Symbol: {symbol}")
    print(f"💰 Entry: ₹{entry}")
    print(f"🎯 Target: ₹{target}")
    print(f"⛔ Stop-Loss: ₹{stop_loss}")
    print(f"🧠 Confidence Score: {confidence}/100")
    log_trade(symbol, entry, target, stop_loss, confidence)

# 🚀 Main
def main():
    print(f"# 📅 Report - {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}\n")
    sentiment_score = get_global_sentiment()
    banknifty_data = analyze_banknifty()
    generate_trade_signal(banknifty_data, sentiment_score)
    weekly_summary()

if __name__ == "__main__":
    main()
