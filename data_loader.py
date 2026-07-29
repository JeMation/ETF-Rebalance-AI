import yfinance as yf
import FinanceDataReader as fdr

def is_korean_ticker(ticker):
    return ticker.isdigit()


def get_exchange_rate():
    pass


def get_us_etf_data(ticker):
    pass


def get_kr_etf_data(ticker, period="1y"):
    df = fdr.DataReader(ticker)

    # 최근 1년 데이터만 사용
    df = df.tail(252)

    prices = df["Close"]

    return {
        "labels": prices.index.strftime("%Y-%m-%d").tolist(),
        "values": prices.tolist()
    }

def get_etf_data(symbol="QQQ", period="1y"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)

    prices = df["Close"]

    return {
        "labels": prices.index.strftime("%Y-%m-%d").tolist(),
        "values": prices.tolist()
    }

if __name__ == "__main__":
    data = get_kr_etf_data("161510")

    print(data["labels"][:5])
    print(data["values"][:5])