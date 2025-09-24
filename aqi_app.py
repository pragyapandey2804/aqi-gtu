import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# Helper functions
# -----------------------------
def clamp(val, min_val=0, max_val=300):
    return max(min_val, min(max_val, val))

def get_aqi_status(aqi):
    if aqi <= 50:
        return "Good", "green", "Air quality is good. Enjoy outdoor activities!"
    elif aqi <= 100:
        return "Moderate", "yellow", "Air quality is moderate. Sensitive people may reduce prolonged outdoor exertion."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "orange", "Sensitive groups should limit outdoor activities."
    elif aqi <= 200:
        return "Unhealthy", "red", "Air quality is unhealthy. Wear a mask if going outside."
    elif aqi <= 300:
        return "Very Unhealthy", "purple", "Avoid outdoor activities. Wear a proper mask if necessary."
    else:
        return "Hazardous", "maroon", "Stay indoors! Air quality is hazardous."

def get_color_for_aqi(aqi):
    return get_aqi_status(aqi)[1]

# -----------------------------
# Streamlit page
# -----------------------------
st.set_page_config(page_title="Dynamic AQI Dashboard", layout="wide")
st.title("🌍 Dynamic AQI Dashboard - Single Location")

# Sidebar
st.sidebar.header("Settings")
location = st.sidebar.text_input("Location", "Delhi")

if "live_update" not in st.session_state:
    st.session_state.live_update = True
toggle = st.sidebar.checkbox("Live Updates (10 sec)", value=st.session_state.live_update)
st.session_state.live_update = toggle
if st.session_state.live_update:
    st_autorefresh(interval=10000, key="aqi_autorefresh")

# -----------------------------
# Initialize AQI history
# -----------------------------
if "history" not in st.session_state:
    base_aqi = 120
    st.session_state.history = pd.DataFrame({
        "Time": list(range(20)),
        "AQI": [clamp(base_aqi + random.randint(-5,5)) for _ in range(20)]
    })

# -----------------------------
# Update AQI
# -----------------------------
history = st.session_state.history
new_aqi = clamp(history["AQI"].iloc[-1] + random.randint(-5,5))
new_row = pd.DataFrame({"Time": [history["Time"].iloc[-1]+1], "AQI": [new_aqi]})
st.session_state.history = pd.concat([history, new_row], ignore_index=True).tail(8)

# -----------------------------
# Layout
# -----------------------------
col1, col2 = st.columns([1,2])

with col1:
    # AQI Card with emoji
    status, color, suggestion = get_aqi_status(new_aqi)
    
    # Choose emoji based on AQI
    if new_aqi <= 50:
        emoji = "🌞"
    elif new_aqi <= 100:
        emoji = "😊"
    elif new_aqi <= 150:
        emoji = "😐"
    elif new_aqi <= 200:
        emoji = "😷"
    elif new_aqi <= 300:
        emoji = "🤢"
    else:
        emoji = "☠️"
    
    st.metric(label=f"Current AQI - {location} {emoji}", value=new_aqi, delta=status)
    
    # AQI suggestion
    st.markdown(f"**Suggestion:** {suggestion}")

    # AQI Categories
    st.markdown("### AQI Categories")
    st.markdown("""
    - **0-50:** Good 🟢  
    - **51-100:** Moderate 🟡  
    - **101-150:** Unhealthy for Sensitive Groups 🟠  
    - **151-200:** Unhealthy 🔴  
    - **201-300:** Very Unhealthy 🟣  
    - **300+:** Hazardous 🟤  
    """)

    st.write("")
    st.write("")

    # Past 20 readings as colored boxes
    st.markdown("### Last 8 AQI Readings")
    readings = st.session_state.history['AQI'].tolist()
    num_per_row = 4

    for i in range(0, len(readings), num_per_row):
        row = readings[i:i+num_per_row]
        cols = st.columns(len(row))
        for j, val in enumerate(row):
            _, c, _ = get_aqi_status(val)
            cols[j].markdown(
                f"<div style='background-color:{c};color:white;text-align:center;padding:6px;border-radius:6px'>{val}</div>",
                unsafe_allow_html=True
            )

    st.write("")  # empty line
    

    # AQI Legend with colors and emojis
    st.markdown("### AQI Legend")
    legend_html = """
    <div style="display:flex; flex-wrap:wrap; gap:8px;">
        <div style="background-color:green;color:white;padding:6px;border-radius:6px;text-align:center;">0-50 🌞 Good</div>
        <div style="background-color:yellow;color:black;padding:6px;border-radius:6px;text-align:center;">51-100 😊 Moderate</div>
        <div style="background-color:orange;color:white;padding:6px;border-radius:6px;text-align:center;">101-150 😐 Unhealthy for Sensitive Groups</div>
        <div style="background-color:red;color:white;padding:6px;border-radius:6px;text-align:center;">151-200 😷 Unhealthy</div>
        <div style="background-color:purple;color:white;padding:6px;border-radius:6px;text-align:center;">201-300 🤢 Very Unhealthy</div>
        <div style="background-color:maroon;color:white;padding:6px;border-radius:6px;text-align:center;">300+ ☠️ Hazardous</div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    st.write("")

    # Max / Min AQI
    st.markdown(f"- Max AQI today: {st.session_state.history['AQI'].max()}")
    st.markdown(f"- Min AQI today: {st.session_state.history['AQI'].min()}")

with col2:
    # Dynamic line chart with color segments
    times = st.session_state.history["Time"].tolist()
    aqi_values = st.session_state.history["AQI"].tolist()
    fig = go.Figure()

    for i in range(len(times)-1):
        seg_color = get_color_for_aqi(aqi_values[i])
        fig.add_trace(go.Scatter(
            x=[times[i], times[i+1]],
            y=[aqi_values[i], aqi_values[i+1]],
            mode='lines+markers',
            line=dict(color=seg_color, width=4),
            marker=dict(size=8),
            hoverinfo='text',
            text=[f"AQI: {aqi_values[i]}<br>Status: {get_aqi_status(aqi_values[i])[0]}<br>Suggestion: {get_aqi_status(aqi_values[i])[2]}",
                  f"AQI: {aqi_values[i+1]}<br>Status: {get_aqi_status(aqi_values[i+1])[0]}<br>Suggestion: {get_aqi_status(aqi_values[i+1])[2]}"]
        ))

    fig.update_layout(title=f"AQI Trend - {location}", xaxis_title="Time", yaxis_title="AQI", showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"line_chart_{new_aqi}")

    st.write("")

    # Donut chart
    fig_donut = px.pie(
        values=[new_aqi, 300 - new_aqi],
        names=["Current AQI", "Remaining to Max"],
        hole=0.6,
        color_discrete_sequence=[color, "lightgrey"]
    )
    fig_donut.update_traces(textinfo="none")
    st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_chart_{new_aqi}")

# -----------------------------
# About / Info
# -----------------------------
st.markdown("---")
st.markdown("""
### ℹ️ About this Prototype
This dashboard simulates a **Smart AQI Monitoring System**:

- **Sensor** → MQ135 + ESP32  
- **Communication** → 4G SIM / LoRaWAN (MQTT protocol)  
- **Cloud** → AWS IoT Core + Lambda + DynamoDB  
- **Visualization** → Web Dashboard (this prototype shows random AQI data for demonstration)

⚠️ *Note: All AQI data here is randomly generated and for demonstration purposes only.*
""")
