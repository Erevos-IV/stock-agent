⚠️ WARNING: NOT FINANCIAL ADVICE

This software is for educational and informational purposes only.

Do not use this tool as the sole basis for any investment decisions.

Do not risk money you cannot afford to lose.

The data provided (Yahoo Finance, Google News) may be delayed, inaccurate, or incomplete.

The "Buy/Sell" signals generated are purely mathematical outputs based on historical data and simple algorithms. They do not account for real-world complexity, market manipulation, or black swan events.

Always consult with a qualified financial advisor or do your own due diligence before trading.

Pro Stock Analysis Agent

An advanced Python-based financial agent that combines Sentiment Analysis (Google News), Fundamental Valuation, and Technical Analysis to generate actionable "Buy/Sell/Hold" signals with a confidence score.

🚀 Features

Sentiment Engine: Fetches real-time news from Google News RSS and uses NLTK VADER to score headlines (Positive/Negative/Neutral).

Valuation Engine: Analyzes PEG Ratio, Trailing P/E, and Forward P/E to determine if a stock is cheap or expensive relative to its growth.

Technical Analysis:

RSI (Relative Strength Index): Detects Overbought (>70) and Oversold (<30) conditions.

SMA (Simple Moving Average): Checks if the stock is in an uptrend (Price > 50-Day SMA).

Pro Scoring System: Generates a 0-100 Confidence Score based on 5 weighted factors.

Dual Strategy Modes:

trend: Best for Bear Markets (Sells downtrends).

reversion: Best for Bull Markets (Buys dips).

📦 Installation

Clone the repository (or download the files).

Install dependencies:

pip install -r requirements.txt


🛠 Usage

Open stock_agent.py and edit the my_watchlist list with your favorite tickers:

my_watchlist = ["AAPL", "TSLA", "NVDA", "MSFT"]


Run the agent:

python stock_agent.py


View Results:

A summary table will appear in your terminal.

A detailed CSV report (e.g., Pro_Stock_Report_2025-11-22.csv) will be saved in the same folder.

🧠 How It Works (The Logic)

1. The Confidence Score (0-100)

The agent starts with a neutral score of 50 and adds/subtracts points based on evidence:

Factor

Condition

Points

Reasoning

Valuation

PEG < 1.0 (Undervalued)

+20

Growth is cheap.



PEG > 2.0 (Overvalued)

-20

Price is too high for growth.

Technicals

RSI < 30 (Oversold)

+15

Potential bounce/reversal.



Price > 50 SMA

+10

Stock is in a healthy uptrend.

Sentiment

Positive News Sentiment

+10

Good PR/Earnings buzz.

Analyst

Upside > 20%

+15

Wall St. expects price to rise.

Volume

Vol > 1.2x Average

+5

High conviction move.

2. Strategy Modes

You can toggle STRATEGY_MODE at the top of stock_agent.py.

"trend" (Default):

Logic: "Don't catch a falling knife."

Behavior: Punishes stocks trading below their 50-Day Moving Average (-25 points).

Best For: Bear Markets, Corrections, Volatile periods.

"reversion":

Logic: "Buy low, sell high."

Behavior: Rewards stocks with low RSI (Oversold) even if they are downtrending.

Best For: Bull Markets, Blue-chip accumulation.

📊 Interpreting the Report

Signal: The final recommendation (STRONG BUY, BUY, HOLD, SELL).

Score: The strength of the signal (0-100). 80+ is very strong.

RSI: Momentum indicator.

< 30: Oversold (Panic selling).

> 70: Overbought (Euphoria).

Vol Ratio: Current Volume vs. 10-Day Average.

> 1.0: Higher than normal volume (Institutional activity).

< 0.8: Weak interest.

Analyst Upside: How much higher Wall Street analysts think the stock will go.
