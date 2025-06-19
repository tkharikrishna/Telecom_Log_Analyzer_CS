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
tabs = st.tabs(["🔍 Anomaly Detection", "💬 Ask a Question", "🕒 Time-Based Search"])
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
# === TAB 2: Natural Question Placeholder ===
with tabs[1]:
   if logs:
       st.subheader("💬 Ask a Custom Question")
       query = st.text_input("e.g. Did RP 48 fail last night?")
       if query:
           st.warning("This part is currently disabled (RCA/GPT removed as per request).")
# === TAB 3: Time-Based Log Search ===
with tabs[2]:
   if logs:
       import streamlit as st
import re
from datetime import datetime
import dateparser
import dateparser.search
st.subheader("🕒 Time-Based Log Search")
query = st.text_input("Ask: e.g. Any events between 03:00 and 04:00 on May 10 2024 (24hr format)")
# --- Block extractor around AP time ---
def extract_blocks(log_text, window_lines=5):
   lines = log_text.splitlines()
   blocks = []
   for i in range(len(lines)):
       if 'AP time:' in lines[i]:
           block = "\n".join(lines[i:i+window_lines])
           blocks.append(block)
   return blocks
# --- Timestamp extractor from block ---
def extract_timestamp_from_block(block):
   match = re.search(r'AP time:\s*(\d{8}_\d{6})', block)
   if match:
       try:
           return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
       except:
           return None
   return None
if query:
   start_time = end_time = None
   blocks = extract_blocks(logs, window_lines=5)
   # Extract date from user query
   dates = dateparser.search.search_dates(query)
   times = re.findall(r'\d{1,2}[:.]\d{2}', query)
   if "between" in query and "and" in query and len(times) >= 2:
       if dates:
           full_date = dates[0][1].strftime("%Y-%m-%d")
           start_time = dateparser.parse(f"{full_date} {times[0]}")
           end_time = dateparser.parse(f"{full_date} {times[1]}")
   elif dates:
       start_time = dates[0][1]
   matched_blocks = []
   for block in blocks:
       ts = extract_timestamp_from_block(block)
       if not ts:
           continue
       # ⬇️ Strict year + full datetime match
       in_time = False
       if start_time and end_time:
           in_time = (
               ts.year == start_time.year and
               start_time <= ts <= end_time
           )
       elif start_time:
           in_time = ts.date() == start_time.date() and ts.year == start_time.year
       if in_time:
           matched_blocks.append((ts.strftime("%Y-%m-%d %H:%M:%S"), block))
   if matched_blocks:
       st.success(f"✅ Found {len(matched_blocks)} event(s) in specified time range:")
       for ts, blk in matched_blocks:
           st.markdown(f"**🕒 {ts}**")
           st.code(blk, language="text")
   else:
       st.warning("No events found in the given time window.")