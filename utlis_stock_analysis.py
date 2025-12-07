import streamlit as st
import plotly.express as px
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import requests
import io

# -----------------------------------------------------------------------------
# NEW: LIVE TICKER FETCHING FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def get_stock_mapping(country):
    """
    Returns a dictionary mapping {Ticker: Company Name}.
    Example: {'RELIANCE.NS': 'Reliance Industries', 'TCS.NS': 'Tata Consultancy Services'}
    """
    mapping = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    # }

    try:
        # --- INDIA (NSE) ---
        if country == "India":
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            s = requests.get(url, headers=headers).content
            df = pd.read_csv(io.StringIO(s.decode('utf-8')))
            # Create a dictionary directly from the two columns
            # zip() pairs the Ticker (with suffix) and the Name
            mapping = dict(zip(df['SYMBOL'] + ".NS", df['NAME OF COMPANY']))

        # --- USA (S&P 500) ---
        elif country == "USA":
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            r = requests.get(url, headers=headers)
            df = pd.read_html(r.text)[0]
            mapping = dict(zip(df['Symbol'], df['Security']))

        # --- GERMANY (DAX) ---
        elif country == "Germany":
            url = "https://en.wikipedia.org/wiki/DAX"
            r = requests.get(url, headers=headers)
            tables = pd.read_html(r.text)
            for table in tables:
                if 'Ticker' in table.columns and 'Company' in table.columns:
                    raw_tickers = table['Ticker'].tolist()
                    clean_tickers = [f"{t}.DE" if not str(t).endswith(".DE") else t for t in raw_tickers]
                    mapping = dict(zip(clean_tickers, table['Company']))
                    break
            
        # --- UK (FTSE 100) ---
        elif country == "UK":
            url = "https://en.wikipedia.org/wiki/FTSE_100_Index"
            r = requests.get(url, headers=headers)
            tables = pd.read_html(r.text)
            for table in tables:
                if 'Ticker' in table.columns and 'Company' in table.columns:
                    clean_tickers = (table['Ticker'] + ".L").tolist()
                    mapping = dict(zip(clean_tickers, table['Company']))
                    break

    except Exception as e:
        print(f"Error fetching {country}: {e}")
        return {} # Return empty dict on failure (or add fallback manual dict here)
        
    return mapping

@st.cache_data(ttl=86400)
def get_index_constituents(index_ticker, country):
    """
    Returns a list of tickers belonging to a specific index.
    """
    tickers = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # --- INDIA ---
        if country == "India":
            if index_ticker == "^NSEI": # Nifty 50
                url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
                s = requests.get(url, headers=headers).content
                df = pd.read_csv(io.StringIO(s.decode('utf-8')))
                tickers = (df['Symbol'] + ".NS").tolist()
            elif index_ticker == "^NSEBANK": # Nifty Bank
                url = "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv"
                s = requests.get(url, headers=headers).content
                df = pd.read_csv(io.StringIO(s.decode('utf-8')))
                tickers = (df['Symbol'] + ".NS").tolist()
                
        # --- USA ---
        elif index_ticker == "^GSPC": # S&P 500
            # Reuse the S&P fetch logic we already have
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df = pd.read_html(requests.get(url, headers=headers).text)[0]
            tickers = df['Symbol'].tolist()
            
        # --- GERMANY ---
        elif index_ticker == "^GDAXI": # DAX
            url = "https://en.wikipedia.org/wiki/DAX"
            tables = pd.read_html(requests.get(url, headers=headers).text)
            for table in tables:
                if 'Ticker' in table.columns:
                    raw = table['Ticker'].tolist()
                    tickers = [f"{t}.DE" if not str(t).endswith(".DE") else t for t in raw]
                    break

    except Exception as e:
        print(f"Error fetching constituents: {e}")
        return []

    return tickers


# function to fetch data and 
# -----------------------------------------------------------------------------
# HELPER FUNCTIONS (Add this section below imports)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=300)
def get_stock_data(tickers, period):
    if not tickers:
        return pd.DataFrame(), False
    
    # Download data
    data = yf.download(tickers, period=period, progress=False)
    
    # 1. Extract Price Data (Handle MultiIndex)
    if len(tickers) > 1:
        try:
            df = data['Close']
        except KeyError:
            df = data.xs('Close', level=0, axis=1)
    else:
        df = pd.DataFrame(data['Close'])
        df.columns = tickers

    # 2. SMART TRUNCATION CHECK
    # We define "Truncated" as a significant gap in start dates (e.g., > 10 days).
    # This ignores small holiday misalignments between countries.
    was_truncated = False
    
    if not df.empty:
        # Find the first valid date for each column (Ticker)
        first_valid_dates = df.apply(lambda col: col.first_valid_index())
        
        # Check if we have valid dates to compare
        if not first_valid_dates.isnull().any():
            earliest_start = first_valid_dates.min()
            latest_start = first_valid_dates.max()
            
            # Calculate the gap in days
            gap = (latest_start - earliest_start).days
            
            # Only flag if the gap is massive (e.g., > 10 days)
            if gap > 10:
                was_truncated = True

    # 3. Clean Data
    # .ffill() fills holidays/gaps inside the data
    # .dropna() cuts off the "pre-listing" empty dates at the start
    df = df.ffill().dropna()
    
    return df, was_truncated

