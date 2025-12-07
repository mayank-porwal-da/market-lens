import streamlit as st
from utlis_stock_analysis import *
# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MarketLens: Global Market Comparator & Analyzer",
    page_icon="📈",
    layout="wide"
)

# setting up title for Page
st.title("Analyze & Compare Stocks / Indexes")
st.markdown("Compare indices, analyze stocks, and discover market trends.")

# -----------------------------------------------------------------------------
# 2. CONSTANTS & DATA STRUCTURES
# -----------------------------------------------------------------------------

# A. Standard Indices Map
WORLD_INDICES = {
    "🇺🇸 S&P 500 (USA)": "^GSPC",
    "🇺🇸 Nasdaq 100 (USA)": "^NDX",
    "🇮🇳 Nifty 50 (India)": "^NSEI",
    "🇮🇳 Sensex (India)": "^BSESN",
    "🇬🇧 FTSE 100 (UK)": "^FTSE",
    "🇯🇵 Nikkei 225 (Japan)": "^N225",
    "🇩🇪 DAX (Germany)": "^GDAXI",
    "🇨🇳 Shanghai Composite (China)": "000001.SS",
    "🇨🇳 Shenzhen Composite (China)": "399001.SZ",
    "🇭🇰 Hang Seng Index (Hong Kong)": "^HSI",
    "Australia":"^AXJO"
}

# B. Country Configuration (Suffix & Currency)
COUNTRY_CONFIG = {
    "India": {"suffix": ".NS", "currency": "INR"},
    "USA": {"suffix": "", "currency": "USD"},
    "UK": {"suffix": ".L", "currency": "GBP"},
    "Germany": {"suffix": ".DE", "currency": "EUR"},
}

# C. Stock Lists (Mock Data for Step 1 - We can replace this with CSV loads later)
# Ideally, you would load these from a file like 'nse_stocks.csv'
STOCK_DB = {
    "India": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "TATAMOTORS", "SBIN"],
    "USA": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"],
    "UK": ["RR", "HSBA", "BP", "SHEL", "VOD"], # Suffix .L added automatically later
    "Germany": ["SIE", "BMW", "VOW3", "SAP", "ALV"]
}

def render_stock_selection_ui(country, mode="multi", max_selections=5, key_suffix=""):
    """
    Renders the UI for filtering and selecting stocks.
    Args:
        country: Selected country (e.g., "India")
        mode: "multi" (for comparison) or "single" (for deep dive)
        max_selections: Max limit for multiselect
        key_suffix: Unique string to prevent Streamlit duplicate widget ID errors
    Returns:
        List of selected tickers (e.g., ['RELIANCE.NS'])
    """
    
    # 1. Fetch Master Map (Ticker -> Name)
    with st.spinner(f"Loading stock list for {country}..."):
        stock_map = get_stock_mapping(country)
        all_tickers = list(stock_map.keys())

    # 2. Filter UI
    # We use columns to make it look compact
    c1, c2 = st.columns([1, 2])
    
    with c1:
        filter_mode = st.radio(
            "Filter By:",
            ["All Stocks", "Index"],
            key=f"filter_{key_suffix}"
        )
    
    filtered_options = all_tickers
    
    # 3. Index Logic (If "Index" is selected)
    if filter_mode == "Index":
        # Dynamic Index List based on country
        indices = {k:v for k,v in WORLD_INDICES.items() if country in k}
        if country == "India": indices["🇮🇳 Nifty Bank"] = "^NSEBANK"
            
        with c2:
            target_index = st.selectbox("Select Index", indices.keys(), key=f"idx_{key_suffix}")
            target_ticker = indices[target_index]
        
        # Fetch Constituents
        with st.spinner(f"Fetching {target_index} stocks..."):
            index_stocks = get_index_constituents(target_ticker, country)
            
        if index_stocks:
            # Intersection: Only keep stocks that are in the index
            filtered_options = [t for t in all_tickers if t in index_stocks]
        else:
            st.warning("Index data unavailable. Showing all stocks.")

    # 4. Selection Widget
    label = "Search Stock" if mode == "single" else f"Select Stocks (Max {max_selections})"
    
    if mode == "single":
        selected = st.selectbox(
            label, 
            options=filtered_options,
            format_func=lambda x: f"{stock_map.get(x, x)} ({x})",
            key=f"sel_{key_suffix}"
        )
        return [selected] if selected else []
    else:
        selected = st.multiselect(
            label, 
            options=filtered_options, 
            max_selections=max_selections,
            format_func=lambda x: f"{stock_map.get(x, x)} ({x})",
            key=f"sel_{key_suffix}"
        )
        return selected

