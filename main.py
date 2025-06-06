import asyncio
import requests
import time
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
import threading
import os
import re
import io
import base64
import uuid # For unique request IDs

# For chart generation
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

# Simple HTTP server for webhook (alternative to polling)
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# For Gemini API
import google.generativeai as genai

# Gemini API Key (Ideally, use environment variables or a secrets manager)
GEMINI_API_KEY = "GEMINI_API_KEY"
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE": # Basic check
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini API configured.")
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        GEMINI_API_KEY = None # Disable Gemini features if config fails
else:
    print("⚠️ Gemini API key not set or is a placeholder. Gemini features will be disabled.")
    GEMINI_API_KEY = None


class BybitCryptoBotEnhanced:
    def __init__(self, telegram_token, api_key, api_secret):
        self.telegram_token = telegram_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bybit.com"
        self.telegram_api = f"https://api.telegram.org/bot{telegram_token}"
        
        self.popular_coins = [
            "BTC", "ETH", "BNB", "XRP", "ADA", "DOT", "LINK", "LTC", "BCH", "UNI",
            "SOL", "MATIC", "AVAX", "ATOM", "ALGO", "MANA", "SAND", "AXS", "DYDX",
            "DOGE", "SHIB", "TRX", "NEAR", "FTM", "CRO", "APE", "GMT", "OP", "ARB"
        ]
        
        self.coin_aliases = {
            'BITCOIN': 'BTC', 'ETHEREUM': 'ETH', 'RIPPLE': 'XRP', 'CARDANO': 'ADA',
            'POLKADOT': 'DOT', 'CHAINLINK': 'LINK', 'LITECOIN': 'LTC', 
            'BITCOIN CASH': 'BCH', 'UNISWAP': 'UNI', 'SOLANA': 'SOL', 
            'POLYGON': 'MATIC', 'AVALANCHE': 'AVAX', 'COSMOS': 'ATOM', 
            'ALGORAND': 'ALGO', 'DOGECOIN': 'DOGE', 'SHIBA INU': 'SHIB', 'TRON': 'TRX'
        }
        
        self.offset = 0
        self.supported_symbols_cache = set()
        self.cache_updated = False
        plt.style.use('dark_background')
    
    def generate_signature(self, timestamp, params_str):
        param_str = str(timestamp) + self.api_key + params_str
        return hmac.new(
            bytes(self.api_secret, 'utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def make_request(self, endpoint, params=None):
        if params is None: params = {}
        timestamp = str(int(time.time() * 1000))
        params_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = self.generate_signature(timestamp, params_str)
        headers = {
            'X-BAPI-API-KEY': self.api_key, 'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp, 'Content-Type': 'application/json'
        }
        url = f"{self.base_url}{endpoint}"
        if params_str: url += f"?{params_str}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_symbols(self):
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {"category": "spot"}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    symbols = set()
                    for item in data.get('result', {}).get('list', []):
                        symbol = item.get('symbol', '')
                        if symbol.endswith('USDT'):
                            symbols.add(symbol.replace('USDT', ''))
                    return symbols
        except Exception as e:
            print(f"Error getting symbols: {e}")
        return set()
    
    def update_symbols_cache(self):
        if not self.cache_updated:
            print("📊 Updating supported symbols cache...")
            self.supported_symbols_cache = self.get_all_symbols()
            self.cache_updated = True
            print(f"✅ Cached {len(self.supported_symbols_cache)} symbols")
    
    def normalize_symbol(self, symbol):
        symbol = symbol.strip().upper()
        symbol = re.sub(r'(USDT|USD|/USDT|/USD)$', '', symbol)
        return self.coin_aliases.get(symbol, symbol)
    
    def find_matching_symbols(self, query):
        query = query.upper()
        self.update_symbols_cache()
        if query in self.supported_symbols_cache: return [query]
        return [s for s in self.supported_symbols_cache if query in s][:5]

    def get_kline_data(self, symbol, user_interval='1h', limit=168):
        bybit_interval_map = {'1h': '60', '4h': '240', '1d': 'D'}
        api_interval = bybit_interval_map.get(user_interval, '60')
        url = f"{self.base_url}/v5/market/kline"
        params = {"category": "spot", "symbol": f"{symbol}USDT", "interval": api_interval, "limit": limit}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    return data.get('result', {}).get('list', [])
                else:
                    print(f"DEBUG: Bybit kline API error for {symbol}USDT (interval: {api_interval}): {data.get('retCode')} - {data.get('retMsg')}")
        except Exception as e:
            print(f"Error in get_kline_data for {symbol} (interval: {api_interval}): {e}")
        return []

    def create_price_chart(self, symbol, requested_interval='1h', requested_days=7):
        intervals_to_try_config = [('1h', 3), ('4h', 7), ('1d', 30)]
        unique_intervals_to_try = []
        seen_intervals = set()

        if requested_interval in ['1h', '4h', '1d']:
            unique_intervals_to_try.append((requested_interval, requested_days))
            seen_intervals.add(requested_interval)
        for user_i, default_d in intervals_to_try_config:
            if user_i not in seen_intervals:
                unique_intervals_to_try.append((user_i, default_d))
                seen_intervals.add(user_i)

        kline_data = None
        final_interval_used = requested_interval
        final_days_used = requested_days
        print(f"DEBUG: Chart generation for {symbol}. Initial request: interval {requested_interval}, days {requested_days}.")

        for current_user_interval, current_days in unique_intervals_to_try:
            print(f"DEBUG: Trying chart for {symbol} with user_interval: {current_user_interval}, days: {current_days}")
            limit = {'1h': current_days * 24, '4h': current_days * 6, '1d': current_days}.get(current_user_interval, 200)
            if limit == 200 and current_user_interval not in ['1h', '4h', '1d']: 
                 print(f"Warning: Unexpected interval '{current_user_interval}' in fallback logic.")

            kline_data = self.get_kline_data(symbol, current_user_interval, limit)
            if kline_data:
                print(f"DEBUG: Success! Fetched kline data for {symbol} with user_interval {current_user_interval}, limit {limit}.")
                final_interval_used = current_user_interval
                final_days_used = current_days
                break
            else:
                print(f"DEBUG: Failed for {symbol} with user_interval {current_user_interval}. Trying next.")
        
        if not kline_data:
            print(f"DEBUG: All fallbacks failed for {symbol}. No kline data. Returning None.")
            return None
            
        try:
            df_data = [{'timestamp': int(c[0]), 'open': float(c[1]), 'high': float(c[2]), 
                        'low': float(c[3]), 'close': float(c[4]), 'volume': float(c[5])}
                       for c in reversed(kline_data)]
            df = pd.DataFrame(df_data)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
            fig.patch.set_facecolor('#0a0a0a')
            
            for i, row in df.iterrows():
                color = '#00ff88' if row['close'] >= row['open'] else '#ff4757'
                ax1.plot([row['datetime'], row['datetime']], [row['low'], row['high']], color=color, linewidth=1, alpha=0.8)
                rect = Rectangle((mdates.date2num(row['datetime']) - 0.0003, min(row['open'], row['close'])),
                                 0.0006, abs(row['close'] - row['open']),
                                 facecolor=color, alpha=0.8, edgecolor=color)
                ax1.add_patch(rect)
            ax1.plot(df['datetime'], df['close'], color='#ffa502', linewidth=1.5, alpha=0.7)
            
            ax1.set_facecolor('#0a0a0a')
            ax1.grid(True, alpha=0.3, color='#333333')
            ax1.set_title(f'{symbol}/USDT Price Chart ({final_interval_used}, {final_days_used} days)', 
                          color='#ffffff', fontsize=16, fontweight='bold', pad=20)
            ax1.set_ylabel('Price (USDT)', color='#ffffff', fontsize=12)
            ax1.tick_params(axis='y', colors='#ffffff') 
            ax1.tick_params(axis='x', colors='#ffffff') 

            price_range = df['high'].max() - df['low'].min()
            if price_range < 1: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.6f}'))
            elif price_range < 100: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))
            else: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
            
            volume_bar_colors = ['#00ff88' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ff4757' for i in range(len(df))]
            ax2.bar(df['datetime'], df['volume'], color=volume_bar_colors, alpha=0.6, width=0.0008)
            ax2.set_facecolor('#0a0a0a')
            ax2.grid(True, alpha=0.3, color='#333333')
            ax2.set_ylabel('Volume', color='#ffffff', fontsize=12)
            ax2.tick_params(axis='y', colors='#ffffff') 
            ax2.tick_params(axis='x', colors='#ffffff') 
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1000000 else f'{x/1000000:.1f}M'))
            
            if final_interval_used == '1h' and final_days_used <= 3:
                date_format = '%m/%d %H:%M'
                locator_interval = max(1, final_days_used * 24 // 6) 
                major_locator = mdates.HourLocator(interval=max(1, 24 // (24//locator_interval if locator_interval > 0 else 1)))
            elif final_interval_used == '1h':
                date_format = '%m/%d'
                major_locator = mdates.DayLocator(interval=max(1, final_days_used // 7))
            elif final_interval_used == '4h':
                date_format = '%m/%d'
                major_locator = mdates.DayLocator(interval=max(1, final_days_used // 7))
            elif final_interval_used == '1d':
                date_format = '%Y-%m-%d'
                if final_days_used <= 14: major_locator = mdates.DayLocator(interval=1)
                elif final_days_used <= 90: major_locator = mdates.WeekdayLocator(interval=1)
                else: major_locator = mdates.MonthLocator(interval=1)
            else:
                date_format = '%m/%d'
                major_locator = mdates.AutoDateLocator()

            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
                ax.xaxis.set_major_locator(major_locator)
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

            current_price = df['close'].iloc[-1]
            price_change_pct = (current_price - df['close'].iloc[0]) / df['close'].iloc[0] * 100 if df['close'].iloc[0] != 0 else 0
            stats_text = f'Current: ${current_price:.6f} | Change: {price_change_pct:+.2f}% | High: ${df["high"].max():.6f} | Low: ${df["low"].min():.6f}'
            fig.suptitle(stats_text, color='#ffffff', fontsize=10, y=0.025) 
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
            plt.subplots_adjust(top=0.93, bottom=0.15) 

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', facecolor='#0a0a0a', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            pattern_analysis_text = "Pattern analysis not available." 
            if GEMINI_API_KEY and kline_data: 
                try:
                    pattern_analysis_text = self.get_chart_pattern_analysis(symbol, kline_data, final_interval_used, final_days_used)
                except Exception as e:
                    print(f"Error invoking pattern analysis from create_price_chart: {e}")
                    pattern_analysis_text = "Error during pattern analysis."
            
            return {
                'image': image_base64, 
                'interval_used': final_interval_used, 
                'days_used': final_days_used,
                'pattern_analysis': pattern_analysis_text
            }
        except Exception as e:
            print(f"Error during chart matplotlib processing: {e}")
            return None

    def get_chart_pattern_analysis(self, symbol, kline_data_list, interval_used, days_used):
        """Get chart pattern analysis for /chart command caption using Gemini API."""
        if not GEMINI_API_KEY:
            return "⚠️ Gemini pattern analysis disabled (API key missing)."

        if not kline_data_list:
            return "No kline data provided for pattern analysis."

        print(f"DEBUG: Getting chart pattern analysis for {symbol} using {len(kline_data_list)} kline entries. Interval: {interval_used}, Days: {days_used}")

        num_points_to_analyze = 100 
        recent_data_newest_first = kline_data_list[:num_points_to_analyze]
        data_to_analyze_chronological = list(reversed(recent_data_newest_first))

        formatted_kline_data = "Timestamp (ms), Open, High, Low, Close, Volume\n"
        for k_entry in data_to_analyze_chronological:
            formatted_kline_data += f"{k_entry[0]}, {k_entry[1]}, {k_entry[2]}, {k_entry[3]}, {k_entry[4]}, {k_entry[5]}\n"
        
        if len(formatted_kline_data) > 3500: 
            formatted_kline_data = formatted_kline_data[:3500] + "\n... (data truncated to fit prompt)"

        prompt = f"""You are a technical analyst specializing in cryptocurrency chart patterns.
Analyze the provided candlestick data for {symbol}/USDT.
The data represents {interval_used} intervals over approximately the last {days_used} days.
The candlestick data below is in chronological order (oldest to newest from the recent set).

Candlestick Data (Timestamp ms, Open, High, Low, Close, Volume):
{formatted_kline_data}

Identify any common chart patterns forming or completed. Examples include:
- Head and Shoulders (and Inverse)
- Triangles (Ascending, Descending, Symmetrical)
- Flags and Pennants (Bullish, Bearish)
- Wedges (Rising, Falling)
- Double/Triple Tops and Bottoms
- Channels (Ascending, Descending, Horizontal)
- Cup and Handle

For each significant pattern identified:
1. Name the pattern.
2. Briefly describe its characteristics based on the data (e.g., key price levels, trendlines).
3. State its typical implication (e.g., bullish continuation, bearish reversal, price target if applicable but optional).

If no distinct patterns are clear, state that "No clear patterns identified in the recent data."
Keep the analysis concise (2-4 short paragraphs or bullet points) and focused on pattern recognition.
Avoid giving financial advice or specific price predictions beyond typical pattern implications.
When referencing specific timestamps in your analysis, please format them as YYYY-MM-DD HH:MM:SS UTC.
"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash') 
            response = model.generate_content(prompt, request_options={'timeout': 45}) # Added timeout
            
            if response.text:
                return response.text.strip()
            else:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    return f"Gemini analysis blocked: {response.prompt_feedback.block_reason}"
                return "Gemini returned no specific pattern analysis."
        except Exception as e:
            print(f"Error calling Gemini API for pattern analysis: {e}")
            return f"❌ Error during pattern analysis for {symbol}. Details: {str(e)}"

    def get_gemini_analysis(self, coin_symbol, user_query="Provide a general analysis."):
        """(Old general coin overview - This is NOT for chart patterns)"""
        if not GEMINI_API_KEY:
            return "⚠️ Gemini API not configured. This feature is unavailable."

        print(f"DEBUG: Getting OLD Gemini general coin overview for {coin_symbol}, query: {user_query}")
        
        price_data = self.get_coin_price(coin_symbol)
        context_data_str = "No current market data available."
        if price_data and 'price' in price_data:
            context_data_str = (
                f"Current market data for {price_data.get('base_symbol', coin_symbol)}/USDT:\n"
                f"- Price: ${price_data.get('price', 0):.6f}\n"
                f"- 24h Change: {price_data.get('change24h', 0):+.2f}%\n"
                f"- 24h Volume: ${price_data.get('volume24h', 0):,.0f}\n"
                f"- 24h High: ${price_data.get('high24h', 0):.6f}\n"
                f"- 24h Low: ${price_data.get('low24h', 0):.6f}"
            )

        prompt_text = f"""You are a cryptocurrency analyst.
Analyze the cryptocurrency: {coin_symbol}

Current Market Data:
{context_data_str}

User's specific question/request: "{user_query}"

Based on the above, provide:
1.  A brief overview of {coin_symbol}.
2.  Analysis of recent performance or news (if available from your knowledge cutoff).
3.  Potential positive and negative factors.
4.  A general sentiment or outlook (avoid specific price predictions or financial advice).
Keep the response concise and informative, suitable for a Telegram bot.
"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt_text, request_options={'timeout': 60}) # Added timeout
            return response.text.strip() if response.text else "Gemini returned no general analysis."
        except Exception as e:
            print(f"Error calling Gemini API for general coin overview: {e}")
            return f"❌ Error getting general coin overview from Gemini for {coin_symbol}. Details: {str(e)}"

    def get_dedicated_chart_pattern_analysis_for_analyze_command(self, symbol, interval='4h', days=7):
        """AI identifies chart patterns for the /analyze command based on user's spec."""
        if not GEMINI_API_KEY:
            return "⚠️ Gemini pattern analysis disabled (API key missing)."

        kline_fetch_limit = 50 
        
        print(f"DEBUG: /analyze command fetching kline for {symbol}, interval {interval}, days {days} (context), kline_fetch_limit {kline_fetch_limit}")
        kline_data_newest_first = self.get_kline_data(symbol, interval, limit=kline_fetch_limit) 
        
        if not kline_data_newest_first or len(kline_data_newest_first) < 5:
            return f"Insufficient kline data for {symbol} at {interval} interval (context: last {days} days) to perform pattern analysis. (Found {len(kline_data_newest_first or [])} candles from fetch attempt of {kline_fetch_limit})"

        recent_candles_to_analyze_newest_first = kline_data_newest_first[:20]
        recent_candles_chronological = list(reversed(recent_candles_to_analyze_newest_first))
        
        ohlc_summary = []
        for i, candle_data in enumerate(recent_candles_chronological):
            ohlc_summary.append(f"Candle {i+1}: O:{candle_data[1]} H:{candle_data[2]} L:{candle_data[3]} C:{candle_data[4]}")
        
        num_analyzed_candles = len(recent_candles_chronological)
        prompt_text = f"""
Analyze this {symbol} {interval} chart pattern from the {num_analyzed_candles} most recent candles (data context is for approx. last {days} days, interval: {interval}):

{chr(10).join(ohlc_summary)}

Identify:
1. Any recognizable patterns (triangles, flags, head & shoulders, wedges, channels, double/triple tops/bottoms etc.)
2. Trend direction and strength.
3. Potential breakout levels (support and resistance).
4. Trading recommendation (e.g., potential entry, stop-loss, take-profit ideas based purely on identified patterns).

Be specific about price levels and keep it actionable.
IMPORTANT: Start your response with a brief disclaimer: "Disclaimer: This is an AI-generated analysis and not financial advice. Always do your own research (DYOR) before making any trading decisions."
Then proceed with the analysis.
"""
        
        print(f"DEBUG: /analyze prompt for {symbol} ({interval}, {days}d, {num_analyzed_candles} candles): {prompt_text[:400]}...")

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt_text, request_options={'timeout': 60}) # Added timeout
            
            if response.text:
                return response.text.strip()
            else:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    return f"Gemini analysis for /analyze command blocked: {response.prompt_feedback.block_reason}"
                return "Gemini returned no specific pattern analysis for the /analyze command."
        except Exception as e:
            print(f"Error calling Gemini API for /analyze command: {e}")
            return f"❌ Error during pattern analysis for /analyze {symbol}. Details: {str(e)}"

    def get_gemini_forecast_analysis(self, symbol, kline_data_list, interval_used, days_of_historical_data, forecast_horizon_str):
        """
        Get price forecast, textual analysis, and a structured predicted path from Gemini API.
        Returns a tuple: (textual_analysis, predicted_path_string)
        """
        if not GEMINI_API_KEY:
            return "⚠️ Gemini forecast analysis disabled (API key missing).", None

        if not kline_data_list:
            return "No kline data provided for forecast analysis.", None

        print(f"DEBUG: Getting Gemini forecast for {symbol} using {len(kline_data_list)} kline entries. Historical: {interval_used} intervals, {days_of_historical_data} days. Forecast: {forecast_horizon_str}")
        
        date_context_info = ""
        latest_year_for_prompt = "the current year" 
        if kline_data_list:
            try:
                latest_timestamp_ms = int(kline_data_list[0][0]) 
                latest_datetime_utc = datetime.fromtimestamp(latest_timestamp_ms / 1000, tz=timezone.utc)
                current_date_for_gemini_prompt = latest_datetime_utc.strftime('%Y-%m-%d')
                latest_year_for_prompt = str(latest_datetime_utc.year)
                date_context_info = f"Context: The most recent historical data point provided is from {current_date_for_gemini_prompt} UTC. Please ensure all dates in your textual analysis are consistent with this year ({latest_year_for_prompt})."
            except Exception as e:
                print(f"Error creating date context for Gemini: {e}")
                date_context_info = "Context: Please be mindful of the current year when referencing dates."
        else: 
            date_context_info = "Context: Please be mindful of the current year when referencing dates."

        num_points_to_analyze = 150 
        recent_data_newest_first = kline_data_list[:num_points_to_analyze]
        data_to_analyze_chronological = list(reversed(recent_data_newest_first))

        formatted_kline_data = "Timestamp (ms), Open, High, Low, Close, Volume\n"
        for k_entry in data_to_analyze_chronological:
            formatted_kline_data += f"{k_entry[0]}, {k_entry[1]}, {k_entry[2]}, {k_entry[3]}, {k_entry[4]}, {k_entry[5]}\n"
        
        if len(formatted_kline_data) > 3000:
            formatted_kline_data = formatted_kline_data[:3000] + "\n... (data truncated to fit prompt)"
        
        num_prediction_points = 5 
        if forecast_horizon_str == "next 24 hours": num_prediction_points = 6 
        elif forecast_horizon_str == "next 3 days": num_prediction_points = 3 
        elif forecast_horizon_str == "next 7 days": num_prediction_points = 7

        prompt = f"""You are a cryptocurrency technical analyst.
{date_context_info}

Analyze the provided historical candlestick data for {symbol}/USDT.
The data represents {interval_used} intervals over approximately the last {days_of_historical_data} days.
Candlestick Data (Timestamp ms, Open, High, Low, Close, Volume) - Oldest to Newest from recent set:
{formatted_kline_data}

Task:
1.  Provide a textual technical analysis and price forecast for {symbol}/USDT for the {forecast_horizon_str}. Include:
    *   Overall expected price trend (e.g., bullish, bearish, sideways, volatile).
    *   Potential key support and resistance levels to watch.
    *   Significant chart patterns or technical indicators in the historical data supporting your forecast.
    *   A brief outlook.
    *   Start this textual analysis with: "🔮 AI Price Forecast for {symbol} ({forecast_horizon_str}):"
    *   Important: Your entire textual analysis, starting with '🔮 AI Price Forecast...' and ending precisely with 'TEXTUAL_ANALYSIS_END_MARKER', must be a single, continuous block of text. Do not generate any other analytical text or headers outside of this specifically marked block before you provide the PROJECTED_PATH_START block.
    *   Conclude your textual analysis with the exact marker: TEXTUAL_ANALYSIS_END_MARKER

2.  Provide a projected price path for the {forecast_horizon_str}.
    *   This path should consist of approximately {num_prediction_points} data points.
    *   Format this path strictly as follows, enclosed in markers:
        PROJECTED_PATH_START
        [timestamp_in_milliseconds, projected_price]
        [timestamp_in_milliseconds, projected_price]
        ... (repeat for {num_prediction_points} points)
        PROJECTED_PATH_END
    *   The timestamps should be in milliseconds UTC and cover the {forecast_horizon_str}, starting after the last historical data point.
    *   The projected_price should be a numerical value.

Example of PROJECTED_PATH block for a 24-hour forecast with 3 points:
PROJECTED_PATH_START
[1678886400000, 23000.50]
[1678893600000, 23150.00]
[1678900800000, 23100.75]
PROJECTED_PATH_END

Ensure the textual analysis is separate from the PROJECTED_PATH block and ends with TEXTUAL_ANALYSIS_END_MARKER.
Avoid giving specific financial advice. Focus on technicals.
When referencing specific timestamps in your analysis, please format them as YYYY-MM-DD HH:MM:SS UTC, being mindful of the current year ({latest_year_for_prompt}) based on the data provided.
"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt, request_options={'timeout': 60}) # Added timeout
            
            full_response_text = ""
            if response.text:
                full_response_text = response.text.strip()
            else:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    return f"Gemini forecast analysis blocked: {response.prompt_feedback.block_reason}", None
                return "Gemini returned no response.", None

            predicted_path_str = None
            textual_analysis_part = ""
            
            path_match = re.search(r"PROJECTED_PATH_START\s*([\s\S]*?)\s*PROJECTED_PATH_END", full_response_text)
            if path_match:
                predicted_path_str = path_match.group(0)

            text_end_marker = "TEXTUAL_ANALYSIS_END_MARKER"
            marker_pos = full_response_text.find(text_end_marker)

            if marker_pos != -1:
                textual_analysis_part = full_response_text[:marker_pos].strip()
            else: 
                if predicted_path_str:
                    textual_analysis_part = full_response_text.replace(predicted_path_str, "").strip()
                else:
                    textual_analysis_part = full_response_text
            
            expected_intro_template = f"🔮 AI Price Forecast for {symbol} ({forecast_horizon_str}):"
            # Remove any existing intro before potentially adding the correct one with request_id (done in handler)
            if textual_analysis_part.startswith(expected_intro_template):
                 textual_analysis_part = textual_analysis_part[len(expected_intro_template):].strip()
            # Fallback if textual_analysis_part is empty or only whitespace after processing
            if not textual_analysis_part.strip():
                if predicted_path_str:
                    textual_analysis_part = "_AI provided a projected path but minimal textual analysis._"
                else:
                    textual_analysis_part = "_AI could not provide a detailed forecast or path at this time._"
            
            return textual_analysis_part, predicted_path_str

        except Exception as e:
            print(f"Error calling Gemini API for forecast analysis: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error during forecast analysis for {symbol}. Details: {str(e)}", None

    def create_prediction_chart(self, symbol, historical_kline_data, predicted_data_str, hist_interval, hist_days, forecast_horizon_str):
        if not historical_kline_data:
            print(f"DEBUG: No historical kline data for {symbol} in create_prediction_chart.")
            return None
        try:
            df_hist_data = [{'timestamp': int(c[0]), 'open': float(c[1]), 'high': float(c[2]), 
                             'low': float(c[3]), 'close': float(c[4]), 'volume': float(c[5])}
                            for c in reversed(historical_kline_data)]
            df_hist = pd.DataFrame(df_hist_data)
            df_hist['datetime'] = pd.to_datetime(df_hist['timestamp'], unit='ms')
            if df_hist.empty: return None

            df_pred = pd.DataFrame()
            if predicted_data_str:
                match = re.search(r"PROJECTED_PATH_START\s*([\s\S]*?)\s*PROJECTED_PATH_END", predicted_data_str)
                if match:
                    path_block = match.group(1)
                    raw_prices = re.findall(r"\[\s*\d+\s*,\s*([\d\.]+)\s*\]", path_block)
                    parsed_prices = [float(p) for p in raw_prices]

                    if parsed_prices:
                        num_expected_points = 0
                        time_delta_per_point = pd.Timedelta(days=1) 

                        if forecast_horizon_str == "next 7 days":
                            num_expected_points = 7
                            time_delta_per_point = pd.Timedelta(days=1)
                        elif forecast_horizon_str == "next 3 days":
                            num_expected_points = 3
                            time_delta_per_point = pd.Timedelta(days=1)
                        elif forecast_horizon_str == "next 24 hours" or forecast_horizon_str == "next 1 day": 
                            num_expected_points = 6 
                            time_delta_per_point = pd.Timedelta(hours=4)
                        
                        prices_to_plot = parsed_prices[:num_expected_points]
                        
                        if prices_to_plot:
                            last_hist_dt = df_hist['datetime'].iloc[-1]
                            future_timestamps = [last_hist_dt + time_delta_per_point * (i+1) for i in range(len(prices_to_plot))]
                            
                            df_pred = pd.DataFrame({
                                'datetime': future_timestamps,
                                'price': prices_to_plot
                            })
                            print(f"DEBUG: Created df_pred with {len(df_pred)} corrected future points for {symbol}.")
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
            fig.patch.set_facecolor('#0a0a0a')

            w_factor = {'1h': 1, '4h': 4, '1d': 24}.get(hist_interval, 1)
            candle_w = 0.0003 * w_factor
            vol_w = 0.0008 * w_factor

            for _, row in df_hist.iterrows():
                color = '#00ff88' if row['close'] >= row['open'] else '#ff4757'
                ax1.plot([row['datetime'], row['datetime']], [row['low'], row['high']], color=color, lw=1, alpha=0.8)
                ax1.add_patch(Rectangle((mdates.date2num(row['datetime']) - candle_w, min(row['open'], row['close'])), candle_w * 2, abs(row['close'] - row['open']), fc=color, alpha=0.8, ec=color))
            ax1.plot(df_hist['datetime'], df_hist['close'], color='#ffa502', lw=1.5, alpha=0.7, label='Historical Close')

            if not df_pred.empty and not df_hist.empty:
                last_hist_dt, last_hist_close = df_hist['datetime'].iloc[-1], df_hist['close'].iloc[-1]
                first_pred_row = pd.DataFrame([{'datetime': last_hist_dt, 'price': last_hist_close}])
                df_pred_plot = pd.concat([first_pred_row, df_pred], ignore_index=True)
                ax1.plot(df_pred_plot['datetime'], df_pred_plot['price'], color='#4169E1', ls='--', marker='o', ms=3, lw=2, label=f'Predicted Path ({forecast_horizon_str.title()})')

            ax1.set_facecolor('#0a0a0a'); ax1.grid(True, alpha=0.3, color='#333333')
            ax1.set_title(f'{symbol}/USDT Price Forecast ({forecast_horizon_str.title()})', color='#ffffff', fontsize=16, fontweight='bold', pad=20)
            ax1.set_ylabel('Price (USDT)', color='#ffffff', fontsize=12)
            ax1.tick_params(axis='both', colors='#ffffff'); ax1.legend(facecolor='#1c1c1c', edgecolor='#333333', labelcolor='#ffffff', fontsize='small')

            all_prices = pd.concat([df_hist['high'], df_hist['low'], df_pred['price'] if not df_pred.empty else pd.Series(dtype=float)])
            p_min, p_max = all_prices.min(), all_prices.max()
            p_range = (p_max - p_min) if pd.notna(p_min) and pd.notna(p_max) else (p_min * 0.1 if pd.notna(p_min) else 0.1)
            if p_range == 0 : p_range = p_min * 0.1 if pd.notna(p_min) and p_min > 0 else 0.1

            if p_range < 1 and p_range !=0: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.6f}'))
            elif p_range < 100 and p_range !=0: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.4f}'))
            else: ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.2f}'))

            ax2.bar(df_hist['datetime'], df_hist['volume'], color=['#00ff88' if c >= o else '#ff4757' for o, c in zip(df_hist['open'], df_hist['close'])], alpha=0.6, width=vol_w)
            ax2.set_facecolor('#0a0a0a'); ax2.grid(True, alpha=0.3, color='#333333')
            ax2.set_ylabel('Volume', color='#ffffff', fontsize=12)
            ax2.tick_params(axis='both', colors='#ffffff')
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1e3:.0f}K' if x < 1e6 else f'{x/1e6:.1f}M'))

            all_dt = pd.concat([df_hist['datetime'], df_pred['datetime'] if not df_pred.empty else pd.Series(dtype='datetime64[ns]')]).dropna()
            min_dt, max_dt = all_dt.min(), all_dt.max()
            
            fmt_str = '%m/%d %H:%M'
            if hist_interval == '1d' or ('days' in forecast_horizon_str and int(re.search(r'\d+', forecast_horizon_str).group()) >= 3): fmt_str = '%m/%d'
            if hist_interval == '1d' and ('days' in forecast_horizon_str and int(re.search(r'\d+', forecast_horizon_str).group()) >= 30): fmt_str = '%Y-%m-%d'

            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt_str))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
                if pd.notna(min_dt) and pd.notna(max_dt):
                    pad = pd.Timedelta(hours=1*w_factor)
                    ax.set_xlim([min_dt - pad, max_dt + pad])
            
            last_h_close = df_hist['close'].iloc[-1]
            h_change = (last_h_close - df_hist['close'].iloc[0]) / df_hist['close'].iloc[0] * 100 if len(df_hist['close']) > 1 and df_hist['close'].iloc[0] != 0 else 0
            fig.suptitle(f'Last Hist: ${last_h_close:.6f} | Hist Change: {h_change:+.2f}% ({hist_days}d)', color='#ffffff', fontsize=10, y=0.025)
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.subplots_adjust(top=0.93, bottom=0.15)
            buf = io.BytesIO(); plt.savefig(buf, format='png', facecolor='#0a0a0a', dpi=150, bbox_inches='tight'); plt.close(fig)
            prediction_plotted_successfully = True if 'df_pred_plot' in locals() and not df_pred_plot.empty else False
            return base64.b64encode(buf.getvalue()).decode(), prediction_plotted_successfully
        except Exception as e:
            print(f"Error in create_prediction_chart for {symbol}: {e}"); import traceback; traceback.print_exc(); return None, False

    def handle_predict_command(self, chat_id, text):
        request_id = str(uuid.uuid4())[:8] 
        if not GEMINI_API_KEY:
            self.send_message(chat_id, f"[{request_id}] ⚠️ Gemini API not configured. Prediction feature is unavailable.")
            return

        parts = text.split()
        if len(parts) < 2:
            self.send_message(chat_id, f"[{request_id}] 🔮 **AI Price Forecast Usage:**\n`/predict <symbol> [period]`\n"
                                       "Periods: `24h`, `1d` (default), `3d`, `7d`\n"
                                       "Example: `/predict BTC 3d`")
            return

        symbol = self.normalize_symbol(parts[1])
        forecast_period_arg = parts[2].lower() if len(parts) > 2 else "1d"
        valid_periods = {"24h": "next 24 hours", "1d": "next 1 day", "3d": "next 3 days", "7d": "next 7 days"}
        if forecast_period_arg not in valid_periods:
            self.send_message(chat_id, f"[{request_id}] ❌ Invalid period. Use: {', '.join(valid_periods.keys())}"); return
        
        forecast_horizon_str = valid_periods[forecast_period_arg]
        hist_config = {
            "24h": {'interval': '1h', 'days': 7}, "1d": {'interval': '1h', 'days': 7},
            "3d": {'interval': '4h', 'days': 21}, "7d": {'interval': '1d', 'days': 60}
        }
        hist_interval = hist_config[forecast_period_arg]['interval']
        hist_days = hist_config[forecast_period_arg]['days']
        hist_limit = min({'1h': hist_days*24, '4h': hist_days*6, '1d': hist_days}.get(hist_interval,150), 200)

        loading_msg_response = self.send_message(chat_id, f"🔮 [{request_id}] Generating AI forecast for {symbol} ({forecast_horizon_str})...\nFetching historical data...")
        message_id_to_edit = loading_msg_response['result']['message_id'] if loading_msg_response and loading_msg_response.get('ok') else None

        historical_kline = self.get_kline_data(symbol, hist_interval, hist_limit)
        if not historical_kline or len(historical_kline) < 10:
            err_msg = f"[{request_id}] ❌ Insufficient historical data for {symbol} ({len(historical_kline or [])} candles)."
            if message_id_to_edit: self.edit_message(chat_id, message_id_to_edit, err_msg)
            else: self.send_message(chat_id, err_msg)
            return

        if message_id_to_edit: self.edit_message(chat_id, message_id_to_edit, f"🔮 [{request_id}] Analyzing data for {symbol} with Gemini AI...")
        
        textual_analysis, predicted_path_str = self.get_gemini_forecast_analysis(symbol, historical_kline, hist_interval, hist_days, forecast_horizon_str)

        default_intro = f"🔮 [{request_id}] AI Price Forecast for {symbol} ({forecast_horizon_str}):"
        
        known_status_messages = [
            "⚠️ Gemini forecast analysis disabled (API key missing).",
            "No kline data provided for forecast analysis.",
            "Gemini returned no response.",
            "Gemini returned no specific forecast analysis or path."
        ]
        is_status_message = any(status_msg in textual_analysis for status_msg in known_status_messages) or \
                            textual_analysis.startswith("❌ Error during forecast analysis") or \
                            textual_analysis.startswith("Gemini forecast analysis blocked:")

        if not is_status_message:
            if textual_analysis.strip(): # If there's actual analysis text (already stripped of generic intro by get_gemini_forecast_analysis)
                 textual_analysis = default_intro + "\n" + textual_analysis
            else: # If textual_analysis became empty (e.g. only path was provided or error in parsing)
                textual_analysis = default_intro + "\n_(No detailed textual analysis provided by AI.)_"
        else:
            if not textual_analysis.startswith(f"[{request_id}]"):
                 textual_analysis = f"[{request_id}] {textual_analysis}"


        img_b64, prediction_plotted = self.create_prediction_chart(symbol, historical_kline, predicted_path_str, hist_interval, hist_days, forecast_horizon_str)
        
        base_caption = textual_analysis
        status_note = ""
        ellipsis = "\n_(...text truncated)_"
        note_max_len = 1024 

        if img_b64 and predicted_path_str and not prediction_plotted:
             status_note = "\n\n_(Note: AI provided path data, but it could not be visualized. Showing historical data.)_"
        elif img_b64 and not predicted_path_str:
             status_note = "\n\n_(Note: AI did not provide path data for plotting. Showing historical data.)_"
        elif not img_b64:
             status_note = "\n\n⚠️ Chart generation failed."
             note_max_len = 4096


        # Smart truncation
        if len(base_caption) + len(status_note) > note_max_len:
            available_for_base = note_max_len - len(status_note) - len(ellipsis)
            if available_for_base > 0:
                caption = base_caption[:available_for_base] + ellipsis + status_note
            else: 
                caption = status_note
                if len(caption) > note_max_len: 
                     caption = status_note[:note_max_len - len(ellipsis)] + ellipsis
        else:
            caption = base_caption + status_note
        
        if img_b64:
            self.send_photo(chat_id, img_b64, caption)
            if message_id_to_edit:
                try:
                    requests.post(f"{self.telegram_api}/deleteMessage", data={'chat_id': chat_id, 'message_id': message_id_to_edit}, timeout=5)
                except Exception as e:
                    print(f"Error deleting message: {e}")
        else:
            if message_id_to_edit: self.edit_message(chat_id, message_id_to_edit, caption)
            else: self.send_message(chat_id, caption)

    def send_photo(self, chat_id, photo_data, caption="", reply_markup=None):
        url = f"{self.telegram_api}/sendPhoto"
        files = {'photo': ('chart.png', base64.b64decode(photo_data), 'image/png')}
        data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
        if reply_markup: data['reply_markup'] = json.dumps(reply_markup)
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.json()
        except Exception as e:
            print(f"Error sending photo: {e}")
        return None

    def get_public_price(self, symbol):
        url = f"{self.base_url}/v5/market/tickers"
        params = {"category": "spot", "symbol": f"{symbol}USDT"}
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_coin_price(self, symbol):
        original_symbol = symbol
        symbol = self.normalize_symbol(symbol)
        result = self.get_public_price(symbol)
        if result.get('retCode') == 0 and result.get('result', {}).get('list'):
            ticker = result['result']['list'][0]
            return {
                'symbol': ticker.get('symbol', ''), 'base_symbol': symbol,
                'price': float(ticker.get('lastPrice', 0)),
                'change24h': float(ticker.get('price24hPcnt', 0)) * 100,
                'volume24h': float(ticker.get('volume24h', 0)),
                'high24h': float(ticker.get('highPrice24h', 0)),
                'low24h': float(ticker.get('lowPrice24h', 0)),
                'bid': float(ticker.get('bid1Price', 0)),
                'ask': float(ticker.get('ask1Price', 0))
            }
        else:
            matches = self.find_matching_symbols(original_symbol)
            return {'matches': matches, 'original_query': original_symbol}

    def send_chart(self, chat_id, symbol, interval='1h', days=7, message_id=None):
        loading_msg = f"📊 Generating {symbol} chart..."
        if message_id: self.edit_message(chat_id, message_id, loading_msg)
        else:
            result = self.send_message(chat_id, loading_msg)
            if result and result.get('ok'): message_id = result['result']['message_id']
        
        chart_result = self.create_price_chart(symbol, interval, days)
        
        if chart_result and chart_result.get('image'):
            image_base64 = chart_result['image']
            actual_interval_used = chart_result['interval_used']
            actual_days_used = chart_result['days_used']
            pattern_analysis = chart_result.get('pattern_analysis') 

            price_data = self.get_coin_price(symbol)
            caption = f"📊 **{symbol}/USDT Chart**"
            if price_data and 'price' in price_data:
                price = price_data['price']; change_24h = price_data['change24h']
                emoji = "📈" if change_24h >= 0 else "📉"
                caption += f"\n\n💰 **Price:** ${price:,.6f}\n{emoji} **24h:** {change_24h:+.2f}%"
            
            caption += f"\n\n**Period:** {actual_days_used} days ({actual_interval_used} intervals)\n**Generated:** {datetime.now().strftime('%H:%M:%S UTC')}"

            print(f"DEBUG send_chart: pattern_analysis content before check: '{pattern_analysis}'")

            if pattern_analysis and pattern_analysis != "Pattern analysis not available.":
                max_analysis_text_len = 700
                ellipsis = "\n_(...analysis truncated)_"
                
                if len(pattern_analysis) > max_analysis_text_len:
                    pattern_analysis = pattern_analysis[:max_analysis_text_len - len(ellipsis)] + ellipsis
                
                caption += f"\n\n🧠 **AI Pattern Insights:**\n_{pattern_analysis}_"
            else:
                print(f"DEBUG send_chart: Pattern analysis not appended. Value was: '{pattern_analysis}'")

            keyboard = {"inline_keyboard": [
                [{"text": "1H", "callback_data": f"chart_{symbol}_1h_3"},
                 {"text": "4H", "callback_data": f"chart_{symbol}_4h_7"},
                 {"text": "1D", "callback_data": f"chart_{symbol}_1d_30"}],
                [{"text": "💰 Price", "callback_data": f"price_{symbol}"},
                 {"text": "🔄 Refresh", "callback_data": f"chart_{symbol}_{actual_interval_used}_{actual_days_used}"}]
            ]}
            self.send_photo(chat_id, image_base64, caption, keyboard)
            if message_id:
                try: requests.post(f"{self.telegram_api}/deleteMessage", data={'chat_id': chat_id, 'message_id': message_id}, timeout=5)
                except: pass
        else:
            error_msg = f"❌ **Failed to generate chart for {symbol}**\n\nThis could be due to:\n• Insufficient/invalid data for selected period\n• Network issues or API rate limits\n• Invalid symbol\n\nTry a different period or symbol."
            if message_id: self.edit_message(chat_id, message_id, error_msg)
            else: self.send_message(chat_id, error_msg)

    def send_message(self, chat_id, text, reply_markup=None, parse_mode='Markdown'):
        url = f"{self.telegram_api}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup: data['reply_markup'] = json.dumps(reply_markup)
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
        return None

    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode='Markdown'):
        url = f"{self.telegram_api}/editMessageText"
        data = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup: data['reply_markup'] = json.dumps(reply_markup)
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error editing message: {e}")
        return None

    def answer_callback_query(self, callback_query_id, text=""):
        url = f"{self.telegram_api}/answerCallbackQuery"
        data = {'callback_query_id': callback_query_id, 'text': text}
        try: requests.post(url, data=data, timeout=5)
        except Exception as e: print(f"Error answering callback: {e}")

    def create_popular_keyboard(self, start=0, per_page=9):
        keyboard, row = [], []
        coins_to_show = self.popular_coins[start:start + per_page]
        for coin in coins_to_show:
            row.append({"text": f"💰 {coin}", "callback_data": f"price_{coin}"})
            if len(row) == 3: keyboard.append(row); row = []
        if row: keyboard.append(row)
        nav_row = []
        if start > 0: nav_row.append({"text": "⬅️ Previous", "callback_data": f"nav_{start-per_page}"})
        if start + per_page < len(self.popular_coins): nav_row.append({"text": "➡️ Next", "callback_data": f"nav_{start+per_page}"})
        if nav_row: keyboard.append(nav_row)
        keyboard.append([{"text": "🔍 Search Any Coin", "callback_data": "search_help"}])
        return {"inline_keyboard": keyboard}

    def create_suggestions_keyboard(self, matches, original_query):
        keyboard, row = [], []
        for match in matches[:9]:
            row.append({"text": f"💰 {match}", "callback_data": f"price_{match}"})
            if len(row) == 3: keyboard.append(row); row = []
        if row: keyboard.append(row)
        return {"inline_keyboard": keyboard}

    def handle_start(self, chat_id, user_name=""):
        welcome_message = f"""
🚀 **Welcome to Universal Crypto Price Bot!**

Hello {user_name}! I can help you check prices for ANY cryptocurrency on Bybit exchange.

**Quick Commands:**
• `/price BTC` - Get Bitcoin price
• `/chart ETH` - Get Ethereum chart (now with AI pattern insights!)
• `/analyze BTC 4h 7` - Get detailed AI chart pattern analysis for Bitcoin.
• `/predict SOL 3d` - Get AI price forecast for Solana for the next 3 days.
• `/popular` - Show popular coins
• `/search doge` - Search for coins
• `/help` - Show all commands

**Super Easy Search:**
Just type ANY coin name or symbol:
• `bitcoin` or `BTC`
• `ethereum` or `ETH` 
• `dogecoin` or `DOGE`

I'll find it for you! 🔍📊📈
        """
        self.send_message(chat_id, welcome_message, self.create_popular_keyboard())

    def handle_help(self, chat_id):
        """Handle /help command"""
        help_text = """🔍 **How to use this Enhanced Crypto Bot:**

**🎯 Quick Price Check:**
• Just type: `BTC`, `bitcoin`, `ETHEREUM`, `doge`
• Works with full names or symbols!

**📊 Chart Commands:**
• `/chart BTC` - Bitcoin chart (default 1h, 3 days). Includes AI pattern insights in caption.
• `/chart ETH 4h` - Ethereum 4-hour chart (default 7 days). Includes AI pattern insights.
• `/chart DOGE 1d 30` - Dogecoin daily chart (30 days). Includes AI pattern insights.

**🤖 AI Chart Pattern Analysis (`/analyze` command):**
• Usage: `/analyze <symbol> [interval] [days]`
  • Example: `/analyze ETH 1h 3` (Analyzes Ethereum on 1-hour chart, using data from last 3 days to identify recent patterns from ~20 candles)
  • Example: `/analyze DOGE 4h` (Analyzes Dogecoin on 4-hour chart, default 7 days context)
  • Example: `/analyze SOL` (Analyzes Solana on 4-hour chart, default 7 days context)
• Provides: Identified patterns, trend, breakout levels, and pattern-based trading ideas.
• Data: Based on the most recent ~20 candles from the specified period context.
• Disclaimer: AI-generated, not financial advice. Always DYOR.

**🔮 AI Price Forecast (`/predict` command):**
• Usage: `/predict <symbol> [period]`
  • Example: `/predict BTC` (Forecast for Bitcoin, default 1 day, shows predicted path on chart)
  • Example: `/predict ETH 24h` (Forecast for Ethereum, next 24 hours, with predicted path)
  • Example: `/predict ADA 3d` (Forecast for Cardano, next 3 days, with predicted path)
  • Example: `/predict DOT 7d` (Forecast for Polkadot, next 7 days, with predicted path)
• Provides: A chart showing historical data with an overlaid AI-generated predicted price path, plus textual analysis.
• Periods: `24h`, `1d` (default), `3d`, `7d`.

**📝 Other Commands:**
• `/price <coin>` - Get specific price
• `/search <query>` - Search for coins
• `/popular` - Popular coins menu
• `/list` - Info on available trading pairs

**📊 Chart Intervals (for `/chart`, `/analyze`, and historical part of `/predict`):**
• `1h` - Hourly
• `4h` - 4-hour 
• `1d` - Daily

**🪙 Supported Formats:**
• Symbol: `BTC`, `ETH`, `XRP`
• Full name: `bitcoin`, `ethereum`, `ripple`

**📊 Chart Features (for `/chart` command):**
• 🕯️ Candlestick price display & Volume bars
• 🧠 **AI Pattern Insights in Caption:** Automated detection of common technical patterns.
• 📱 Interactive timeframe buttons

**Data Source:** Bybit Exchange API"""
        self.send_message(chat_id, help_text)

    def handle_analyze_command(self, chat_id, text):
        """Handles the /analyze command for dedicated chart pattern analysis."""
        request_id = str(uuid.uuid4())[:8] # Unique ID for this request
        if not GEMINI_API_KEY:
            self.send_message(chat_id, f"[{request_id}] ⚠️ Gemini API not configured. Analysis feature is unavailable.")
            return

        parts = text.split() 
        
        if len(parts) < 2: 
            self.send_message(chat_id, f"[{request_id}] 🧠 **AI Chart Pattern Analysis Usage:**\n"
                                       "`/analyze <symbol> [interval] [days]`\n\n"
                                       "**Examples:**\n"
                                       "• `/analyze BTC` (default: 4h interval, 7 days context)\n"
                                       "• `/analyze ETH 1h` (1h interval, default: 7 days context)\n"
                                       "• `/analyze SOL 1d 30` (daily interval, 30 days context)\n\n"
                                       "**Intervals:** `1h`, `4h`, `1d`.\n"
                                       "**Days (context):** Number of days of data (1-90). Analysis focuses on recent ~20 candles from this period.")
            return

        symbol = parts[1].upper()
        interval = '4h' 
        days = 7          

        if len(parts) > 2:
            if parts[2].lower() in ['1h', '4h', '1d']:
                interval = parts[2].lower()
                if len(parts) > 3 and parts[3].isdigit():
                    days = int(parts[3])
            elif parts[2].isdigit():
                days = int(parts[2])
                if len(parts) > 3 and parts[3].lower() in ['1h', '4h', '1d']:
                    interval = parts[3].lower()
        
        if interval not in ['1h', '4h', '1d']:
            self.send_message(chat_id, f"[{request_id}] ❌ Invalid interval: `{interval}`. Use: `1h`, `4h`, or `1d`."); return
        if not (1 <= days <= 90): 
            self.send_message(chat_id, f"[{request_id}] ❌ Days (for context) must be between 1 and 90. You entered: {days}"); return

        loading_msg_text = f"🧠 [{request_id}] Analyzing chart patterns for {symbol} ({interval}, {days}d context)... This may take a moment."
        sent_message_info = self.send_message(chat_id, loading_msg_text)
        message_id_to_edit = None
        if sent_message_info and sent_message_info.get('ok'):
            message_id_to_edit = sent_message_info['result']['message_id']

        analysis_result = self.get_dedicated_chart_pattern_analysis_for_analyze_command(symbol, interval, days)
        
        final_message_body = analysis_result
        # Ensure the disclaimer is there if it's a successful analysis
        disclaimer = "Disclaimer: This is an AI-generated analysis and not financial advice."
        if "Error" not in analysis_result and "blocked" not in analysis_result and "Insufficient" not in analysis_result and disclaimer not in analysis_result :
             final_message_body = f"{disclaimer}\n\n{analysis_result}"


        max_telegram_message_len = 4000 
        ellipsis = "\n\n_(...analysis truncated due to length)_"
        if len(final_message_body) > max_telegram_message_len:
            final_message_body = final_message_body[:max_telegram_message_len - len(ellipsis)] + ellipsis
        
        final_message = f"🔍 [{request_id}] **{symbol} ({interval}, {days}d context) - AI Chart Pattern Analysis:**\n\n{final_message_body}"

        edited_successfully = False
        if message_id_to_edit:
            edit_response = self.edit_message(chat_id, message_id_to_edit, final_message)
            if edit_response and edit_response.get('ok'):
                edited_successfully = True
        
        if not edited_successfully:
            send_response = self.send_message(chat_id, final_message)
            if not send_response or not send_response.get('ok'):
                self.send_message(chat_id, f"[{request_id}] ❌ Sorry, there was an issue displaying the analysis for {symbol}. Please try again later.")


    def handle_popular(self, chat_id):
        self.send_message(chat_id, "📈 **Popular Cryptocurrencies**\n\nClick on any coin to get its current price, or type any coin name to search:", self.create_popular_keyboard())

    def handle_chart_command(self, chat_id, text):
        parts = text.split()
        if len(parts) < 2:
            self.send_message(chat_id, "📊 **Chart Usage:**\n\n"
                "• `/chart BTC` - Bitcoin chart (1h, 3 days default)\n"
                "• `/chart ETH 4h` - Ethereum (4h intervals, 7 days default)\n"
                "• `/chart DOGE 1d 30` - Dogecoin (daily, 30 days)\n\n"
                "Charts now include **AI-powered pattern insights** in the caption!\n\n"
                "**Intervals:** `1h`, `4h`, `1d`\n"
                "**Days:** Any number (1-365)")
            return
        symbol = parts[1].upper()
        interval = '1h' 
        days = 3 
        if len(parts) > 2:
            if parts[2].lower() in ['1h', '4h', '1d']:
                interval = parts[2].lower()
                if interval == '1h': days = 3
                elif interval == '4h': days = 7
                elif interval == '1d': days = 30
                
                if len(parts) > 3 and parts[3].isdigit():
                    days = int(parts[3])
            elif parts[2].isdigit(): 
                 days = int(parts[2])
        
        if interval == '4h' and len(parts) <= 3 : days = 7 
        if interval == '1d' and len(parts) <= 3 : days = 30 


        if interval not in ['1h', '4h', '1d']:
            self.send_message(chat_id, "❌ Invalid interval. Use: `1h`, `4h`, or `1d`."); return
        if not (1 <= days <= 365):
            self.send_message(chat_id, "❌ Days must be between 1 and 365"); return
        self.send_chart(chat_id, symbol, interval, days)

    def handle_search(self, chat_id, query):
        if not query: self.send_message(chat_id, "🔍 **Search Usage:**\n\n`/search bitcoin`\n`/search doge`\n`/search shiba`\n\nOr just type the coin name directly!"); return
        matches = self.find_matching_symbols(query)
        if matches:
            if len(matches) == 1: self.send_price_info(chat_id, matches[0])
            else: self.send_message(chat_id, f"🔍 **Search Results for '{query}':**\n\nFound {len(matches)} matching coins. Click to get price:", self.create_suggestions_keyboard(matches, query))
        else: self.send_message(chat_id, f"❌ **No matches found for '{query}'**\n\n🔍 **Search Tips:**\n• Try the symbol: `BTC`, `ETH`, `DOGE`\n• Try the full name: `bitcoin`, `ethereum`\n• Check spelling\n• Use `/popular` to see available coins")

    def handle_price_command(self, chat_id, text):
        parts = text.split()
        if len(parts) < 2: self.send_message(chat_id, "❌ Please specify a coin.\n\n**Examples:**\n• `/price BTC`\n• `/price ethereum`\n• `/price dogecoin`"); return
        self.send_price_info(chat_id, " ".join(parts[1:]))

    def handle_text_message(self, chat_id, text):
        text = text.strip()
        if 2 <= len(text) <= 50: self.send_price_info(chat_id, text)
        else: self.send_message(chat_id, "🤔 **I can help you check crypto prices!**\n\n"
                "**Try these:**\n"
                "• `BTC` or `bitcoin`\n"
                "• `ETH` or `ethereum`\n"
                "• `DOGE` or `dogecoin`\n"
                "• `/help` - for more options\n"
                "• `/popular` - popular coins menu")

    def send_price_info(self, chat_id, symbol, message_id=None):
        loading_msg = f"🔄 Searching for **{symbol}**..."
        if message_id: self.edit_message(chat_id, message_id, loading_msg)
        else:
            result = self.send_message(chat_id, loading_msg)
            if result and result.get('ok'): message_id = result['result']['message_id']
        
        price_data = self.get_coin_price(symbol)
        if price_data and 'price' in price_data:
            price = price_data['price']; change_24h = price_data['change24h']
            volume_24h = price_data['volume24h']; high_24h = price_data['high24h']; low_24h = price_data['low24h']
            bid = price_data.get('bid',0); ask = price_data.get('ask',0); base_symbol = price_data['base_symbol']
            change_emoji = "🚀" if change_24h >=5 else "📈" if change_24h >=0 else "📉" if change_24h >= -5 else "💥"
            change_color = "🟢" if change_24h >=0 else "🔴"
            price_str = f"${price:,.4f}" if price >=1 else f"${price:.8f}"
            spread = ((ask - bid) / price * 100) if price > 0 and bid > 0 and ask > 0 else 0
            price_text = f"🪙 **{base_symbol}/USDT** Price\n\n💰 **Current Price:** {price_str}\n{change_emoji} **24h Change:** {change_color} {change_24h:+.2f}%\n\n📊 **24h Trading Data:**\n• **Volume:** ${volume_24h:,.0f}\n• **High:** ${high_24h:,.6f}\n• **Low:** ${low_24h:,.6f}\n\n💹 **Order Book:**\n• **Bid:** ${bid:.6f}\n• **Ask:** ${ask:.6f}\n• **Spread:** {spread:.3f}%\n\n🕒 **Updated:** {datetime.now().strftime('%H:%M:%S UTC')}\n📊 **Source:** Bybit Exchange"
            keyboard = {"inline_keyboard": [[{"text": "🔄 Refresh", "callback_data": f"price_{base_symbol}"}, {"text": "📈 Chart", "callback_data": f"chart_{base_symbol}"}],[{"text": "🔍 Search More", "callback_data": "search_help"}]]}
            if message_id: self.edit_message(chat_id, message_id, price_text, keyboard)
            else: self.send_message(chat_id, price_text, keyboard)
        elif price_data and 'matches' in price_data:
            matches = price_data['matches']; original_query = price_data['original_query']
            if matches:
                keyboard = self.create_suggestions_keyboard(matches, original_query)
                suggestion_text = f"🔍 **'{original_query}' not found exactly.**\n\n**Did you mean one of these?**\nClick to get price:"
                if message_id: self.edit_message(chat_id, message_id, suggestion_text, keyboard)
                else: self.send_message(chat_id, suggestion_text, keyboard)
            else:
                error_msg = f"❌ **Sorry, '{original_query}' not found.**\n\n🔍 **Try:**\n• Check spelling\n• Use symbol (BTC, ETH)\n• Use full name (bitcoin, ethereum)\n• `/popular` for popular coins"
                if message_id: self.edit_message(chat_id, message_id, error_msg)
                else: self.send_message(chat_id, error_msg)
        else:
            error_msg = f"❌ **Error getting price for '{symbol}'**\n\n🔍 **Troubleshooting:**\n• Check your internet connection\n• Try again in a moment\n• Use `/popular` for verified coins"
            if message_id: self.edit_message(chat_id, message_id, error_msg)
            else: self.send_message(chat_id, error_msg)

    def handle_callback_query(self, callback_query):
        query_id = callback_query['id']; data = callback_query['data']
        chat_id = callback_query['message']['chat']['id']; message_id = callback_query['message']['message_id']
        self.answer_callback_query(query_id)
        if data.startswith("price_"): self.send_price_info(chat_id, data.replace("price_", ""), message_id)
        elif data.startswith("nav_"): self.edit_message(chat_id, message_id, "📈 **Popular Cryptocurrencies**\n\nClick on any coin to get its current price, or type any coin name to search:", self.create_popular_keyboard(int(data.replace("nav_", ""))))
        elif data == "search_help": self.edit_message(chat_id, message_id, "🔍 **How to Search for Any Coin:**\n\n"
                "**Just type the coin name or symbol:**\n"
                "• `bitcoin` or `BTC`\n"
                "• `ethereum` or `ETH`\n"
                "• `dogecoin` or `DOGE`\n"
                "• `shiba inu` or `SHIB`\n\n"
                "**Or use commands:**\n"
                "• `/search <coin name>`\n"
                "• `/price <coin>`\n\n"
                "I support 1000+ cryptocurrencies! 🚀")
        elif data.startswith("chart_"):
            parts = data.replace("chart_", "").split("_")
            symbol = parts[0]; interval = parts[1] if len(parts) > 1 else '1h'
            days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 7 # Default days for chart callback
            self.send_chart(chat_id, symbol, interval, days)

    def process_update(self, update):
        try:
            if 'message' in update:
                message = update['message']; chat_id = message['chat']['id']
                if 'text' in message:
                    text = message['text']; user_name = message['from'].get('first_name', '')
                    if text.startswith('/start'): self.handle_start(chat_id, user_name)
                    elif text.startswith('/help'): self.handle_help(chat_id)
                    elif text.startswith('/popular'): self.handle_popular(chat_id)
                    elif text.startswith('/price'): self.handle_price_command(chat_id, text)
                    elif text.startswith('/chart'): self.handle_chart_command(chat_id, text)
                    elif text.startswith('/predict') or text.startswith('/pedict'): # Handle common misspelling
                        # If misspelled, replace /pedict with /predict before passing to handler
                        corrected_text = text.replace('/pedict', '/predict') if text.startswith('/pedict') else text
                        self.handle_predict_command(chat_id, corrected_text)
                    elif text.startswith('/analyze'): self.handle_analyze_command(chat_id, text)
                    elif text.startswith('/search'): self.handle_search(chat_id, text.replace('/search', '').strip())
                    elif text.startswith('/list'): self.send_message(chat_id, f"📊 **Available Coins:** {len(self.supported_symbols_cache)} trading pairs\n\nJust type any coin name to check its price! Popular ones include: BTC, ETH, XRP, ADA, DOT, LINK, LTC, BCH, UNI, SOL, MATIC, AVAX, ATOM, DOGE, SHIB, TRX, NEAR, FTM, etc.")
                    else: self.handle_text_message(chat_id, text)
            elif 'callback_query' in update: self.handle_callback_query(update['callback_query'])
        except Exception as e: print(f"Error processing update: {e}")

    def get_updates(self):
        url = f"{self.telegram_api}/getUpdates"
        params = {'offset': self.offset, 'timeout': 10, 'limit': 100}
        try:
            response = requests.get(url, params=params, timeout=15)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting updates: {e}")
        return None

    def run(self):
        print("🤖 Enhanced Crypto Price Bot is starting...")
        print(f"📱 Telegram Bot Token: {self.telegram_token[:10]}...")
        print(f"🔑 Bybit API Key: {self.api_key[:8]}...")
        self.update_symbols_cache()
        print("✅ Bot is ready! Send /start to any chat to begin.")
        print("🌟 Enhanced features: Universal coin search, smart suggestions, fuzzy matching, chart fallback, /analyze command.")
        while True:
            try:
                updates = self.get_updates()
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.process_update(update)
                        self.offset = update['update_id'] + 1
                time.sleep(1)
            except KeyboardInterrupt: print("\n🛑 Bot stopped by user"); break
            except Exception as e: print(f"Error in main loop: {e}"); time.sleep(5)

def main():
    TELEGRAM_BOT_TOKEN = "replace TELEGRAM_BOT_TOKEN"
    BYBIT_API_KEY = "replace BYBIT_API_KEY"
    BYBIT_API_SECRET = "replace BYBIT_API_SECRET"
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Error: Please set your Telegram Bot Token!"); return
    bot = BybitCryptoBotEnhanced(TELEGRAM_BOT_TOKEN, BYBIT_API_KEY, BYBIT_API_SECRET)
    bot.run()

if __name__ == "__main__":
    main()
