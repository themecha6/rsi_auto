import time
import pyupbit
import datetime
import requests

access = 'x9bFXzCAlIqxnSWa0nW00IytezGAE2ET9CsbkN11'
secret = 'ji2JiozEVIkWV9fQDq4V5K6yAtXIMeDPTBWnxvAX'
myToken = "xoxb-3366670448406-3373355330210-jjHAci2MD6OO3vxzcVhPuDXM"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+ token},
        data={"channel": channel,"text": text}
    )

# 로그인
upbit = pyupbit.Upbit(access, secret)

# 시작 메세지 슬랙 전송
post_message(myToken,"#aleart", "autotrade start")
print("start auto Trade")

k = 0.55
bid_price = 100000
KRW_tickers = pyupbit.get_tickers(fiat="KRW")
KRW_tickers.remove("KRW-BTT")

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_yesterday_ma5(ticker):
    """이동평균 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=10)
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[-2]

def buy_order(ticker, price):
    """매수 주문"""
    upbit.buy_market_order(ticker, price)
    post_message(myToken,"#aleart", "{} 매수 완료, 매수 가격 : {}".format(ticker, price))
    print("{} 매수 완료".format(ticker))
    return 0

def sell_order(ticker, price, sell_price):
    """매도 주문"""
    upbit.sell_market_order(ticker, price)
    post_message(myToken,"#aleart", "{} 매도 완료, 매도 가격 : {}".format(ticker, int(sell_price)))
    print("{} 매도 완료".format(ticker))
    return 0

# 자동매매 시작
while True:
    try:
        buy_tickers = []
        # for tickers in KRW_tickers:
            # ma5 = get_yesterday_ma5(tickers)
            # df1 = pyupbit.get_ohlcv(tickers, interval="minute240", count=1)
            # open_price = df1.iloc[0]['open']
            # print(tickers, open_price, ma5)
            # if open_price > ma5:
            #     bid_tickers.append(tickers)
            # balance = upbit.get_balance(tickers[tickers.index("-")+1:])
            # ticker_balance = balance * get_current_price(tickers)
            # if ticker_balance > 5000:
            #     buy_tickers.append(tickers)
            #     if tickers not in bid_tickers:
            #         bid_tickers.append(tickers)
            # time.sleep(0.1)
        start_time = get_start_time("KRW-BTC") + datetime.timedelta(minutes=5)
        end_time = start_time + datetime.timedelta(hours=3, minutes=50)
        while True:
            now = datetime.datetime.now()
            print(start_time, end_time, now)
            print(buy_tickers)
            if start_time < now < end_time:
                for tickers in KRW_tickers:
                    print("{} 매수 조건 검색중".format(tickers))
                    balance = upbit.get_balance(tickers[tickers.index("-") +1:])
                    ticker_balance = balance * get_current_price(tickers)
                    target_price = get_target_price(tickers, k)
                    current_price = get_current_price(tickers)
                    avrPrice = upbit.get_avg_buy_price(tickers)
                    ma5 = get_yesterday_ma5(tickers)
                    if (ticker_balance) > 5000 and (tickers not in buy_tickers):
                        buy_tickers.append(tickers)
                    if (avrPrice * 0.96 > current_price) and (ticker_balance > 5000):
                        sell_order(tickers,balance, ticker_balance)
                        buy_tickers.remove(tickers)
                    if (target_price < current_price) and (current_price > ma5) and (tickers not in buy_tickers):
                        krw = get_balance("KRW")
                        if krw > bid_price:
                            buy_order(tickers, bid_price)
                            buy_tickers.append(tickers)
                        time.sleep(0.1)
            elif end_time + datetime.timedelta(minutes=5) > now > end_time :
                for tickers in KRW_tickers:
                    print("{} 매도 준비중".format(tickers))
                    balance = upbit.get_balance(tickers[tickers.index("-") +1:])
                    ticker_balance = balance * get_current_price(tickers)
                    if ticker_balance > 5000:
                        sell_order(tickers, balance, ticker_balance)
                    time.sleep(0.1)
            else :
                print ("1사이클 완료")
                time.sleep(1)
                break

    except Exception as e:
        print(e)
        post_message(myToken,"#aleart", e)
        time.sleep(1)