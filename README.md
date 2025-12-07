# 🔬 MarketLens: Global Market Comparator

**MarketLens** is a professional-grade financial analytics dashboard built with **Streamlit**. It allows investors to compare global indices, analyze stock performance within specific countries using live data, and conduct deep-dive technical analysis with interactive charts.

---

## 🚀 Live Demo
**https://market-lens-app.streamlit.app/**
<img width="1875" height="750" alt="image" src="https://github.com/user-attachments/assets/35546655-b1ea-4f84-8d45-ebefe6276667" />

---

## 🌟 Key Features

### 1. 🌍 Global Market Comparison
* Compare major indices (Nifty 50, S&P 500, DAX, FTSE 100) side-by-side.
* **Normalized Returns:** See percentage growth starting from 0% for fair comparison.
* **Smart Currency Handling:** Automatically handles currency differences and trading holidays.

### 2. 🏢 Country-Specific Stock Analysis
* **Live Data Fetching:** Automatically downloads the official list of stocks for:
    * 🇮🇳 India (NSE - 2000+ Stocks)
    * 🇺🇸 USA (S&P 500)
    * 🇩🇪 Germany (DAX)
    * 🇬🇧 UK (FTSE 100)
* **Index Filtering:** Filter huge stock lists by specific indices (e.g., "Show me only Nifty Bank stocks").

### 3. 🔬 Deep Dive "Microscope" Mode
A professional technical analysis suite for individual stocks:
* **Interactive Charts:** Combined Candlestick + Volume Overlay chart (Plotly).
* **Volatility Analysis:** View "Avg Daily Volatility" to gauge risk.
* **Price Highlights:** Instantly see where the current price sits relative to the Period High/Low.
* **Smart Metrics:** Best Day, Worst Day, and Total Return for the selected period.

---

## 🛠️ Tech Stack

* **Frontend:** `Streamlit` (Python)
* **Data Source:** `yfinance` (Yahoo Finance API)
* **Live Listings:** `requests` & `pandas` (Scraping NSE/Wikipedia)
* **Visualization:** `Plotly` (Interactive Line & Candlestick charts)

---

## ⚙️ Installation & Local Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/mayank-porwal-da/market-lens.git]
    cd market-lens
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App**
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

```text
market-lens/
├── app.py                # Main application code
├── requirements.txt      # List of dependencies
└── README.md             # Project documentation
