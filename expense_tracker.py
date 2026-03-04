import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Professional Expense Tracker", layout="wide")
st.title("💰 Professional Expense Tracker Dashboard")

DB_NAME = "Tracker.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT
        )
        """)

def add_expense(date, category, amount, note):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
            (date, category, amount, note)
        )

def delete_expense(expense_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

def load_data():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM expenses ORDER BY date DESC", conn)
    return df

init_db()

st.sidebar.header("➕ Add New Expense")

date = st.sidebar.date_input("Date")
category = st.sidebar.selectbox("Category",
                                ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Other"])
amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f")
note = st.sidebar.text_input("Note (Optional)")

if st.sidebar.button("Add Expense"):
    if amount <= 0:
        st.sidebar.error("Amount must be greater than 0")
    else:
        add_expense(str(date), category, amount, note)
        st.sidebar.success("Expense Added Successfully!")
        st.rerun()

df = load_data()

if df.empty:
    st.warning("No expenses yet. Add some from sidebar 👈")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M")

st.subheader("🔍 Filter Options")

col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox("Select Month",
                                  ["All"] + sorted(df["month"].astype(str).unique()))

with col2:
    selected_category = st.selectbox("Select Category",
                                     ["All"] + sorted(df["category"].unique()))

filtered_df = df.copy()

if selected_month != "All":
    filtered_df = filtered_df[filtered_df["month"].astype(str) == selected_month]

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

st.subheader("📊 Summary")

c1, c2, c3 = st.columns(3)

c1.metric("Total Expense", f"₹ {filtered_df['amount'].sum():,.2f}")
c2.metric("No. of Transactions", len(filtered_df))
c3.metric("Average Expense", f"₹ {filtered_df['amount'].mean():,.2f}")

st.markdown("---")

st.subheader("📈 Visual Analytics")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Category-wise Expense")
    category_data = filtered_df.groupby("category")["amount"].sum()

    colors = plt.cm.Set3(range(len(category_data)))
    fig1, ax1 = plt.subplots()
    bars = ax1.bar(category_data.index, category_data.values, color=colors)

    ax1.set_ylabel("Amount (₹)")
    ax1.set_xlabel("Category")
    ax1.set_title("Expenses by Category")
    plt.xticks(rotation=45)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    st.pyplot(fig1)

with col2:
    st.markdown("### Daily Expense Trend")
    daily_data = filtered_df.groupby("date")["amount"].sum()

    fig2, ax2 = plt.subplots()
    ax2.plot(daily_data.index, daily_data.values,
             marker="o",
             linewidth=3,
             color="#FF6F61")

    ax2.fill_between(daily_data.index,
                     daily_data.values,
                     color="#FFB347",
                     alpha=0.3)

    ax2.set_ylabel("Amount (₹)")
    ax2.set_xlabel("Date")
    ax2.set_title("Daily Spending Trend")
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.xticks(rotation=65)
    fig2.autofmt_xdate()

    st.pyplot(fig2)

st.markdown("---")

st.subheader("📋 Expense Records")
st.dataframe(filtered_df[["id", "date", "category", "amount", "note"]],
             use_container_width=True)

st.subheader("⬇ Download Report")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Filtered Data as CSV",
    csv,
    "expense_report.csv",
    "text/csv"
)

st.subheader("❌ Delete Expense")

delete_id = st.number_input("Enter Expense ID", min_value=1, step=1)

if st.button("Delete Expense"):
    delete_expense(delete_id)
    st.success("Expense Deleted Successfully!")
    st.rerun()