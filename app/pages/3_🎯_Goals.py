"""
Goals Dashboard Page
Track and manage your financial goals.
"""

import streamlit as st
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_db, FinancialGoal, init_db

# Page configuration
st.set_page_config(
    page_title="Goals - FinnIE",
    page_icon="🎯",
    layout="wide"
)

# Initialize database
init_db()

st.title("🎯 Financial Goals")
st.markdown("Set, track, and achieve your financial milestones")

# Sidebar - Add New Goal
with st.sidebar:
    st.markdown("## 💰 FinnIE")
    st.markdown("*Goal Planner*")
    st.divider()

    st.markdown("### Create New Goal")
    with st.form("add_goal"):
        goal_name = st.text_input("Goal Name", placeholder="House Down Payment")
        target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=1000.0, value=10000.0)
        current_amount = st.number_input("Current Savings ($)", min_value=0.0, step=100.0, value=0.0)
        target_date = st.date_input("Target Date", value=date.today() + relativedelta(years=1))
        category = st.selectbox(
            "Category",
            options=["Emergency Fund", "House", "Retirement", "Education", "Vacation", "Other"]
        )

        submitted = st.form_submit_button("Add Goal", use_container_width=True)

        if submitted and goal_name and target_amount > 0:
            try:
                db = next(get_db())
                new_goal = FinancialGoal(
                    name=goal_name,
                    target_amount=target_amount,
                    current_amount=current_amount,
                    target_date=target_date,
                    category=category
                )
                db.add(new_goal)
                db.commit()
                st.success(f"Created goal: {goal_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                db.close()


def get_goals_data():
    """Fetch all financial goals."""
    db = next(get_db())
    try:
        goals = db.query(FinancialGoal).all()
        if not goals:
            return None

        data = []
        for goal in goals:
            months_remaining = max(0, (goal.target_date.year - date.today().year) * 12 +
                                   (goal.target_date.month - date.today().month))
            remaining = goal.target_amount - goal.current_amount
            monthly_needed = remaining / months_remaining if months_remaining > 0 else remaining

            progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

            data.append({
                'id': goal.id,
                'Name': goal.name,
                'Target': goal.target_amount,
                'Current': goal.current_amount,
                'Remaining': remaining,
                'Progress %': progress,
                'Target Date': goal.target_date,
                'Months Left': months_remaining,
                'Monthly Needed': monthly_needed,
                'Category': goal.category
            })

        return pd.DataFrame(data)
    finally:
        db.close()


# Main content
goals_df = get_goals_data()

if goals_df is None or goals_df.empty:
    st.info("🎯 No financial goals set yet. Create your first goal using the sidebar!")

    st.markdown("### Why Set Financial Goals?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🏠 Major Purchases")
        st.markdown("Save for a house down payment, car, or other big purchases with a clear timeline.")

    with col2:
        st.markdown("#### 🏖️ Life Events")
        st.markdown("Plan for vacations, weddings, education, or starting a family.")

    with col3:
        st.markdown("#### 🛡️ Security")
        st.markdown("Build an emergency fund and save for retirement peace of mind.")

    st.markdown("---")

    st.markdown("### Suggested Goals to Start")
    suggestions = [
        ("Emergency Fund", "Save 3-6 months of expenses", 15000),
        ("Retirement Boost", "Extra retirement savings this year", 6500),
        ("Vacation Fund", "Dream vacation savings", 5000),
    ]

    cols = st.columns(3)
    for idx, (name, desc, amount) in enumerate(suggestions):
        with cols[idx]:
            st.markdown(f"**{name}**")
            st.caption(desc)
            st.markdown(f"Suggested: ${amount:,}")

else:
    # Summary metrics
    total_target = goals_df['Target'].sum()
    total_saved = goals_df['Current'].sum()
    total_remaining = goals_df['Remaining'].sum()
    overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Goals", len(goals_df))

    with col2:
        st.metric("Total Target", f"${total_target:,.0f}")

    with col3:
        st.metric("Total Saved", f"${total_saved:,.0f}")

    with col4:
        st.metric("Overall Progress", f"{overall_progress:.1f}%")

    st.divider()

    # Goal Progress Cards
    st.markdown("### Goal Progress")

    # Display each goal as a progress card
    for idx, row in goals_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"#### {row['Name']}")
                st.caption(f"{row['Category']} | Due: {row['Target Date']}")

                # Progress bar
                progress = min(row['Progress %'], 100)
                st.progress(progress / 100)
                st.markdown(f"**${row['Current']:,.0f}** of ${row['Target']:,.0f} ({progress:.1f}%)")

            with col2:
                st.metric("Remaining", f"${row['Remaining']:,.0f}")
                st.metric("Months Left", row['Months Left'])

            with col3:
                st.metric("Monthly Needed", f"${row['Monthly Needed']:,.0f}")

                # Status indicator
                if row['Progress %'] >= 100:
                    st.success("Goal Reached!")
                elif row['Months Left'] == 0:
                    st.error("Past Due")
                elif row['Progress %'] >= 75:
                    st.info("Almost There!")

            st.divider()

    # Charts
    st.markdown("### Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Goals by category pie chart
        category_totals = goals_df.groupby('Category')['Target'].sum().reset_index()
        fig_pie = px.pie(
            category_totals,
            values='Target',
            names='Category',
            title="Goals by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Progress comparison bar chart
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name='Current',
            x=goals_df['Name'],
            y=goals_df['Current'],
            marker_color='#2196F3'
        ))
        fig_bar.add_trace(go.Bar(
            name='Remaining',
            x=goals_df['Name'],
            y=goals_df['Remaining'],
            marker_color='#BBDEFB'
        ))
        fig_bar.update_layout(
            title="Progress by Goal",
            barmode='stack',
            height=350,
            yaxis_title="Amount ($)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Manage Goals Section
    st.markdown("### Manage Goals")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("💵 Update Progress"):
            update_goal = st.selectbox(
                "Select Goal",
                options=goals_df['Name'].tolist(),
                key="update_goal_select"
            )
            if update_goal:
                current_goal = goals_df[goals_df['Name'] == update_goal].iloc[0]
                new_amount = st.number_input(
                    "New Savings Amount ($)",
                    min_value=0.0,
                    value=float(current_goal['Current']),
                    step=100.0
                )
                if st.button("Update", type="primary", key="update_progress"):
                    try:
                        db = next(get_db())
                        goal = db.query(FinancialGoal).filter(FinancialGoal.name == update_goal).first()
                        if goal:
                            goal.current_amount = new_amount
                            db.commit()
                            st.success(f"Updated {update_goal}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        db.close()

    with col2:
        with st.expander("🗑️ Delete Goal"):
            delete_goal = st.selectbox(
                "Select Goal to Delete",
                options=goals_df['Name'].tolist(),
                key="delete_goal_select"
            )
            if st.button("Delete Goal", type="primary", key="delete_goal"):
                try:
                    db = next(get_db())
                    goal = db.query(FinancialGoal).filter(FinancialGoal.name == delete_goal).first()
                    if goal:
                        db.delete(goal)
                        db.commit()
                        st.success(f"Deleted {delete_goal}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db.close()

# Tips section
st.divider()
st.markdown("### Goal Setting Tips")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Be Specific")
    st.markdown("Instead of 'save more', set a specific amount and deadline.")

with col2:
    st.markdown("#### Automate Savings")
    st.markdown("Set up automatic transfers to make saving effortless.")

with col3:
    st.markdown("#### Review Regularly")
    st.markdown("Check your progress monthly and adjust as needed.")
