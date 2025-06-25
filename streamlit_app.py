import streamlit as st
import pandas as pd
import plotly.express as px
import base64

st.set_page_config(page_title="AI Trial Balance Analyzer", layout="wide")
st.title("📊 AI Trial Balance Analyzer")
st.write("Upload your monthly Trial Balance CSV to view financials and insights.")

uploaded_file = st.file_uploader("Upload your Trial Balance CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📄 Raw Trial Balance")
    st.dataframe(df)

    required_columns = ["Month", "Account Name", "Debit", "Credit"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"Your CSV must contain these columns: {', '.join(required_columns)}")
    else:
        df["Net"] = df["Debit"].fillna(0) - df["Credit"].fillna(0)

        df["Category"] = df["Account Name"].apply(
            lambda x: "Balance Sheet" if isinstance(x, str) and any(
                k in x.lower() for k in ["receivable", "payable", "cash", "asset", "liability", "equity"]
            ) else "P&L"
        )

        # Add Tag column based on common keywords
        def assign_tag(account):
            account = str(account).lower()
            if "salary" in account or "wages" in account:
                return "Payroll"
            elif "rent" in account:
                return "Facilities"
            elif "utilities" in account or "electric" in account:
                return "Utilities"
            elif "loan" in account:
                return "Financing"
            elif "revenue" in account or "sales" in account:
                return "Revenue"
            elif "equipment" in account or "asset" in account:
                return "Fixed Asset"
            else:
                return "Other"

        df["Tag"] = df["Account Name"].apply(assign_tag)

        # Filter selector
        month_options = df["Month"].dropna().unique().tolist()
        selected_month = st.selectbox("📅 Select Month to Filter", ["All"] + month_options)
        df_filtered = df if selected_month == "All" else df[df["Month"] == selected_month]

        total_net = df_filtered["Net"].sum()
        st.markdown(f"### 🔢 Trial Balance Check: {'✅ Balanced' if abs(total_net) < 0.01 else '❌ Not Balanced'} (Total = {total_net:.2f})")

        # Stacked bar for monthly debits and credits
        st.subheader("📊 Monthly Trial Balance Totals")
        tb_chart = df.groupby(["Month"]).agg({"Debit": "sum", "Credit": "sum"}).reset_index()
        fig_tb = px.bar(tb_chart, x="Month", y=["Debit", "Credit"], barmode="group", title="Debits vs Credits by Month")
        st.plotly_chart(fig_tb, use_container_width=True)

        pnl_summary_data = df.copy()
        revenue_filter = pnl_summary_data["Account Name"].fillna("").str.lower().str.contains("revenue|sales|turnover")
        pnl_summary_data["Revenue"] = pnl_summary_data["Net"].where(revenue_filter, 0) * -1
        pnl_summary_data["Expenses"] = pnl_summary_data["Net"].where(~revenue_filter & (pnl_summary_data["Category"] == "P&L"), 0).abs()

        summary_monthly = pnl_summary_data.groupby("Month").agg({"Revenue": "sum", "Expenses": "sum"}).reset_index()
        summary_monthly["Profit"] = summary_monthly["Revenue"] - summary_monthly["Expenses"]

        summary_monthly["Revenue MoM %"] = summary_monthly["Revenue"].pct_change().fillna(0) * 100
        summary_monthly["Profit MoM %"] = summary_monthly["Profit"].pct_change().fillna(0) * 100

        latest = summary_monthly.iloc[-1]
        prev = summary_monthly.iloc[-2] if len(summary_monthly) > 1 else latest

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Revenue", f"£{latest['Revenue']:,.0f}", f"{latest['Revenue MoM %']:.1f}%")
        with col2:
            st.metric("📉 Profit", f"£{latest['Profit']:,.0f}", f"{latest['Profit MoM %']:.1f}%")
        with col3:
            burn = abs(latest["Expenses"])
            runway = 25000 / burn if burn else float('inf')
            st.metric("🏃‍♂️ Est. Runway", f"{runway:.1f} months")

        balance_sheet = df_filtered[df_filtered["Category"] == "Balance Sheet"].copy()
        profit_loss = df_filtered[df_filtered["Category"] == "P&L"].copy()

        st.subheader("📈 Balance Sheet")
        bs_grouped = balance_sheet.groupby(["Account Name"])["Net"].sum().reset_index()
        fig_bs = px.bar(bs_grouped, x="Account Name", y="Net", title="Balance Sheet Composition")
        st.plotly_chart(fig_bs, use_container_width=True)

        st.subheader("📉 Profit & Loss")
        revenue = df_filtered[revenue_filter].groupby("Account Name")["Net"].sum().reset_index(name="Revenue")
        expenses = df_filtered[(df_filtered["Category"] == "P&L") & ~revenue_filter].groupby("Account Name")["Net"].sum().reset_index(name="Expense")

        fig_exp = px.bar(expenses, x="Account Name", y="Expense", title="Expense Breakdown")
        st.plotly_chart(fig_exp, use_container_width=True)

        st.subheader("🏷️ Tagged Summary")
        tag_summary = df.groupby(["Month", "Tag"])["Net"].sum().reset_index()
        fig_tag = px.bar(tag_summary, x="Month", y="Net", color="Tag", barmode="stack", title="Net Activity by Tag")
        st.plotly_chart(fig_tag, use_container_width=True)

        assumed_cash = 25000
        pnl_summary = summary_monthly.copy()
        pnl_summary["Monthly Burn"] = pnl_summary["Expenses"].apply(lambda x: abs(x))
        pnl_summary["Estimated Runway (months)"] = pnl_summary["Monthly Burn"].apply(lambda x: assumed_cash / x if x else float('inf'))

        st.subheader("🧾 P&L Table with Runway")
        st.dataframe(pnl_summary)

        def convert_df_to_excel(df):
            output = pd.ExcelWriter("output.xlsx", engine='xlsxwriter')
            df.to_excel(output, index=False, sheet_name='P&L')
            output.close()
            with open("output.xlsx", "rb") as f:
                return f.read()

        excel_data = convert_df_to_excel(pnl_summary)
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="P&L_Summary.xlsx">📥 Download P&L Summary as Excel</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.subheader("📢 AI Financial Commentary")
        st.info("🧠 AI commentary temporarily disabled to avoid OpenAI charges. Enable it again once you're ready.")
