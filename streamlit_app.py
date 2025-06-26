import streamlit as st
import pandas as pd
import plotly.express as px
import base64

st.set_page_config(page_title="AI Trial Balance Analyzer", layout="wide")
st.title("\U0001F4CA AI Trial Balance Analyzer")
st.write("Upload your monthly Trial Balance CSV to view financials and insights.")

uploaded_file = st.file_uploader("Upload your Trial Balance CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("\U0001F4C4 Raw Trial Balance")
    st.dataframe(df)

    required_columns = ["Month", "Account Name", "Debit", "Credit"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"Your CSV must contain these columns: {', '.join(required_columns)}")
    else:
        df = df.drop(columns=[col for col in df.columns if "Unnamed" in col])

        df["Debit"] = df["Debit"].fillna(0)
        df["Credit"] = df["Credit"].fillna(0)
        df["Net"] = df["Debit"] - df["Credit"]

        df["Account Name"] = df["Account Name"].astype(str)

        df["IsRevenue"] = df["Account Name"].str.lower().str.contains("revenue|sales|turnover", na=False)
        balance_sheet_keywords = ["receivable", "payable", "cash", "asset", "liability", "equity", "loan", "equipment"]
        is_balance_sheet = df["Account Name"].str.lower().str.contains("|".join(balance_sheet_keywords), na=False)
        df["IsExpense"] = (~df["IsRevenue"]) & (~is_balance_sheet)

        df["Revenue"] = df.apply(lambda row: abs(row["Net"]) if row["IsRevenue"] else 0, axis=1)
        df["Expenses"] = df.apply(lambda row: abs(row["Net"]) if row["IsExpense"] else 0, axis=1)

        # Monthly summary
        summary_monthly = df.groupby("Month")[["Revenue", "Expenses"]].sum().reset_index()
        summary_monthly["Profit"] = summary_monthly["Revenue"] - summary_monthly["Expenses"]
        summary_monthly["Revenue MoM %"] = summary_monthly["Revenue"].pct_change().fillna(0) * 100
        summary_monthly["Profit MoM %"] = summary_monthly["Profit"].pct_change().fillna(0) * 100

        st.subheader("\U0001F4C8 Monthly Profit & Loss Summary")
        st.dataframe(summary_monthly)

        # P&L Bar Chart
        st.subheader("\U0001F4C9 P&L Trend by Month")
        fig_pnl = px.bar(summary_monthly, x="Month", y=["Revenue", "Expenses", "Profit"], barmode="group",
                        title="Monthly Revenue, Expenses, and Profit")
        st.plotly_chart(fig_pnl, use_container_width=True)

        # Export
        def convert_df_to_excel(df):
            output = pd.ExcelWriter("output.xlsx", engine='xlsxwriter')
            df.to_excel(output, index=False, sheet_name='P&L')
            output.close()
            with open("output.xlsx", "rb") as f:
                return f.read()

        excel_data = convert_df_to_excel(summary_monthly)
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="P&L_Summary.xlsx">\U0001F4C5 Download P&L Summary as Excel</a>'
        st.markdown(href, unsafe_allow_html=True)
