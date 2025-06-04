# 🤖 Crypto Insights Bot 📈🔮

**Your AI-Powered Telegram Companion for Navigating the Crypto Markets!**

[![Crypto Bot In Action](https://via.placeholder.com/728x90.png?text=Imagine+a+Cool+Bot+Demo+GIF+Here)](https://t.me/your_bot_username_here)

This bot isn't just another price ticker. It's your personal crypto analyst, ready 24/7 on Telegram! Get real-time prices, generate insightful charts, and unlock AI-driven pattern analysis and price forecasts, all powered by Bybit and Google's Gemini API.

---

## 🌟 Key Features

*   **📊 Universal Price & Charting:**
    *   Fetch current prices for **any** coin listed on Bybit.
    *   Generate detailed candlestick charts with volume data.
    *   Interactive chart buttons for quick timeframe switching (1H, 4H, 1D).
*   **🧠 AI-Powered Chart Pattern Analysis (via Gemini):**
    *   `/chart` command captions now include AI-detected pattern insights.
    *   Dedicated `/analyze <symbol> [interval] [days]` command for in-depth pattern breakdown (identifies trends, support/resistance, potential breakouts).
*   **🔮 AI Price Prediction (via Gemini):**
    *   `/predict <symbol> [period]` command to forecast prices for `24h`, `1d`, `3d`, or `7d`.
    *   Visualizes the predicted path directly on the historical price chart.
    *   Provides textual AI analysis supporting the forecast.
*   **🤖 Smart & User-Friendly:**
    *   **Natural Language Search:** Just type a coin name (`bitcoin`) or symbol (`BTC`).
    *   **Smart Suggestions:** If your query is ambiguous, the bot suggests matching symbols.
    *   **Popular Coins Menu:** Quickly access frequently checked cryptocurrencies.
    *   **Comprehensive Help:** `/help` command details all functionalities.
*   **⚙️ Robust & Extensible:**
    *   Built with Python, leveraging `requests`, `matplotlib`, and `google-generativeai`.
    *   Handles API interactions, data processing, chart generation, and Telegram communication.

---

## 🚀 Quick Start & Usage

Interacting with the bot is as simple as sending a message on Telegram!

1.  **Find the bot on Telegram:** (Link to your bot, e.g., `t.me/YourCryptoInsightsBot`)
2.  **Send `/start`** for a welcome message and quick navigation.

### Core Commands:

*   **Get Price:**
    *   Simply type the coin name or symbol: `BTC`, `ethereum`, `doge usdt`
    *   Or use the command: `/price SOL`
*   **Get Chart (with AI Pattern Insights in caption):**
    *   `/chart BTC` (Default: 1-hour candles, 3 days data)
    *   `/chart ETH 4h` (4-hour candles, 7 days data)
    *   `/chart ADA 1d 30` (Daily candles, 30 days data)
*   **AI Chart Pattern Analysis:**
    *   `/analyze SOL` (Default: 4-hour candles, 7 days context)
    *   `/analyze BTC 1h 3` (1-hour candles, 3 days context for analysis)
*   **AI Price Prediction:**
    *   `/predict ETH` (Default: 1-day forecast)
    *   `/predict ADA 3d` (3-day forecast for Cardano)
    *   `/predict DOT 7d` (7-day forecast for Polkadot)
*   **Discover Coins:**
    *   `/popular` - Shows a menu of popular coins.
    *   `/search shiba` - Searches for coins matching "shiba".
*   **Help & Info:**
    *   `/help` - Shows all available commands and usage instructions.
    *   `/list` - Displays information about the number of supported trading pairs.

---

## 🛠️ Technologies Used

*   **Python 3.x**
*   **Telegram Bot API:** For interacting with Telegram.
*   **Bybit API:** For cryptocurrency market data (prices, kline/candlestick data).
*   **Google Gemini API:** For AI-powered chart pattern analysis and price forecasting.
*   **Matplotlib & Pandas:** For generating and processing data for charts.
*   **Requests:** For making HTTP API calls.
*   **Standard Python Libraries:** `hmac`, `hashlib`, `json`, `datetime`, `asyncio`, etc.

---

## ⚙️ Setup & Configuration (For Developers)

1.  **Clone the repository:**
    ```bash
    git clone https://your-repo-url/crypto-insights-bot.git
    cd crypto-insights-bot
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `requirements.txt` includes `requests`, `matplotlib`, `pandas`, `google-generativeai`)*
3.  **Set API Keys:**
    *   Open `main.py`.
    *   Replace placeholder values for:
        *   `TELEGRAM_BOT_TOKEN`
        *   `BYBIT_API_KEY`
        *   `BYBIT_API_SECRET`
        *   `GEMINI_API_KEY`
    *   **Security Note:** For production, use environment variables or a secure secrets management solution instead of hardcoding keys.
4.  **Run the bot:**
    ```bash
    python main.py
    ```

---

## 💡 Why This Bot?

In the fast-paced world of cryptocurrencies, timely information and insightful analysis are key. This bot aims to provide:

*   **Accessibility:** Complex data and AI analysis, available directly in your Telegram chat.
*   **Speed:** Quick access to prices, charts, and AI insights.
*   **Intelligence:** Goes beyond simple price lookups by integrating advanced AI for pattern recognition and forecasting.
*   **User-Experience:** Designed to be intuitive and easy to use for both beginners and experienced traders.

---

## ✨ Future Ideas

*   Customizable alert notifications for price movements or pattern formations.
*   Portfolio tracking features.
*   Integration with more exchanges or data sources.
*   Advanced sentiment analysis from news/social media.
*   User-configurable AI analysis parameters.

---

## 🔑 API Keys Notice

This bot requires API keys for Telegram, Bybit, and Google Gemini to function.
*   **Telegram Bot Token:** Get this from BotFather on Telegram.
*   **Bybit API Key & Secret:** Generate these from your Bybit account (ensure appropriate permissions).
*   **Google Gemini API Key:** Obtain this from Google AI Studio or Google Cloud Console.

**Always keep your API keys secure and never share them publicly.**

---

Happy Trading and Analyzing! 🚀