# -----------------------------------------------------------------------------
# 3. SIDEBAR: GLOBAL CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Controls")
    
    # 3.1 Main Intent Selection
    app_mode = st.radio(
        "What would you like to do?",
        [
            "1. Compare Indexes", 
            "2. Compare Stocks (One Country)", 
            "3. Index vs Stocks (Alpha Check)", 
            "4. Analyze Single Stock"
        ]
    )
    
    custom_divider(height=1, margin_top=10, margin_bottom=10)
    
    # 3.2 Dynamic Country Selection (Hidden for Option 1)
    selected_country = None
    if "1." not in app_mode:
        selected_country = st.selectbox(
            "Select Country",
            options=list(COUNTRY_CONFIG.keys())
        )
        st.caption(f"Currency: {COUNTRY_CONFIG[selected_country]['currency']}")
        custom_divider(height=1, margin_top=10, margin_bottom=10)

    # 3.3 Time Period Selector
    period = st.select_slider(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
        value="1y"
    )

# -----------------------------------------------------------------------------
# 4. MAIN AREA: INPUT LOGIC (Based on Selection)
# -----------------------------------------------------------------------------

selected_tickers = []
benchmark_ticker = None

# --- LOGIC 1: COMPARE INDICES ---
if "1." in app_mode:
    st.subheader("🌍 Global Index Comparison")
    selected_indices = st.multiselect(
        "Select Indices to Compare",
        options=list(WORLD_INDICES.keys()),
        default=["🇮🇳 Nifty 50 (India)", "🇺🇸 S&P 500 (USA)"]
    )
    # Convert display names to Ticker symbols
    selected_tickers = [WORLD_INDICES[name] for name in selected_indices]

# --- LOGIC 2: COMPARE STOCKS ---
elif "2." in app_mode:
    st.subheader(f"🏢 Compare Stocks in {selected_country}")
    
    # Call our new function!
    selected_tickers = render_stock_selection_ui(
        country=selected_country, 
        mode="multi", 
        max_selections=5, 
        key_suffix="mode2"
    )

# --- LOGIC 3: INDEX VS STOCK ---
elif "3." in app_mode:
    st.subheader(f"⚖️ Benchmark vs Stocks ({selected_country})")
    
    # Benchmark Selection
    index_options = [name for name in WORLD_INDICES.keys() if selected_country in name]
    if not index_options: index_options = list(WORLD_INDICES.keys())
    
    benchmark_name = st.selectbox("Select Benchmark Index", options=index_options)
    benchmark_ticker = WORLD_INDICES[benchmark_name]
    
    # Stock Selection (Using our new function)
    user_stocks = render_stock_selection_ui(
        country=selected_country, 
        mode="multi", 
        max_selections=3, 
        key_suffix="mode3"
    )
    
    if benchmark_ticker:
        selected_tickers = [benchmark_ticker] + user_stocks

# --- LOGIC 4: SINGLE STOCK ANALYSIS ---
elif "4." in app_mode:
    st.subheader(f"🔎 Deep Dive Analysis ({selected_country})")
    
    # Call our new function in "single" mode
    selected_tickers = render_stock_selection_ui(
        country=selected_country, 
        mode="single", 
        key_suffix="mode4"
    )

# -----------------------------------------------------------------------------
# DEBUG / VERIFICATION (Temporary)
# -----------------------------------------------------------------------------
# with st.expander("Debug Info (Data to be fetched)", expanded=True):
#     st.write(f"**Mode:** {app_mode}")
#     st.write(f"**Selected Country:** {selected_country}")
#     st.write(f"**Tickers to Fetch:** {selected_tickers}")
#     st.write(f"**Time Period:** {period}")

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION (Replace the Debug Section with this)
# -----------------------------------------------------------------------------

