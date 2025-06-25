import streamlit as st
import pandas as pd
import openai

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="AI Financial Analyst", layout="wide")
st.title("📊 AI Trial Balance Analyzer")
st.write("Upload your monthly Trial Balance to generate financial statements and analysis.")
st.subheader("📄 Upload your Trial Balance CSV")
uploaded_file = st.file_uploader("Upload your Trial Balance", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📄 Raw Trial Balance")
    st.dataframe(df)

    # Validate required columns
    required_columns = ["Account Name", "Debit", "Credit"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"Your CSV must contain these columns: {', '.join(required_columns)}")
    else:
        # Calculate net amount
        df["Net"] = df["Debit"].fillna(0) - df["Credit"].fillna(0)

        # Categorize into Balance Sheet or P&L
        df["Category"] = df["Account Name"].apply(
            lambda x: "Balance Sheet" if isinstance(x, str) and any(
                k in x.lower() for k in ["receivable", "payable", "cash", "asset", "liability", "equity"]
            ) else "P&L"
        )

        # Build financial statements
        balance_sheet = df[df["Category"] == "Balance Sheet"].copy()
        profit_loss = df[df["Category"] == "P&L"].copy()

        st.subheader("📈 Balance Sheet")
        st.dataframe(balance_sheet[["Account Name", "Net"]].groupby("Account Name").sum())

        st.subheader("📉 Profit & Loss")
        st.dataframe(profit_loss[["Account Name", "Net"]].groupby("Account Name").sum())

        # Prepare data summary for GPT
        csv_summary = df.to_csv(index=False)
        prompt = f"""
You are a smart finance analyst. Here's the trial balance data:

{csv_summary}

Summarize:
- Total Revenue and Expenses
- Net Profit
- Any unusual items
- Suggest 1–2 ways to improve
"""
