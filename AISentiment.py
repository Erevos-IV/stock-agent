import yfinance as yf
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime
import time
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os

# --- CONFIGURATION ---
# Paste your key below. No complex checks needed.
GOOGLE_API_KEY = "APIKEYHERE" 

# Initialize AI
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-2.5-flash') # MODEL HERE
except Exception as e:
    print(f"⚠️ AI Init Failed: {e}")
    ai_model = None

class StockAgent:
    def __init__(self, tickers):
        self.tickers = tickers
        self.analyzer = SentimentIntensityAnalyzer()
        self.results = []

    def _safe_float(self, value, default=0.0):
        """ Helper to safely convert values to float, handling None types. """
        try:
            if value is None: return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def calculate_rsi(self, ticker_symbol, period=14):
        """ Calculates RSI using 6 months of data for stability. """
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="6mo") 
            if hist.empty: return 50
            
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except: return 50

    def get_news_headlines(self, ticker_symbol):
        """ Fetches headlines from Google News RSS. """
        url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        headlines = []
        try:
            response = requests.get(url, headers=headers, timeout=10)
            root = ET.fromstring(response.content)
            for item in root.findall('./channel/item')[:5]:
                title = item.find('title')
                if title is not None:
                    headlines.append(title.text)
        except: pass
        return headlines

    def get_ai_analysis(self, ticker, headlines):
        """ Asks Gemini AI to interpret the news for long-term impact. """
        if not ai_model or not headlines:
            return "AI Disabled/No News"
        
        prompt = f"""
        You are a senior financial analyst. Analyze these news headlines for {ticker}:
        {headlines}
        
        In 1 very short sentence (max 15 words), summarize if this is a temporary setback or a long-term fundamental problem. 
        Focus on the business health, not just price action.
        """
        try:
            response = ai_model.generate_content(prompt)
            return response.text.strip()
        except:
            return "AI Error"

    def get_long_term_metrics(self, ticker_symbol):
        """ Fetches Quality, Safety, and Valuation metrics. """
        ticker = yf.Ticker(ticker_symbol)
        try:
            info = ticker.info
        except:
            info = {}

        price = self._safe_float(info.get('currentPrice'), 0)
        
        # --- Fundamental Quality (The "Moat") ---
        margins = self._safe_float(info.get('profitMargins')) * 100
        debt_equity = self._safe_float(info.get('debtToEquity'))
        roe = self._safe_float(info.get('returnOnEquity')) * 100
        
        # --- Valuation ---
        peg_ratio = self._safe_float(info.get('pegRatio'), 999.0) 
        fwd_pe = self._safe_float(info.get('forwardPE'))
        
        # --- Long Term Trend ---
        sma_200 = self._safe_float(info.get('twoHundredDayAverage'), price)
        rsi = self.calculate_rsi(ticker_symbol)
        
        # Analyst Upside
        target_price = self._safe_float(info.get('targetMeanPrice'), price)
        upside = ((target_price - price) / price) * 100 if price and target_price else 0

        return {
            "price": price,
            "margins": margins,
            "debt": debt_equity,
            "roe": roe,
            "peg": peg_ratio,
            "fwd_pe": fwd_pe,
            "sma_200": sma_200,
            "rsi": rsi,
            "upside": upside
        }

    def calculate_long_term_score(self, data):
        """ Generates a 0-100 Quality Score. """
        score = 50 
        reasons = []

        # 1. Profitability (Quality)
        if data['margins'] > 20:
            score += 15
            reasons.append("High Margins")
        elif data['margins'] < 5:
            score -= 15
            reasons.append("Low Margins")

        # 2. Financial Health (Safety)
        if data['debt'] < 50 and data['debt'] > 0: 
            score += 10
            reasons.append("Low Debt")
        elif data['debt'] > 150: 
            score -= 15
            reasons.append("High Debt")

        # 3. Valuation (Price)
        if data['peg'] != 999.0:
            if data['peg'] < 1.2:
                score += 20
                reasons.append("Cheap Growth (PEG)")
            elif data['peg'] > 2.5:
                score -= 15
                reasons.append("Expensive")

        # 4. Long Term Trend (Timing)
        if data['price'] > data['sma_200']:
            score += 10
            reasons.append("Bull Trend (>200SMA)")
        else:
            if data['rsi'] < 30:
                score += 10
                reasons.append("Deep Value Dip")
            else:
                score -= 15
                reasons.append("Long Term Downtrend")

        # 5. Analyst Consensus
        if data['upside'] > 20:
            score += 10
        
        score = max(0, min(100, score))
        
        if score >= 80: signal = "STRONG BUY"
        elif score >= 60: signal = "BUY"
        elif score <= 40: signal = "SELL"
        else: signal = "HOLD"

        return score, signal, ", ".join(reasons[:3])

    def run_analysis(self):
        print(f"--- Long-Term AI Investment Agent ---")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        for t in self.tickers:
            print(f"Analyzing {t}...")
            
            # 1. Get Data
            headlines = self.get_news_headlines(t)
            data = self.get_long_term_metrics(t)
            
            # 2. AI Reasoning
            ai_summary = self.get_ai_analysis(t, headlines)
            
            # 3. Score
            score, signal, key_factors = self.calculate_long_term_score(data)

            self.results.append({
                "Ticker": t,
                "Price": data['price'],
                "Signal": signal,
                "Score": score,
                "AI Outlook": ai_summary,
                "Key Factors": key_factors,
                "Margins": f"{data['margins']:.1f}%",
                "Debt/Eq": f"{data['debt']:.1f}",
                "PEG": f"{data['peg']:.2f}" if data['peg'] != 999 else "N/A",
                "Upside": f"{data['upside']:.1f}%"
            })
            time.sleep(1) # Gentle delay for AI API
                
        return pd.DataFrame(self.results)

if __name__ == "__main__":
    # Long term watchlist (mix of Tech, Consumer, Finance)
    my_watchlist = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "KO", "JPM", "COST"]
    
    agent = StockAgent(my_watchlist)
    df = agent.run_analysis()
    
    if not df.empty:
        cols = ["Ticker", "Price", "Signal", "Score", "AI Outlook", "Key Factors", "Margins", "PEG", "Upside"]
        print("\n" + "="*100)
        print(df[cols].to_string(index=False))
        print("="*100)
        
        filename = f"LongTerm_AI_Report_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"\nReport saved to {filename}")
    else:
        print("No data found.")
