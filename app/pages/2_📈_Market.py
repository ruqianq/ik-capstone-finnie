"""
Market Dashboard Page
View market indices, sector performance, and trends.
"""

import streamlit as st
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tools.market_data import MarketDataTool

# Page configuration
st.set_page_config(
    page_title="Market - FinnIE",
    page_icon="📈",
    layout="wide"
)

# Initialize
market_tool = MarketDataTool()

st.title("📈 Market Dashboard")
st.markdown("Track major indices, sectors, and market trends")

# Sidebar
with st.sidebar:
    st.markdown("## 💰 FinnIE")
    st.markdown("*Market Analysis*")
    st.divider()

    st.markdown("### Quick Lookup")
    lookup_symbol = st.text_input("Enter Symbol", placeholder="AAPL").upper()
    if st.button("Get Quote", use_container_width=True):
        if lookup_symbol:
            data = market_tool.get_stock_price(lookup_symbol)
            if data:
                change_color = "green" if data['change_percent'] >= 0 else "red"
                st.metric(
                    lookup_symbol,
                    f"${data['last_price']:.2f}",
                    f"{data['change_percent']:+.2f}%"
                )
            else:
                st.error(f"Could not find {lookup_symbol}")


def get_index_data():
    """Fetch major market indices data."""
    indices = {
        "S&P 500": "^GSPC",
        "Dow Jones": "^DJI",
        "NASDAQ": "^IXIC",
        "Russell 2000": "^RUT",
        "VIX": "^VIX"
    }

    data = []
    for name, symbol in indices.items():
        price_data = market_tool.get_stock_price(symbol)
        if price_data:
            data.append({
                'Index': name,
                'Symbol': symbol,
                'Price': price_data['last_price'],
                'Change %': price_data['change_percent']
            })

    return pd.DataFrame(data) if data else None


def get_sector_data():
    """Fetch sector ETF performance data."""
    sectors = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Disc.": "XLY",
        "Consumer Staples": "XLP",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication": "XLC"
    }

    data = []
    for name, symbol in sectors.items():
        price_data = market_tool.get_stock_price(symbol)
        if price_data:
            data.append({
                'Sector': name,
                'ETF': symbol,
                'Price': price_data['last_price'],
                'Change %': price_data['change_percent']
            })

    return pd.DataFrame(data) if data else None


# Main content
st.markdown("### Major Indices")

with st.spinner("Loading market data..."):
    index_df = get_index_data()

if index_df is not None and not index_df.empty:
    # Display index metrics
    cols = st.columns(len(index_df))

    for idx, (_, row) in enumerate(index_df.iterrows()):
        with cols[idx]:
            # Format price based on index type
            if row['Index'] == 'VIX':
                price_fmt = f"{row['Price']:.2f}"
            else:
                price_fmt = f"{row['Price']:,.2f}"

            st.metric(
                row['Index'],
                price_fmt,
                f"{row['Change %']:+.2f}%"
            )

    st.divider()

    # Index performance bar chart (excluding VIX)
    chart_df = index_df[index_df['Index'] != 'VIX'].copy()
    colors = ['green' if x >= 0 else 'red' for x in chart_df['Change %']]

    fig_indices = go.Figure(data=[
        go.Bar(
            x=chart_df['Index'],
            y=chart_df['Change %'],
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in chart_df['Change %']],
            textposition='outside'
        )
    ])
    fig_indices.update_layout(
        title="Index Performance Today",
        yaxis_title="Change %",
        xaxis_title="",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_indices, use_container_width=True)
else:
    st.warning("Unable to load index data. Please check your connection.")

st.divider()

# Sector Performance
st.markdown("### Sector Performance")

with st.spinner("Loading sector data..."):
    sector_df = get_sector_data()

if sector_df is not None and not sector_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        # Sector performance bar chart
        sector_df_sorted = sector_df.sort_values('Change %', ascending=True)
        colors = ['green' if x >= 0 else 'red' for x in sector_df_sorted['Change %']]

        fig_sectors = go.Figure(data=[
            go.Bar(
                y=sector_df_sorted['Sector'],
                x=sector_df_sorted['Change %'],
                orientation='h',
                marker_color=colors,
                text=[f"{x:+.2f}%" for x in sector_df_sorted['Change %']],
                textposition='outside'
            )
        ])
        fig_sectors.update_layout(
            title="Sector ETF Performance",
            xaxis_title="Change %",
            yaxis_title="",
            height=450,
            showlegend=False
        )
        st.plotly_chart(fig_sectors, use_container_width=True)

    with col2:
        # Sector heatmap-style treemap
        # Add absolute change for sizing
        sector_df['Abs Change'] = sector_df['Change %'].abs()
        sector_df['Color'] = sector_df['Change %']

        fig_treemap = px.treemap(
            sector_df,
            path=['Sector'],
            values='Abs Change',
            color='Color',
            color_continuous_scale=['red', 'white', 'green'],
            color_continuous_midpoint=0,
            title="Sector Heatmap"
        )
        fig_treemap.update_layout(height=450)
        fig_treemap.update_traces(
            textinfo="label+text",
            text=[f"{x:+.2f}%" for x in sector_df['Change %']]
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

    st.divider()

    # Top movers
    st.markdown("### Top Movers")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Gainers")
        gainers = sector_df.nlargest(3, 'Change %')
        for _, row in gainers.iterrows():
            st.success(f"**{row['Sector']}** ({row['ETF']}): {row['Change %']:+.2f}%")

    with col2:
        st.markdown("#### Top Losers")
        losers = sector_df.nsmallest(3, 'Change %')
        for _, row in losers.iterrows():
            st.error(f"**{row['Sector']}** ({row['ETF']}): {row['Change %']:+.2f}%")

    st.divider()

    # Detailed sector table
    st.markdown("### Sector Details")

    display_df = sector_df[['Sector', 'ETF', 'Price', 'Change %']].copy()
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
    display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.warning("Unable to load sector data. Please check your connection.")

# Market info section
st.divider()
st.markdown("### About Market Indicators")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### VIX (Volatility Index)")
    st.markdown("""
    The VIX measures expected market volatility over the next 30 days.
    - **Below 15**: Low volatility, calm markets
    - **15-25**: Normal volatility
    - **Above 25**: High volatility, uncertainty
    """)

with col2:
    st.markdown("#### Major Indices")
    st.markdown("""
    - **S&P 500**: 500 large US companies
    - **Dow Jones**: 30 blue-chip stocks
    - **NASDAQ**: Tech-heavy composite
    - **Russell 2000**: Small-cap stocks
    """)

with col3:
    st.markdown("#### Sector ETFs")
    st.markdown("""
    Sector ETFs track specific market segments.
    They help identify which areas of the economy
    are performing well or struggling.
    """)
