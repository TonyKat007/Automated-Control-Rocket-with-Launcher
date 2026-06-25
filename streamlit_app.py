import streamlit as st
import pandas as pd
import numpy as np
import time
import datetime
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

# --- App Configuration ---
st.set_page_config(
    page_title="VAYUSAT-1 Advanced Ground Control",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 VAYUSAT-1 Mission Control Center")
st.markdown("""
Welcome to the **VAYUSAT-1 Ground Control Dashboard**. 
Monitor real-time telemetry, track launch range safety, simulate aerodynamic stability, and analyze post-flight logs.
---
""")

# --- Create Main Feature Tabs (Inspired by your Cosmic Ray Dashboard) ---
tabs = st.tabs([
    "🛰️ Live Telemetry", 
    "🗺️ Range Safety & Tracking", 
    "🧮 PD Controller Simulation", 
    "📊 Post-Flight Log Analyzer"
])

# ==========================================
# TAB 1: LIVE TELEMETRY 
# ==========================================
with tabs[0]:
    st.subheader("Real-Time Flight Telemetry")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ GSE Controls")
        col1, col2 = st.columns(2)
        start_btn = col1.button("▶ Start Rx", type="primary")
        stop_btn = col2.button("⏹ Stop Rx")
        
        if 'is_running' not in st.session_state:
            st.session_state.is_running = False
            
        if start_btn: st.session_state.is_running = True
        if stop_btn: st.session_state.is_running = False

        st.markdown("---")
        st.subheader("System Health")
        st.success("Battery: 7.8V (NOMINAL)")
        st.info("I2C Bus: ACTIVE")
        st.warning("Wind Speed: 4.2 m/s")

    # Metrics Layout
    m1, m2, m3, m4 = st.columns(4)
    alt_metric = m1.empty()
    vel_metric = m2.empty()
    roll_metric = m3.empty()
    canard_metric = m4.empty()

    # Chart Layout
    c1, c2 = st.columns(2)
    roll_chart = c1.empty()
    alt_chart = c2.empty()

    if st.session_state.is_running:
        if 't_data' not in st.session_state:
            st.session_state.t_data, st.session_state.r_data, st.session_state.a_data = [], [], []
            st.session_state.start_time = time.time()
            
        current_time = time.time() - st.session_state.start_time
        
        # Mock Telemetry Generator
        mock_roll = np.sin(current_time * 2) * 8 * np.exp(-current_time/5) + np.random.normal(0, 0.5)
        mock_alt = (current_time ** 2) * 15 if current_time < 10 else 1500 - ((current_time-10)**2)*5
        mock_vel = current_time * 30 if current_time < 10 else 300 - (current_time-10)*10
        mock_canard = np.clip(mock_roll * -1.2, -15, 15)

        st.session_state.t_data.append(current_time)
        st.session_state.r_data.append(mock_roll)
        st.session_state.a_data.append(max(0, mock_alt))

        # Keep lists manageable
        if len(st.session_state.t_data) > 100:
            st.session_state.t_data.pop(0)
            st.session_state.r_data.pop(0)
            st.session_state.a_data.pop(0)

        # Update UI
        alt_metric.metric("Altitude (m)", f"{max(0, mock_alt):.1f}")
        vel_metric.metric("Velocity (m/s)", f"{mock_vel:.1f}")
        roll_metric.metric("Roll Error (°)", f"{mock_roll:.2f}")
        canard_metric.metric("Canard Cmd (°)", f"{mock_canard:.1f}")

        # Plotly Charts
        fig_r = go.Figure(go.Scatter(x=st.session_state.t_data, y=st.session_state.r_data, mode='lines', line=dict(color='#00F1FF')))
        fig_r.update_layout(title="Active Roll Stabilization", height=300, margin=dict(l=0,r=0,t=30,b=0), yaxis_range=[-20, 20])
        roll_chart.plotly_chart(fig_r, use_container_width=True)

        fig_a = go.Figure(go.Scatter(x=st.session_state.t_data, y=st.session_state.a_data, mode='lines', fill='tozeroy', line=dict(color='#00FF00')))
        fig_a.update_layout(title="Flight Trajectory", height=300, margin=dict(l=0,r=0,t=30,b=0))
        alt_chart.plotly_chart(fig_a, use_container_width=True)
        
        time.sleep(0.1)
        st.rerun()
    else:
        st.info("Awaiting telemetry stream. Press 'Start Rx' in the sidebar.")


# ==========================================
# TAB 2: RANGE SAFETY & MAP 
# ==========================================
with tabs[1]:
    st.subheader("Range Safety & Vehicle Tracking")
    st.markdown("Live GPS tracking of the launch vehicle for recovery operations.")
    
    # Map coordinates (Assuming a launch pad location)
    pad_lat, pad_lon = 13.733, 80.235 # Sriharikota
    
    m = folium.Map(location=[pad_lat, pad_lon], zoom_start=14)
    
    # Launch Pad Marker
    folium.CircleMarker(
        location=[pad_lat, pad_lon],
        radius=10,
        color="red",
        fill=True,
        popup="Launch Pad"
    ).add_to(m)
    
    # Simulated Rocket Location Marker
    folium.Marker(
        [pad_lat + 0.005, pad_lon + 0.002],
        popup="VAYUSAT-1 (Current Pos)",
        icon=folium.Icon(color="blue", icon="rocket", prefix='fa')
    ).add_to(m)
    
    # Hazard Zone
    folium.Circle(
        location=[pad_lat, pad_lon],
        radius=2000,
        color="orange",
        fill=True,
        fill_opacity=0.2,
        popup="2km Hazard Exclusion Zone"
    ).add_to(m)

    folium_static(m, width=1000, height=500)


# ==========================================
# TAB 3: PD CONTROLLER SIMULATION
# ==========================================
with tabs[2]:
    st.subheader("Control Law Simulator")
    st.markdown("Test your Proportional-Derivative (PD) gains before uploading them to the ESP32.")
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("**Tune Gains**")
        kp = st.slider("Proportional Gain (Kp)", 0.1, 5.0, 1.25, step=0.05)
        kd = st.slider("Derivative Gain (Kd)", 0.0, 2.0, 0.45, step=0.05)
        disturbance = st.slider("Initial Wind Gust Roll Error (°)", 5, 45, 15)
        
    with col_b:
        # Simulate PD response (Damped harmonic oscillator)
        t = np.linspace(0, 5, 200)
        omega_n = np.sqrt(kp)
        zeta = kd / (2 * omega_n) if omega_n > 0 else 0
        
        if zeta < 1: # Underdamped
            wd = omega_n * np.sqrt(1 - zeta**2)
            response = disturbance * np.exp(-zeta * omega_n * t) * (np.cos(wd * t) + (zeta * omega_n / wd) * np.sin(wd * t))
        else: # Overdamped/Critically damped
            response = disturbance * np.exp(-omega_n * t) * (1 + omega_n * t)
            
        fig_sim, ax_sim = plt.subplots(figsize=(8, 4))
        ax_sim.plot(t, response, color='purple', linewidth=2)
        ax_sim.axhline(0, color='black', linestyle='--')
        ax_sim.set_title("Simulated Roll Correction")
        ax_sim.set_xlabel("Time (s)")
        ax_sim.set_ylabel("Roll Angle (°)")
        ax_sim.grid(True)
        st.pyplot(fig_sim)
        
        if zeta < 0.5: st.warning("⚠️ System is highly underdamped. Expect aggressive oscillation.")
        elif zeta > 1.2: st.warning("⚠️ System is sluggish (overdamped).")
        else: st.success("✅ System is near critically damped. Good tuning.")


# ==========================================
# TAB 4: CSV ANALYZER (Based on Source code)
# ==========================================
with tabs[3]:
    st.subheader("📤 Post-Flight Log Analyzer")
    st.markdown("Upload the `.csv` telemetry dumps extracted from the ESP32 SPIFFS memory for forensic analysis.")
    
    uploaded_file = st.file_uploader("Upload Flight Log (CSV)", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"Log loaded! Shape: {df.shape[0]} samples × {df.shape[1]} variables")

            st.markdown("### Preview")
            st.dataframe(df.head())

            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

            if numeric_cols:
                # Custom Plot Builder inspired by your code
                st.markdown("### Flight Data Plotter")
                cc1, cc2 = st.columns(2)
                x_axis = cc1.selectbox("Select X-axis (Usually Time)", options=numeric_cols)
                y_axis = cc2.selectbox("Select Y-axis", options=numeric_cols, index=1 if len(numeric_cols)>1 else 0)
                
                fig_custom = px.line(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                st.plotly_chart(fig_custom, use_container_width=True)
                
                st.markdown("### Sensor Correlation Matrix")
                fig_corr, ax_corr = plt.subplots(figsize=(8, 4))
                sns.heatmap(df[numeric_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax_corr)
                st.pyplot(fig_corr)

        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- Footer ---
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: gray;">
      VAYUSAT-1 Mission Control | Local Time: {datetime.datetime.now().strftime("%B %d, %Y - %H:%M")} IST
    </div>
    """,
    unsafe_allow_html=True
)