def plot_performance_chart(df):
    """
    Normalizes prices to percentage change starting at 0% and plots line chart.
    """
    if df.empty:
        st.warning("No data available for the selected range.")
        return None

    # Normalization Formula: (Price / Start_Price - 1) * 100
    # This makes all assets start at 0%
    normalized_df = (df / df.iloc[0] - 1) * 100
    
    # Create Plotly Chart
    fig = px.line(
        normalized_df, 
        x=normalized_df.index, 
        y=normalized_df.columns,
        title="Relative Performance (%)",
        labels={"value": "Return (%)", "variable": "Asset", "Date": "Date"}
    )
    
    # Add a horizontal line at 0%
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    
    # Styling
    fig.update_layout(
        hovermode="x unified", 
        template="plotly_dark",
        yaxis_title="Growth (%)",
        legend_title="Assets"
    )
    
    return fig

def get_ohlc_data(ticker, period):
    """
    Fetches Open/High/Low/Close/Volume data for a single ticker.
    """
    # Force a list to ensure consistent MultiIndex behavior, or handle single string
    data = yf.download(ticker, period=period, progress=False)
    
    # 1. Handle MultiIndex (If yf returns (Price, Ticker))
    # Recent yfinance versions often return MultiIndex even for single tickers
    if isinstance(data.columns, pd.MultiIndex):
        try:
            # Extract the ticker level if it exists
            data = data.xs(ticker, level=1, axis=1)
        except KeyError:
            # Fallback if structure is different
            pass
            
    # 2. Reset Index to make 'Date' a column (easier for Plotly)
    data = data.reset_index()
    return data

# def plot_candle_chart(df, ticker):
#     """
#     Creates a 2-row subplot: Candlestick (Top) and Volume (Bottom).
#     """
#     # Create Subplots
#     fig = make_subplots(
#         rows=2, cols=1, 
#         shared_xaxes=True, 
#         vertical_spacing=0.03, 
#         subplot_titles=(f'{ticker} Price', 'Volume'),
#         row_heights=[0.7, 0.3]
#     )

#     # 1. Candlestick Trace
#     fig.add_trace(
#         go.Candlestick(
#             x=df['Date'],
#             open=df['Open'], high=df['High'],
#             low=df['Low'], close=df['Close'],
#             name='OHLC'
#         ), row=1, col=1
#     )

#     # 2. Volume Trace (Color-coded: Green if Close > Open, else Red)
#     # Handle colors safely with numpy or list comprehension
#     colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df.iterrows()]
    
#     fig.add_trace(
#         go.Bar(
#             x=df['Date'], y=df['Volume'],
#             marker_color=colors,
#             name='Volume'
#         ), row=2, col=1
#     )

#     # Layout Updates
#     fig.update_layout(
#         height=700,
#         xaxis_rangeslider_visible=False, # Hide the default slider
#         template="plotly_dark",
#         showlegend=False
#     )
    
#     return fig

def plot_candle_chart(df, ticker):
    """
    Creates a Single-Chart Overlay: Candlesticks with Volume at the bottom.
    """
    # 1. Define Colors for Volume (Green for Up days, Red for Down days)
    colors = ['rgba(0, 200, 0, 0.2)' if row['Close'] >= row['Open'] 
              else 'rgba(200, 0, 0, 0.2)' for _, row in df.iterrows()]
    
    # 2. Create the Figure
    fig = go.Figure()

    # --- TRACE 1: CANDLESTICK (Left Axis) ---
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a', # Professional Green
            decreasing_line_color='#ef5350'  # Professional Red
        )
    )

    # --- TRACE 2: VOLUME (Right Axis) ---
    fig.add_trace(
        go.Bar(
            x=df['Date'], 
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            yaxis='y2' # Link to the secondary axis
        )
    )

    # 3. Layout Configuration
    fig.update_layout(
        title=f'{ticker} Price & Volume Action',
        # Make the chart taller for better analysis
        height=800, 
        template="plotly_dark",
        showlegend=False,
        hovermode="x unified",
        
        # Left Axis (Price)
        yaxis=dict(
            title="Price",
            side="left",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        
        # Right Axis (Volume)
        yaxis2=dict(
            title="Volume",
            side="right",
            overlaying="y", # Overlay on top of the Price axis
            showgrid=False, # Hide volume gridlines to avoid clutter
            # TRICK: Set range to 4x max volume to push bars to bottom 25%
            range=[0, df['Volume'].max() * 4], 
            visible=False # Optional: Hide the axis numbers if you just want the visual bars
        ),
        
        xaxis=dict(
            rangeslider_visible=False,
            showgrid=False
        )
    )
    
    return fig

def custom_divider(height=2, margin_top=5, margin_bottom=5):
    """
    Renders a custom HTML divider with controlled spacing.
    """
    st.markdown(
        f"""
        <hr style="
            height: {height}px; 
            border: none; 
            color: #444; 
            background-color: #444; 
            margin-top: {margin_top}px; 
            margin-bottom: {margin_bottom}px;
        " />
        """, 
        unsafe_allow_html=True
    )