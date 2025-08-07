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
    underlying = chain["records"]["underlyingValue"]
    pcr = round(chain["records"]["totalPutOpenInterest"] / chain["records"]["totalCallOpenInterest"], 2)
    expiry_list = chain["records"]["expiryDates"]
    today = datetime.date.today()

    # Filter nearest expiry that's at least 3 days away
    valid_expiry = next((e for e in expiry_list if (datetime.datetime.strptime(e, "%d-%b-%Y").date() - today).days >= 3), expiry_list[0])
    strikes = chain["records"]["data"]

    # Filter strikes with decent OI
    filtered = [s for s in strikes if s.get("CE") and s.get("PE") and s["strikePrice"] > 0]
    top_ce = max(filtered, key=lambda x: x["CE"]["openInterest"])
    top_pe = max(filtered, key=lambda x: x["PE"]["openInterest"])

    print("\n📘 BANKNIFTY Option Chain Analysis")
    print(f"📈 PCR: {pcr}")
    print(f"📆 Expiry: {valid_expiry}")
    print(f"💹 Underlying: ₹{underlying}")
    print(f"🔢 Top CE Strike: {top_ce['strikePrice']} (OI: {top_ce['CE']['openInterest']})")
    print(f"🔢 Top PE Strike: {top_pe['strikePrice']} (OI: {top_pe['PE']['openInterest']})")

    return {
        "pcr": pcr,
        "underlying": underlying,
        "expiry": valid_expiry,
        "top_ce": top_ce,
        "top_pe": top_pe
    }

def generate_trade_signal(data, sentiment_score):
    pcr = data["pcr"]
    ce_strike = data["top_ce"]["strikePrice"]
    pe_strike = data["top_pe"]["strikePrice"]
    expiry = data["expiry"]

    print("\n📍 Trade Signal")

    # Filter logic
    if sentiment_score > 0 and pcr < 0.9:
        symbol = f"OPTIDXBANKNIFTY{expiry.replace('-', '')}CE{ce_strike}.00"
        entry = 628.4
        target = round(entry * 1.5, 2)
        stop_loss = round(entry * 0.7, 2)
        print(f"✅ CALL Option Selected")
    elif sentiment_score < 0 and pcr > 1.1:
        symbol = f"OPTIDXBANKNIFTY{expiry.replace('-', '')}PE{pe_strike}.00"
        entry = 628.4
        target = round(entry * 1.5, 2)
        stop_loss = round(entry * 0.7, 2)
        print(f"✅ PUT Option Selected")
    else:
        print("⚠️ Signal: Neutral — No clear trend")
        return

    print(f"🎫 Symbol: {symbol}")
    print(f"💰 Entry: ₹{entry}")
    print(f"🎯 Target: ₹{target}")
    print(f"⛔ Stop-Loss: ₹{stop_loss}")
    print(f"📊 Sentiment Score: {sentiment_score}")
    print(f"📈 PCR: {pcr}")

def main():
    print(f"# 📅 Report - {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}\n")
    sentiment_score = get_global_sentiment()
    banknifty_data = analyze_banknifty()
    generate_trade_signal(banknifty_data, sentiment_score)

if __name__ == "__main__":
    main()