if selected_tickers:
    # 1. Fetch Data
    with st.spinner(f"Fetching data for {', '.join(selected_tickers)}..."):
        # Unpack the Tuple: df_prices gets the data, truncated gets the True/False flag
        df_prices, truncated = get_stock_data(selected_tickers, period)
    
    # Show the Toast HERE (Outside the cached function)
    if truncated:
        st.toast("⚠️ Note: Some assets listed recently. Chart adjusted to common start date.", icon="ℹ️")
    
    # 2. Comparison Logic (Modes 1, 2, 3)
    # (Mode 4 uses a different chart type, so we handle it separately next step)
    if "4." not in app_mode:
        if not df_prices.empty:
            
            # --- NEW: CREATE A TICKER -> NAME MAP ---
            # We build a dictionary to translate weird symbols back to human names
            name_map = {}
            
            if "1." in app_mode: # Compare Indexes
                # Reverse the WORLD_INDICES dict: {'^NSEI': 'Nifty 50', ...}
                name_map = {v: k for k, v in WORLD_INDICES.items()}
                
            elif "2." in app_mode: # Compare Stocks
                # Map 'RELIANCE.NS' -> 'RELIANCE'
                # We know the logic was: ticker = stock + suffix
                suffix = COUNTRY_CONFIG[selected_country]['suffix']
                for stock in selected_tickers:
                    name_map[f"{stock}{suffix}"] = stock
            
            elif "3." in app_mode: # Index vs Stocks
                # 1. Map the Benchmark
                # Find the benchmark name from the ticker
                bench_name = [k for k, v in WORLD_INDICES.items() if v == benchmark_ticker][0]
                name_map[benchmark_ticker] = bench_name
                
                # 2. Map the Stocks
                suffix = COUNTRY_CONFIG[selected_country]['suffix']
                for stock in selected_tickers:
                    name_map[f"{stock}{suffix}"] = stock

            # ----------------------------------------
            
            # A. Display the Chart
            # (Optional: Rename columns in the dataframe for the chart legend too!)
            df_plot = df_prices.rename(columns=name_map)
            st.plotly_chart(plot_performance_chart(df_plot), use_container_width=True)
            
            # B. Display "Smart Insights"
            st.subheader("⚡ Quick Insights")
            
            # Calculate Total Return
            total_return = (df_prices.iloc[-1] / df_prices.iloc[0] - 1) * 100
            
            # Identify Best/Worst Tickers
            best_ticker = total_return.idxmax()
            worst_ticker = total_return.idxmin()
            
            # TRANSLATE TICKERS TO NAMES
            # .get(ticker, ticker) means: "Try to find the name, if not found, keep the ticker"
            best_name = name_map.get(best_ticker, best_ticker)
            worst_name = name_map.get(worst_ticker, worst_ticker)
            
            col1, col2 = st.columns(2)
            col1.metric("🏆 Best Performer", best_name, f"{total_return.max():.2f}%")
            col2.metric("📉 Worst Performer", worst_name, f"{total_return.min():.2f}%")
            
            with st.expander("View Raw Data"):
                st.dataframe(df_prices)

    # 3. Mode 4: Deep Dive Analysis
    else:
        if selected_tickers:
            target_stock = selected_tickers[0]
            
            with st.spinner(f"Analyzing {target_stock}..."):
                df_ohlc = get_ohlc_data(target_stock, period)
            
            if not df_ohlc.empty:
                # ---------------------------------------------------------
                # 1. CALCULATE METRICS
                # ---------------------------------------------------------
                
                # A. Current Price
                latest = df_ohlc.iloc[-1]
                current_price = latest['Close']
                
                # B. Period High (Price & Date)
                max_price = df_ohlc['High'].max()
                max_price_date = df_ohlc.loc[df_ohlc['High'].idxmax(), 'Date']
                
                # C. Period Low (Price & Date)
                min_price = df_ohlc['Low'].min()
                min_price_date = df_ohlc.loc[df_ohlc['Low'].idxmin(), 'Date']
                
                # D. Total Return (Context)
                start_price = df_ohlc.iloc[0]['Close']
                total_return = ((current_price / start_price) - 1) * 100
                
                # ---------------------------------------------------------
                # 2. DISPLAY DASHBOARD
                # ---------------------------------------------------------
                
                # --- ROW 1: THE BIG HIGHLIGHTS ---
                st.subheader(f"🏷️ Price Highlights ({period})")
                
                h1, h2, h3 = st.columns(3)
                
                # Highlight 1: The Peak
                h1.metric(
                    label=f"🏔️ Max Price ({max_price_date.strftime('%d %b %y')})",
                    value=f"{max_price:,.2f}",
                    delta=f"{(current_price - max_price):,.2f} from top",
                    # delta_color="inverse" # Red arrow because we are below top
                )
                
                # Highlight 2: Current Status
                h2.metric(
                    label="📍 Current Price",
                    value=f"{current_price:,.2f}",
                    delta=f"{total_return:.2f}% Return"
                )
                
                # Highlight 3: The Bottom
                h3.metric(
                    label=f"⚓ Min Price ({min_price_date.strftime('%d %b %y')})",
                    value=f"{min_price:,.2f}",
                    delta=f"+{(current_price - min_price):,.2f} from low"
                )

                custom_divider(height=1, margin_top=10, margin_bottom=10)

                # --- ROW 2: THE CHART ---
                st.plotly_chart(plot_candle_chart(df_ohlc, target_stock), use_container_width=True)
                
                # --- ROW 3: RAW DATA ---
                with st.expander("View OHLC Data"):
                    st.dataframe(df_ohlc)
            
            else:
                st.error("No data found for this ticker.")

else:
    st.info("👆 Please select at least one asset from above options to begin.")