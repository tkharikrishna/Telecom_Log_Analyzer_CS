# === Imports ===
import streamlit as st
import pandas as pd
import re
from datetime import datetime
import dateparser
import dateparser.search
from collections import Counter
from anomaly_agent import AnomalyAgent
from ml_anomaly_agent import MLAnomalyAgent
# === Streamlit UI ===
st.set_page_config(layout="wide")
st.title("📡 AI-Powered Telecom Log Analyzer")
# === File Upload ===
uploaded_file = st.file_uploader("Upload your log file (.txt)", type=["txt"])
logs = uploaded_file.read().decode("utf-8", errors="ignore") if uploaded_file else ""
# === Tab Layout ===
tabs = st.tabs(["🔍 Anomaly Detection", "💬 Ask a Question"])
# === TAB 1: Anomaly Detection ===
with tabs[0]:
   if logs:
       # --- Keyword-Based Anomalies ---
       st.subheader("🔎 Keyword-Based Anomaly Detection")
       agent = AnomalyAgent()
       keyword_anomalies = agent.detect(logs)
       def find_nearest_timestamp(index, all_lines):
           for i in range(index, -1, -1):
               match = re.search(r'AP time:\s*(\d{8}_\d{6})', all_lines[i])
               if match:
                   return match.group(1)
           return "N/A"
       if keyword_anomalies:
           log_lines = logs.splitlines()
           parsed_rows = []
           for anomaly_line in keyword_anomalies:
               try:
                   idx = log_lines.index(anomaly_line)
               except ValueError:
                   continue
               ts = find_nearest_timestamp(idx, log_lines)
               parsed_rows.append({"Timestamp": ts, "Anomaly Line": anomaly_line.strip()})
           df_kw = pd.DataFrame(parsed_rows)
           st.dataframe(df_kw, use_container_width=True)
       else:
           st.info("No keyword-based anomalies detected.")
       # --- ML-Based Anomalies ---
       st.subheader("🧠 ML-Based Anomaly Detection (Isolation Forest)")
       ml_agent = MLAnomalyAgent()
       ml_anomalies = ml_agent.detect(logs)
       if ml_anomalies:
           st.success(f"✅ {len(ml_anomalies)} anomalies detected")
           parsed_data = []
           current_ts = ""
           for i, line in enumerate(ml_anomalies):
               ts_match = re.search(r'AP time:\s*(\d{8}_\d{6})', line)
               if ts_match:
                   current_ts = ts_match.group(1)
               ip_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', line)
               ip = ip_match.group(1) if ip_match else ""
               rp_match = re.search(r'RP\s*[:\-]?\s*(\d+)', line)
               rp = f"RP {rp_match.group(1)}" if rp_match else ""
               parsed_data.append({
                   "Timestamp": current_ts,
                   "IP": ip,
                   "RP": rp,
                   "Anomaly Line": line.strip()
               })
           df = pd.DataFrame(parsed_data)
           st.dataframe(df, use_container_width=True)
           # --- Summary Section ---
           st.markdown("### 📊 Anomaly Summary")
           col1, col2, col3 = st.columns(3)
           if "IP" in df.columns:
               ip_counts = df["IP"].value_counts().head(10)
               with col1:
                   st.markdown("#### 🔁 Top IPs")
                   st.dataframe(ip_counts.rename("Count"))
           if "RP" in df.columns:
               rp_counts = df["RP"].value_counts().head(10)
               with col2:
                   st.markdown("#### 🧩 Top RPs")
                   st.dataframe(rp_counts.rename("Count"))
           time_counts = df["Timestamp"].value_counts().head(10)
           with col3:
               st.markdown("#### 🕒 Top Timestamps")
               st.dataframe(time_counts.rename("Count"))
           # --- Most Frequent Patterns (IP/RP/Error Codes) ---
           st.markdown("### 🔍 Top Repeated Patterns in Anomalies")
           def extract_significant_terms(text):
               return re.findall(
                   r"(RP\s*\d+|\d{1,3}(?:\.\d{1,3}){3}|H'[A-Fa-f0-9]+|timeout|fail|reset|snmpCallback|[a-zA-Z_]+\.(?:cpp|cxx|py))",
                   text
               )
           term_counter = Counter()
           for line in df["Anomaly Line"]:
               term_counter.update(extract_significant_terms(line))
           top_terms_df = pd.DataFrame(term_counter.most_common(15), columns=["Pattern", "Count"])
           st.dataframe(top_terms_df, use_container_width=True)
       else:
           st.info("No ML-based anomalies detected.")

# === TAB 2: Ask a Question ===
with tabs[1]:
   if logs:
       st.subheader("💬 Ask a Custom Question (Powered by Ollama LLM)")
       query = st.text_input("Ask a question about the logs (e.g. Did RP 48 fail?)")
       if query:
           try:
               from langchain_community.llms import Ollama
               from langchain.prompts import PromptTemplate
               from langchain.chains import LLMChain
               # Load Ollama LLM (no key needed)
               llm = Ollama(model="mistral")  # You can change to llama2, codellama, etc.
               # Define prompt template
               prompt = PromptTemplate(
                   input_variables=["log_data", "query"],
                   template="""
You are a telecom log analysis assistant.
LOG DATA:
{log_data}
USER QUESTION:
{query}
Based on the logs, answer clearly and concisely.
Mention timestamps, RPs, IPs or error types if relevant.
"""
               )
               # Run LangChain chain
               chain = LLMChain(llm=llm, prompt=prompt)
               with st.spinner("Thinking..."):
                   response = chain.run({"log_data": logs[:3000], "query": query})  # slice to fit input
                   st.success("Answer:")
                   st.write(response)
           except Exception as e:
               st.error(f"❌ Error running LangChain with Ollama: {e}")
