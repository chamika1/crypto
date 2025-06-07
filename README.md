# 🤖 Crypto Insights Bot 📈🔮

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Replace with your actual license -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) <!-- Or your preferred formatter -->
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg?logo=telegram)](https://t.me/your_bot_username_here) <!-- Replace with your bot link -->
[![GitHub stars](https://img.shields.io/github/stars/chamika1/crypto.svg?style=social&label=Star&maxAge=2592000)](https://github.com/chamika1/crypto/stargazers/) <!-- Replace with your repo -->
[![GitHub forks](https://img.shields.io/github/forks/chamika1/crypto.svg?style=social&label=Fork&maxAge=2592000)](https://github.com/chamika1/crypto/network/members) <!-- Replace with your repo -->

**Your AI-Powered Telegram Companion for Navigating the Crypto Markets!**

[![Crypto Bot In Action](https://via.placeholder.com/728x90.png?text=Imagine+a+Cool+Bot+Demo+GIF+Here)](https://t.me/your_bot_username_here) <!-- Replace with your bot link or a real GIF -->

This bot isn't just another price ticker. It's your personal crypto analyst, ready 24/7 on Telegram! Get real-time prices, generate insightful charts, and unlock AI-driven pattern analysis and price forecasts, all powered by Bybit and Google's Gemini API.

---

## 🌟 Overview

The Crypto Insights Bot provides a comprehensive suite of tools for cryptocurrency enthusiasts and traders. It leverages powerful APIs to deliver real-time data and AI-driven analysis directly to your Telegram chat.

## ✨ Key Features

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

## 🛠️ Tech Stack

This project is built with a modern and robust stack:

*   **Programming Language:**
    *   ![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
*   **Core Libraries & Frameworks:**
    *   ![Flask](https://img.shields.io/badge/Flask-Framework-lightgrey?logo=flask) (If used for web components or API)
    *   ![Requests](https://img.shields.io/badge/Requests-HTTP%20Library-brightgreen)
    *   ![Matplotlib](https://img.shields.io/badge/Matplotlib-Plotting-orange)
    *   ![NumPy](https://img.shields.io/badge/NumPy-Numerical%20Computing-blueviolet)
    *   ![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-darkgreen)
    *   ![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI%20Server-green) (If deploying a Flask app)
*   **APIs & Services:**
    *   **Telegram Bot API:** For interacting with Telegram.
    *   **Bybit API:** For cryptocurrency market data.
    *   **Google Gemini API:** For AI-powered analysis and forecasting.
*   **Development Tools:**
    *   Git & GitHub
    *   VS Code (or your preferred IDE)

---

## ⚙️ Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://your-repo-url/crypto-insights-bot.git
    cd crypto-insights-bot
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set API Keys & Environment Variables:**
    *   Create a `.env` file in the root directory or set environment variables directly.
    *   **Example `.env` file:**
        ```env
        TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
        BYBIT_API_KEY="YOUR_BYBIT_API_KEY"
        BYBIT_API_SECRET="YOUR_BYBIT_API_SECRET"
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```
    *   Update `main.py` to load these variables (e.g., using `python-dotenv` library or `os.environ`).
    *   **Security Note:** **Never commit your `.env` file or hardcode API keys directly into your scripts for production.** Add `.env` to your `.gitignore` file.
4.  **Run the bot:**
    ```bash
    python main.py
    ```

---

## 🚀 Deployment (Example with Gunicorn for Flask)

If your bot includes a Flask component (e.g., for a health check endpoint or webhook), you might deploy it using Gunicorn:

```bash
gunicorn main:app # Assuming 'app' is your Flask instance in main.py
```

Adjust according to your specific application structure.

---

## 💡 Why This Bot?
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

## ✨ Potential Future Enhancements

*   **Advanced Alerting:** Customizable notifications for price swings, volume spikes, or specific pattern formations.
*   **Portfolio Management:** Allow users to track their crypto holdings and performance.
*   **Expanded Exchange Support:** Integrate with additional cryptocurrency exchanges.
*   **Sentiment Analysis:** Incorporate sentiment data from news articles and social media.
*   **Deeper AI Customization:** Allow users to fine-tune parameters for AI analysis.
*   **Web Interface:** A simple web dashboard for viewing trends or managing bot settings.

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements or new features, feel free to:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

Please ensure your code adheres to the project's coding standards.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (you'll need to create this file if you choose MIT).

---

## 🔑 API Keys Notice

This bot requires API keys for Telegram, Bybit, and Google Gemini to function.
*   **Telegram Bot Token:** Get this from BotFather on Telegram.
*   **Bybit API Key & Secret:** Generate these from your Bybit account (ensure appropriate permissions).
*   **Google Gemini API Key:** Obtain this from Google AI Studio or Google Cloud Console.

**Always keep your API keys secure and never share them publicly.**

---

Happy Trading and Analyzing! 🚀
