import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from collections import deque

# --- Page Configuration ---
st.set_page_config(
    page_title="VAYUSAT-1 Ground Control",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
# We use deques to keep the last N data points for smooth plotting
MAX_POINTS = 100
if 'time_data' not in st.session_state:
    st.session_state.time_data = deque(maxlen=MAX_POINTS)
    st.session_state.roll_data = deque(maxlen=MAX_POINTS)
    st.session_state.alt_data = deque(maxlen=MAX_POINTS)
    st.session_state.is_running = False

# --- Sidebar Controls ---
with st.sidebar:
    st.title("⚙️ GSE Controls")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶ Start Rx", use_container_width=True, type="primary")
    with col2:
        stop_btn = st.button("⏹ Stop Rx", use_container_width=True)
        
    if start_btn:
        st.session_state.is_running = True
    if stop_btn:
        st.session_state.is_running = False

    st.markdown("---")
    st.subheader("System Status")
    st.info("I2C Bus: NOMINAL")
    st.success("Battery: 7.8V")
    st.warning("GPS: SEARCHING...")

# --- Main Dashboard Layout ---
st.title("🚀 VAYUSAT-1 Telemetry Dashboard")

# Top Level Metrics
metric_cols = st.columns(4)
alt_metric = metric_cols[0].empty()
vel_metric = metric_cols[1].empty()
roll_metric = metric_cols[2].empty()
canard_metric = metric_cols[3].empty()

# Chart Placeholders
chart_cols = st.columns(2)
roll_chart_placeholder = chart_cols[0].empty()
alt_chart_placeholder = chart_cols[1].empty()

# --- Live Data Loop ---
if st.session_state.is_running:
    # Start time for our mock simulation
    start_time = time.time()
    
    while st.session_state.is_running:
        current_time = time.time() - start_time
        
        # --- 1. MOCK DATA GENERATION (Replace with UDP Listener later) ---
        # Simulating a stabilized roll with some noise
        mock_roll = np.sin(current_time) * 5 + np.random.normal(0, 0.5) 
        # Simulating ascent
        mock_alt = current_time * 50 + np.random.normal(0, 1)
        mock_vel = 50 + np.random.normal(0, 2)
        mock_canard = np.clip(mock_roll * -1.5, -15, 15) # PD response simulation
        
        # --- 2. UPDATE STATE ---
        st.session_state.time_data.append(current_time)
        st.session_state.roll_data.append(mock_roll)
        st.session_state.alt_data.append(mock_alt)
        
        # --- 3. UPDATE METRICS ---
        alt_metric.metric("Altitude (m)", f"{mock_alt:.1f}")
        vel_metric.metric("Velocity (m/s)", f"{mock_vel:.1f}")
        roll_metric.metric("Roll (deg)", f"{mock_roll:.2f}")
        canard_metric.metric("Canard Deflection", f"{mock_canard:.1f}°")
        
        # --- 4. UPDATE CHARTS ---
        # Plotly is used here because it handles dynamic updates cleanly
        roll_fig = go.Figure(data=go.Scatter(
            x=list(st.session_state.time_data), 
            y=list(st.session_state.roll_data),
            mode='lines',
            line=dict(color='#00F1FF', width=3)
        ))
        roll_fig.update_layout(
            title="Roll Stabilization (PD Output)",
            xaxis_title="Time (s)",
            yaxis_title="Roll Angle (°)",
            yaxis_range=[-20, 20],
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )
        roll_chart_placeholder.plotly_chart(roll_fig, use_container_width=True, key="roll_plot")

        alt_fig = go.Figure(data=go.Scatter(
            x=list(st.session_state.time_data), 
            y=list(st.session_state.alt_data),
            mode='lines',
            line=dict(color='#00FF00', width=3),
            fill='tozeroy'
        ))
        alt_fig.update_layout(
            title="Ascent Profile",
            xaxis_title="Time (s)",
            yaxis_title="Altitude (m)",
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )
        alt_chart_placeholder.plotly_chart(alt_fig, use_container_width=True, key="alt_plot")
        
        # --- 5. FRAME RATE LIMITER ---
        time.sleep(0.1) # Limits to ~10Hz for Streamlit stability
else:
    st.info("System Idle. Awaiting 'Start Rx' command to begin telemetry ingestion.")