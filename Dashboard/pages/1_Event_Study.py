import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats

st.set_page_config(page_title="Event Study Analysis", page_icon="📊", layout="wide")

st.title("📊 Event Study Analysis")

st.markdown("""
This page presents the **Essay 2 event study analysis**, examining market reactions to data breach disclosures.
""")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx')
    df['breach_date'] = pd.to_datetime(df['breach_date'])
    df['breach_year'] = df['breach_date'].dt.year
    return df

df = load_data()

# Filter to event study sample
event_study_df = df[df['has_crsp_data'] == True].copy()

st.info(f"📊 Event study sample: **{len(event_study_df)}** breaches with market data")

# ============================================================================
# BASELINE ANALYSIS
# ============================================================================

st.markdown("## 1. Baseline Market Reactions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Mean 5-Day CAR", f"{event_study_df['car_5d'].mean():.4f}%")
    
with col2:
    st.metric("Mean 30-Day CAR", f"{event_study_df['car_30d'].mean():.4f}%")
    
with col3:
    st.metric("Mean 5-Day BHAR", f"{event_study_df['bhar_5d'].mean():.4f}%")
    
with col4:
    st.metric("Mean 30-Day BHAR", f"{event_study_df['bhar_30d'].mean():.4f}%")

st.markdown("---")

# CAR distributions
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Distribution of 5-Day CARs")
    
    fig = go.Figure()
    
    car_5d_data = event_study_df['car_5d'].dropna()
    
    fig.add_trace(go.Histogram(
        x=car_5d_data,
        nbinsx=50,
        marker_color='steelblue',
        opacity=0.7,
        name='5-Day CAR'
    ))
    
    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
    fig.add_vline(x=car_5d_data.mean(), line_dash="dash", line_color="red", line_width=2,
                  annotation_text=f"Mean: {car_5d_data.mean():.2f}%")
    
    # T-test
    t_stat, p_val = stats.ttest_1samp(car_5d_data, 0)
    
    fig.update_layout(
        xaxis_title="CAR (%)",
        yaxis_title="Frequency",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"""
    **Statistical Test (H₀: CAR = 0)**
    - t-statistic: {t_stat:.4f}
    - p-value: {p_val:.4f}
    - Result: {'***' if p_val < 0.01 else '**' if p_val < 0.05 else '*' if p_val < 0.10 else 'Not significant'}
    """)

with col2:
    st.markdown("### Distribution of 30-Day CARs")
    
    fig = go.Figure()
    
    car_30d_data = event_study_df['car_30d'].dropna()
    
    fig.add_trace(go.Histogram(
        x=car_30d_data,
        nbinsx=50,
        marker_color='darkblue',
        opacity=0.7,
        name='30-Day CAR'
    ))
    
    fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
    fig.add_vline(x=car_30d_data.mean(), line_dash="dash", line_color="red", line_width=2,
                  annotation_text=f"Mean: {car_30d_data.mean():.2f}%")
    
    # T-test
    t_stat, p_val = stats.ttest_1samp(car_30d_data, 0)
    
    fig.update_layout(
        xaxis_title="CAR (%)",
        yaxis_title="Frequency",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"""
    **Statistical Test (H₀: CAR = 0)**
    - t-statistic: {t_stat:.4f}
    - p-value: {p_val:.4f}
    - Result: {'***' if p_val < 0.01 else '**' if p_val < 0.05 else '*' if p_val < 0.10 else 'Not significant'}
    """)

# ============================================================================
# DISCLOSURE TIMING
# ============================================================================

st.markdown("---")
st.markdown("## 2. Disclosure Timing Effects")

immediate_car = event_study_df[event_study_df['immediate_disclosure']==1]['car_30d'].dropna()
delayed_car = event_study_df[event_study_df['delayed_disclosure']==1]['car_30d'].dropna()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Immediate Disclosure", 
             f"{len(immediate_car)} breaches",
             delta=f"Mean: {immediate_car.mean():.4f}%")

with col2:
    st.metric("Delayed Disclosure", 
             f"{len(delayed_car)} breaches",
             delta=f"Mean: {delayed_car.mean():.4f}%")

with col3:
    t_stat, p_val = stats.ttest_ind(immediate_car, delayed_car)
    st.metric("Difference", 
             f"{immediate_car.mean() - delayed_car.mean():.4f}%",
             delta=f"p-value: {p_val:.4f}")

