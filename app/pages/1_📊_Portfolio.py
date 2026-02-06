"""
Portfolio Dashboard Page
View and manage your investment portfolio.
"""

import streamlit as st
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_db, PortfolioItem, init_db
from app.tools.market_data import MarketDataTool

# Page configuration
st.set_page_config(
    page_title="Portfolio - FinnIE",
    page_icon="📊",
    layout="wide"
)

# Initialize
init_db()
market_tool = MarketDataTool()

st.title("📊 Portfolio Dashboard")
st.markdown("View and manage your investment portfolio")

# Sidebar
with st.sidebar:
    st.markdown("## 💰 FinnIE")
    st.markdown("*Portfolio Manager*")
    st.divider()

    st.markdown("### Quick Add")
    with st.form("add_stock"):
        symbol = st.text_input("Symbol", placeholder="AAPL").upper()
        shares = st.number_input("Shares", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Add to Portfolio", use_container_width=True)

        if submitted and symbol and shares > 0:
            try:
                db = next(get_db())
                existing = db.query(PortfolioItem).filter(PortfolioItem.symbol == symbol).first()

                if existing:
                    existing.quantity += shares
                else:
                    price_data = market_tool.get_stock_price(symbol)
                    price = price_data['last_price'] if price_data else 0.0
                    new_item = PortfolioItem(symbol=symbol, quantity=shares, avg_price=price)
                    db.add(new_item)

                db.commit()
                st.success(f"Added {shares} shares of {symbol}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                db.close()


def get_portfolio_data():
    """Fetch portfolio data with current prices."""
    db = next(get_db())
    try:
        items = db.query(PortfolioItem).all()
        if not items:
            return None

        data = []
        for item in items:
            price_data = market_tool.get_stock_price(item.symbol)
            current_price = price_data['last_price'] if price_data else 0.0
            change_pct = price_data['change_percent'] if price_data else 0.0

            value = current_price * item.quantity
            cost_basis = item.avg_price * item.quantity
            gain_loss = value - cost_basis
            gain_loss_pct = ((value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

            data.append({
                'Symbol': item.symbol,
                'Shares': item.quantity,
                'Avg Cost': item.avg_price,
                'Current Price': current_price,
                'Day Change %': change_pct,
                'Value': value,
                'Gain/Loss': gain_loss,
                'Gain/Loss %': gain_loss_pct
            })

        return pd.DataFrame(data)
    finally:
        db.close()


# Main content
portfolio_df = get_portfolio_data()

if portfolio_df is None or portfolio_df.empty:
    st.info("📭 Your portfolio is empty. Add stocks using the sidebar or chat with FinnIE!")

    st.markdown("### Get Started")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1. Add Stocks")
        st.markdown("Use the sidebar form or say 'Add 10 AAPL' in chat")

    with col2:
        st.markdown("#### 2. Track Performance")
        st.markdown("View gains, losses, and allocation")

    with col3:
        st.markdown("#### 3. Stay Informed")
        st.markdown("Get market news and analysis")

else:
    # Summary metrics
    total_value = portfolio_df['Value'].sum()
    total_gain_loss = portfolio_df['Gain/Loss'].sum()
    total_cost = (portfolio_df['Avg Cost'] * portfolio_df['Shares']).sum()
    total_gain_pct = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Value", f"${total_value:,.2f}")

    with col2:
        st.metric(
            "Total Gain/Loss",
            f"${total_gain_loss:,.2f}",
            f"{total_gain_pct:+.2f}%"
        )

    with col3:
        st.metric("Positions", len(portfolio_df))

    with col4:
        best_performer = portfolio_df.loc[portfolio_df['Day Change %'].idxmax(), 'Symbol']
        best_change = portfolio_df['Day Change %'].max()
        st.metric("Top Performer", best_performer, f"{best_change:+.2f}%")

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Portfolio Allocation")
        fig_pie = px.pie(
            portfolio_df,
            values='Value',
            names='Symbol',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("### Daily Performance")
        colors = ['green' if x >= 0 else 'red' for x in portfolio_df['Day Change %']]
        fig_bar = go.Figure(data=[
            go.Bar(
                x=portfolio_df['Symbol'],
                y=portfolio_df['Day Change %'],
                marker_color=colors,
                text=[f"{x:+.2f}%" for x in portfolio_df['Day Change %']],
                textposition='outside'
            )
        ])
        fig_bar.update_layout(
            yaxis_title="Change %",
            xaxis_title="",
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Holdings table
    st.markdown("### Holdings")

    # Format the dataframe for display
    display_df = portfolio_df.copy()
    display_df['Avg Cost'] = display_df['Avg Cost'].apply(lambda x: f"${x:,.2f}")
    display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:,.2f}")
    display_df['Value'] = display_df['Value'].apply(lambda x: f"${x:,.2f}")
    display_df['Gain/Loss'] = display_df['Gain/Loss'].apply(lambda x: f"${x:+,.2f}")
    display_df['Day Change %'] = display_df['Day Change %'].apply(lambda x: f"{x:+.2f}%")
    display_df['Gain/Loss %'] = display_df['Gain/Loss %'].apply(lambda x: f"{x:+.2f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Actions
    st.divider()
    st.markdown("### Manage Holdings")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🗑️ Remove Stock"):
            remove_symbol = st.selectbox(
                "Select stock to remove",
                options=portfolio_df['Symbol'].tolist()
            )
            if st.button("Remove", type="primary"):
                try:
                    db = next(get_db())
                    item = db.query(PortfolioItem).filter(PortfolioItem.symbol == remove_symbol).first()
                    if item:
                        db.delete(item)
                        db.commit()
                        st.success(f"Removed {remove_symbol}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db.close()

    with col2:
        with st.expander("✏️ Update Shares"):
            update_symbol = st.selectbox(
                "Select stock to update",
                options=portfolio_df['Symbol'].tolist(),
                key="update_select"
            )
            new_shares = st.number_input("New share count", min_value=0.0, step=1.0)
            if st.button("Update", type="primary"):
                try:
                    db = next(get_db())
                    item = db.query(PortfolioItem).filter(PortfolioItem.symbol == update_symbol).first()
                    if item:
                        if new_shares == 0:
                            db.delete(item)
                        else:
                            item.quantity = new_shares
                        db.commit()
                        st.success(f"Updated {update_symbol}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db.close()
