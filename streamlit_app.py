import streamlit as st
import pandas as pd
import openai
import os

# Set OpenAI API Key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# App title and instructions
st.set_page_config(page_title="AI Financial Analyst", layout="centered")
st.title("AI Financial Analyst")
st.write("Upload your P&L CSV file and get a summary of your financial performance.")

# Upload CSV
uploaded_file = st.file_uploader("Upload your Profit & Loss CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("📊 Preview of Uploaded Data")
    st.dataframe(df)

    # Required columns check
    required_columns = ["Month", "Revenue", "COGS", "Operating Expenses", "Net Profit"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"Your CSV must contain these columns: {', '.join(required_columns)}")
    else:
        # Convert CSV data to string for GPT
        csv_string = df.to_csv(index=False)

        # Build GPT prompt
        prompt = f"""
You are a helpful financial analyst. Review the following SME profit & loss data:

{csv_string}

1. Summarize key trends in plain English.
2. Calculate and display:
   - Total revenue and month-over-month change
   - Gross margin %
   - Net profit %
   - Operating expenses as % of revenue
   - Monthly burn rate (if applicable)
   - Estimated cash runway (assume £25,000 in bank)
3. Flag any risks or anomalies.
4. Make 1–2 recommendations for improvement.

Be friendly and clear. Use simple language.
"""

        st.subheader("📈 AI Analysis")
        with st.spinner("Analyzing your financials..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a financial analyst for small businesses."},
                        {"role": "user", "content": prompt}
                    ]
                )
                summary = response.choices[0].message.content
                st.markdown(summary)
            except Exception as e:
                st.error(f"Error: {e}")