# Visualization
col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=immediate_car,
        name='Immediate',
        marker_color='lightgreen',
        boxmean='sd'
    ))
    
    fig.add_trace(go.Box(
        y=delayed_car,
        name='Delayed',
        marker_color='lightcoral',
        boxmean='sd'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    
    fig.update_layout(
        title="CARs by Disclosure Timing",
        yaxis_title="30-Day CAR (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=immediate_car,
        nbinsx=30,
        name='Immediate',
        marker_color='green',
        opacity=0.5
    ))
    
    fig.add_trace(go.Histogram(
        x=delayed_car,
        nbinsx=30,
        name='Delayed',
        marker_color='red',
        opacity=0.5
    ))
    
    fig.add_vline(x=immediate_car.mean(), line_dash="dash", line_color="green", line_width=2)
    fig.add_vline(x=delayed_car.mean(), line_dash="dash", line_color="red", line_width=2)
    fig.add_vline(x=0, line_dash="solid", line_color="black", line_width=1)
    
    fig.update_layout(
        title="Distribution Comparison",
        xaxis_title="30-Day CAR (%)",
        yaxis_title="Frequency",
        barmode='overlay',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# FCC REGULATION
# ============================================================================

st.markdown("---")
st.markdown("## 3. FCC Regulation Effects")

fcc_regulated = event_study_df[event_study_df['fcc_reportable']==1]['car_30d'].dropna()
non_regulated = event_study_df[event_study_df['fcc_reportable']==0]['car_30d'].dropna()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("FCC-Regulated", 
             f"{len(fcc_regulated)} breaches",
             delta=f"Mean: {fcc_regulated.mean():.4f}%")

with col2:
    st.metric("Non-Regulated", 
             f"{len(non_regulated)} breaches",
             delta=f"Mean: {non_regulated.mean():.4f}%")

with col3:
    t_stat, p_val = stats.ttest_ind(fcc_regulated, non_regulated)
    st.metric("Difference", 
             f"{fcc_regulated.mean() - non_regulated.mean():.4f}%",
             delta=f"p-value: {p_val:.4f}")

# Visualization
fig = go.Figure()

fig.add_trace(go.Box(
    y=fcc_regulated,
    name='FCC-Regulated',
    marker_color='lightblue',
    boxmean='sd'
))

fig.add_trace(go.Box(
    y=non_regulated,
    name='Non-Regulated',
    marker_color='lightgray',
    boxmean='sd'
))

fig.add_hline(y=0, line_dash="dash", line_color="black")

fig.update_layout(
    title="CARs by FCC Regulation Status",
    yaxis_title="30-Day CAR (%)",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# HETEROGENEITY ANALYSIS
# ============================================================================

st.markdown("---")
st.markdown("## 4. Heterogeneity Analysis")

st.markdown("### Impact of Enrichment Variables")

# Create tabs for each enrichment
tabs = st.tabs(["Prior Breaches", "Severity", "Exec Turnover", "Regulatory", "Dark Web"])

with tabs[0]:
    st.markdown("### Prior Breach History")
    
    first_time = event_study_df[event_study_df['is_first_breach']==1]['car_30d'].dropna()
    repeat = event_study_df[event_study_df['is_repeat_offender']==1]['car_30d'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=first_time, name='First-Time', marker_color='lightgreen'))
        fig.add_trace(go.Box(y=repeat, name='Repeat Offender', marker_color='lightcoral'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(title="CARs by Prior Breach History", 
                         yaxis_title="30-Day CAR (%)", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        st.metric("First-Time Mean", f"{first_time.mean():.4f}%")
        st.metric("Repeat Offender Mean", f"{repeat.mean():.4f}%")
        
        t_stat, p_val = stats.ttest_ind(first_time, repeat)
        st.metric("Difference", f"{first_time.mean() - repeat.mean():.4f}%",
                 delta=f"p-value: {p_val:.4f}")

with tabs[1]:
    st.markdown("### Breach Severity")
    
    low_severity = event_study_df[event_study_df['high_severity_breach']==0]['car_30d'].dropna()
    high_severity = event_study_df[event_study_df['high_severity_breach']==1]['car_30d'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=low_severity, name='Low Severity', marker_color='lightgreen'))
        fig.add_trace(go.Box(y=high_severity, name='High Severity', marker_color='darkred'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(title="CARs by Breach Severity", 
                         yaxis_title="30-Day CAR (%)", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        st.metric("Low Severity Mean", f"{low_severity.mean():.4f}%")
        st.metric("High Severity Mean", f"{high_severity.mean():.4f}%")
        
        t_stat, p_val = stats.ttest_ind(low_severity, high_severity)
        st.metric("Difference", f"{low_severity.mean() - high_severity.mean():.4f}%",
                 delta=f"p-value: {p_val:.4f}")

with tabs[2]:
    st.markdown("### Executive Turnover")
    
    no_turnover = event_study_df[event_study_df['has_executive_change']==0]['car_30d'].dropna()
    has_turnover = event_study_df[event_study_df['has_executive_change']==1]['car_30d'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=no_turnover, name='No Turnover', marker_color='lightgray'))
        fig.add_trace(go.Box(y=has_turnover, name='Exec Turnover', marker_color='orange'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(title="CARs by Executive Turnover", 
                         yaxis_title="30-Day CAR (%)", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        st.metric("No Turnover Mean", f"{no_turnover.mean():.4f}%")
        st.metric("With Turnover Mean", f"{has_turnover.mean():.4f}%")
        
        t_stat, p_val = stats.ttest_ind(no_turnover, has_turnover)
        st.metric("Difference", f"{no_turnover.mean() - has_turnover.mean():.4f}%",
                 delta=f"p-value: {p_val:.4f}")

with tabs[3]:
    st.markdown("### Regulatory Enforcement")
    
    no_reg = event_study_df[event_study_df['has_any_regulatory_action']==0]['car_30d'].dropna()
    has_reg = event_study_df[event_study_df['has_any_regulatory_action']==1]['car_30d'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=no_reg, name='No Regulatory Action', marker_color='lightgreen'))
        fig.add_trace(go.Box(y=has_reg, name='Regulatory Action', marker_color='darkred'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(title="CARs by Regulatory Action", 
                         yaxis_title="30-Day CAR (%)", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        st.metric("No Action Mean", f"{no_reg.mean():.4f}%")
        st.metric("With Action Mean", f"{has_reg.mean():.4f}%")
        
        t_stat, p_val = stats.ttest_ind(no_reg, has_reg)
        st.metric("Difference", f"{no_reg.mean() - has_reg.mean():.4f}%",
                 delta=f"p-value: {p_val:.4f}")

with tabs[4]:
    st.markdown("### Dark Web Presence")
    
    not_hibp = event_study_df[event_study_df['in_hibp']==0]['car_30d'].dropna()
    in_hibp = event_study_df[event_study_df['in_hibp']==1]['car_30d'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=not_hibp, name='Not in HIBP', marker_color='lightgreen'))
        fig.add_trace(go.Box(y=in_hibp, name='In HIBP', marker_color='darkred'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(title="CARs by Dark Web Presence", 
                         yaxis_title="30-Day CAR (%)", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        st.metric("Not in HIBP Mean", f"{not_hibp.mean():.4f}%")
        st.metric("In HIBP Mean", f"{in_hibp.mean():.4f}%")
        
        if len(in_hibp) > 0:
            t_stat, p_val = stats.ttest_ind(not_hibp, in_hibp)
            st.metric("Difference", f"{not_hibp.mean() - in_hibp.mean():.4f}%",
                     delta=f"p-value: {p_val:.4f}")

# ============================================================================
# SUMMARY
# ============================================================================

st.markdown("---")
st.markdown("## 📋 Key Findings Summary")

st.markdown("""
<div style='background-color: #e8f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;'>
<h4>Main Results:</h4>
<ul>
    <li><b>Baseline Effect:</b> Data breaches result in significant negative market reactions</li>
    <li><b>Disclosure Timing:</b> Immediate disclosure shows different market reactions than delayed disclosure</li>
    <li><b>FCC Regulation:</b> Regulated firms show distinct patterns in market reactions</li>
    <li><b>Heterogeneity:</b> Effects vary by prior breach history, severity, governance, and enforcement</li>
</ul>
</div>
""", unsafe_allow_html=True)