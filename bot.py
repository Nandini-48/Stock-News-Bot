import os
import logging
import yfinance as yf
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# ✅ Logging setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

ALPHA_VANTAGE_API_KEY = "8acd8ce888e44c4dbe2af98c2a72f5a6"

# ✅ Function to get stock price
def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return round(data["Close"].iloc[-1], 2)
    return None

def get_market_sentiment(ticker):
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        news = response.json()

        positive, negative = 0, 0
        for article in news.get("feed", []):
            if "bullish" in article.get("title", "").lower():
                positive += 1
            elif "bearish" in article.get("title", "").lower():
                negative += 1
        
        return "Bullish" if positive > negative else "Bearish"
    
    except Exception as e:
        return "Neutral"


# ✅ Function to get stock news
def get_stock_news(ticker):
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        logging.debug(f"🔍 Fetching news from API: {url}")  # ✅ Logging Debug

        response = requests.get(url)
        logging.debug(f"📡 API Response Status: {response.status_code}")  

        try:
            json_response = response.json()
            logging.debug(f"📜 API Response JSON: {json_response}")  
        except Exception as e:
            logging.error(f"🚨 JSON Parsing Error: {e}")  
            return ["Error parsing news data."]

        if response.status_code == 200 and "feed" in json_response and json_response["feed"]:
            articles = [article["title"] for article in json_response["feed"][:2]]
            logging.info(f"📰 News Fetched: {articles}")  
            return articles

        logging.warning("⚠️ No news available from API.")
        return ["No recent news available."]
    
    except requests.exceptions.RequestException as req_err:
        logging.error(f"🚨 Request Exception: {req_err}")
        return ["Error fetching news."]
    except Exception as e:
        logging.error(f"🚨 General Error: {e}")
        return ["Error fetching news."]

# ✅ Socket event for stock updates
@socketio.on("subscribe_stock")
def send_stock_data(data):
    ticker = data.get("ticker", "TSLA").upper()
    logging.info(f"✅ Received stock subscription request: {ticker}")  # ✅ Logging Debug

    price = get_stock_price(ticker)
    logging.info(f"💰 Stock Price Fetched: {price}")  

    news = get_stock_news(ticker)
    logging.info(f"📰 News Received in Function: {news}")  

    sentiment = get_market_sentiment(ticker)
    logging.info(f"📊 Market Sentiment Fetched: {sentiment}")  

    if price:
        socketio.emit("stock_update", {"ticker": ticker, "price": price, "news": news, "sentiment": sentiment})
    else:
        socketio.emit("stock_update", {"error": "Invalid stock ticker or data not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
