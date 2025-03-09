import os
import yfinance as yf
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")  # Eventlet async mode

ALPHA_VANTAGE_API_KEY = "YT6ZNN6907UWED2Z"

# Function to get stock price
def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return round(data["Close"].iloc[-1], 2)
    return None

# Function to get stock news
def get_stock_news(ticker):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json().get("feed", [])
        return [article["title"] for article in news_data[:2]]
    return ["No recent news available."]

# Function to get market sentiment (Bullish / Bearish)
def get_market_sentiment(ticker):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        news = response.json()
        positive, negative = 0, 0
        for article in news.get("feed", []):
            if "bullish" in article.get("title", "").lower():
                positive += 1
            elif "bearish" in article.get("title", "").lower():
                negative += 1
        return "Bullish" if positive > negative else "Bearish"
    return "Neutral"

# Add a test route to check if server is running
@app.route('/')
def index():
    return "Server is running!"

# Socket event for stock updates
@socketio.on("subscribe_stock")
def send_stock_data(data):
    ticker = data.get("ticker", "TSLA").upper()
    price = get_stock_price(ticker)
    news = get_stock_news(ticker)
    sentiment = get_market_sentiment(ticker)

    if price:
        socketio.emit("stock_update", {"ticker": ticker, "price": price, "news": news, "sentiment": sentiment})
    else:
        socketio.emit("stock_update", {"error": "Invalid stock ticker or data not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns port dynamically
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
