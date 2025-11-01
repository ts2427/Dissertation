import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Data Breach Analytics Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# GLOBAL CSS - ONLY CUSTOM STYLES REMAIN
# ===============================
# The lines forcing 'color: #0B2740 !important;' are REMOVED.
# The custom classes for headers and boxes are KEPT.
st.markdown("""
<style>
/* Streamlit's default theme will now control text color. */

.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4; 
    text-align: center;
    padding: 1rem 0;
    margin-bottom: 2rem;
}
.metric-card {
    /* Background kept light for contrast against the dark default theme */
    background-color: #f0f2f6; 
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
}
.highlight-box {
    /* Background kept light for contrast against the dark default theme */
    background-color: #e8f4f8;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 1rem 0;
}
.stTabs [data-baseweb="tab-list"] { gap: 2rem; }
</style>
""", unsafe_allow_html=True)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    try:
        with st.spinner('Loading and processing data...'):
            df = pd.read_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')
            df['breach_date'] = pd.to_datetime(df['breach_date'])
            df['breach_year'] = df['breach_date'].dt.year
            return df
    except FileNotFoundError:
        st.error("❌ Dataset not found! Ensure FINAL_DISSERTATION_DATASET_ENRICHED.xlsx is in Data/processed/")
        return None

df = load_data()
if df is None:
    st.stop()

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Data+Breach+Analytics", use_container_width=True)
st.sidebar.markdown("## 🔍 Filters")

# Year filter
year_range = st.sidebar.slider(
    "Select Year Range",
    int(df['breach_year'].min()),
    int(df['breach_year'].max()),
    (int(df['breach_year'].min()), int(df['breach_year'].max()))
)

# FCC filter
fcc_filter = st.sidebar.multiselect(
    "FCC Regulation Status",
    ["All", "FCC-Regulated", "Non-Regulated"],
    default=["All"]
)

# Disclosure timing filter
disclosure_filter = st.sidebar.multiselect(
    "Disclosure Timing",
    ["All", "Immediate", "Delayed"],
    default=["All"]
)

# Apply filters
filtered_df = df[
    (df['breach_year'] >= year_range[0]) & 
    (df['breach_year'] <= year_range[1])
].copy()

if "FCC-Regulated" in fcc_filter and "Non-Regulated" not in fcc_filter:
    filtered_df = filtered_df[filtered_df['fcc_reportable'] == 1]
elif "Non-Regulated" in fcc_filter and "FCC-Regulated" not in fcc_filter:
    filtered_df = filtered_df[filtered_df['fcc_reportable'] == 0]

if "Immediate" in disclosure_filter and "Delayed" not in disclosure_filter:
    filtered_df = filtered_df[filtered_df['immediate_disclosure'] == 1]
elif "Delayed" in disclosure_filter and "Immediate" not in disclosure_filter:
    filtered_df = filtered_df[filtered_df['delayed_disclosure'] == 1]

st.sidebar.markdown("---")
st.sidebar.info(f"**Showing {len(filtered_df)} of {len(df)} breaches**")

# ===============================
# MAIN HEADER
# ===============================
# Removed redundant H1 markdown header
st.markdown("<h1 class='main-header'>🔒 Data Breach Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("""
<div class='highlight-box'>
<h3>📊 The Definitive Data Breach Dataset</h3>
<p>Explore <b>858 data breaches</b> from 2004-2025 with <b>6 novel enrichments</b> including 
prior breach history, executive turnover, regulatory enforcement, and dark web presence.</p>
</div>
""", unsafe_allow_html=True)

# ===============================
# KEY METRICS (Used .dropna() for consistent CAR mean calculation)
# ===============================
st.markdown("## 📈 Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

total_breaches = len(filtered_df)
mean_car_30d = filtered_df['car_30d'].dropna().mean()
repeat_offenders_count = filtered_df['is_repeat_offender'].sum()
repeat_offenders_delta = f"{filtered_df['is_repeat_offender'].mean()*100:.1f}%" if total_breaches > 0 else "0.0%"
total_penalties = filtered_df['total_regulatory_cost'].sum()

with col1:
    st.metric("Total Breaches", f"{total_breaches:,}")
with col2:
    st.metric("Unique Companies", f"{filtered_df['org_name'].nunique():,}")
with col3:
    st.metric("Mean 30-Day CAR", f"{mean_car_30d:.2f}%")
with col4:
    st.metric("Repeat Offenders", f"{repeat_offenders_count:,}", delta=repeat_offenders_delta)
with col5:
    st.metric("Total Penalties", f"${total_penalties/1e9:.2f}B")

st.markdown("---")

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Market Reactions", "🎯 Enrichments", "📈 Trends"])

# ---- TAB 1: OVERVIEW ----
with tab1:
    st.markdown("### Breach Timeline")
    timeline = filtered_df.groupby('breach_year').size().reset_index(name='count')
    fig = px.bar(timeline, x='breach_year', y='count', title='Data Breaches Over Time',
                 labels={'breach_year': 'Year', 'count': 'Number of Breaches'}, color='count', color_continuous_scale='Blues')
    fig.update_layout(height=400, showlegend=False, xaxis_title="Year", yaxis_title="Number of Breaches")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏢 Top Companies by Breach Frequency")
        top_companies = filtered_df['org_name'].value_counts().head(10).reset_index()
        top_companies.columns = ['Company', 'Breaches']
        fig = px.bar(top_companies, x='Breaches', y='Company', orientation='h', color='Breaches', color_continuous_scale='Reds')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### 📊 Disclosure Timing Distribution")
        disclosure_counts = pd.DataFrame({
            'Type': ['Immediate', 'Delayed'],
            'Count': [filtered_df['immediate_disclosure'].sum(), filtered_df['delayed_disclosure'].sum()]
        })
        fig = px.pie(disclosure_counts, values='Count', names='Type',
                     color='Type', color_discrete_map={'Immediate': 'lightgreen', 'Delayed': 'lightcoral'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# ---- TAB 2: MARKET REACTIONS ----
with tab2:
    st.markdown("### 💰 Cumulative Abnormal Returns (CARs)")
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=filtered_df['car_30d'].dropna(), nbinsx=50, name='30-Day CAR', marker_color='steelblue', opacity=0.7))
        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
        fig.add_vline(x=filtered_df['car_30d'].mean(), line_dash="dash", line_color="red", line_width=2,
                      annotation_text=f"Mean: {filtered_df['car_30d'].mean():.2f}%")
        fig.update_layout(title="Distribution of 30-Day CARs", xaxis_title="CAR (%)", yaxis_title="Frequency", height=400)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        immediate_car = filtered_df[filtered_df['immediate_disclosure']==1]['car_30d'].dropna()
        delayed_car = filtered_df[filtered_df['delayed_disclosure']==1]['car_30d'].dropna()
        fig = go.Figure()
        fig.add_trace(go.Box(y=immediate_car, name='Immediate', marker_color='lightgreen', boxmean='sd'))
        fig.add_trace(go.Box(y=delayed_car, name='Delayed', marker_color='lightcoral', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title="CARs by Disclosure Timing", yaxis_title="30-Day CAR (%)", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 Overall Statistics")
        st.write(filtered_df[['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d']].describe())
    with col2:
        st.markdown("### ✅ Immediate Disclosure")
        if len(immediate_car) > 0:
            st.metric("Mean CAR", f"{immediate_car.mean():.4f}%")
            st.metric("Median CAR", f"{immediate_car.median():.4f}%")
            st.metric("Std Dev", f"{immediate_car.std():.4f}%")
    with col3:
        st.markdown("### ⏰ Delayed Disclosure")
        if len(delayed_car) > 0:
            st.metric("Mean CAR", f"{delayed_car.mean():.4f}%")
            st.metric("Median CAR", f"{delayed_car.median():.4f}%")
            st.metric("Std Dev", f"{delayed_car.std():.4f}%")

# ---- TAB 3: ENRICHMENTS ----
with tab3:
    st.markdown("### 💎 Novel Data Enrichments")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🔄 Prior Breaches")
        st.metric("Repeat Offenders", f"{filtered_df['is_repeat_offender'].sum()}", delta=f"{filtered_df['is_repeat_offender'].mean()*100:.1f}%")
        st.metric("Avg Prior Breaches", f"{filtered_df['prior_breaches_total'].mean():.1f}")
    with col2:
        st.markdown("#### 👔 Executive Turnover")
        st.metric("Turnover Cases", f"{filtered_df['has_executive_change'].sum()}", delta=f"{filtered_df['has_executive_change'].mean()*100:.1f}%")
        st.metric("Median Days to Change", f"{filtered_df['days_to_first_change'].median():.0f}")
    with col3:
        st.markdown("#### ⚖️ Regulatory Actions")
        st.metric("Enforcement Cases", f"{filtered_df['has_any_regulatory_action'].sum()}", delta=f"{filtered_df['has_any_regulatory_action'].mean()*100:.1f}%")
        st.metric("Total Penalties", f"${filtered_df['total_regulatory_cost'].sum()/1e9:.2f}B")
    
    st.markdown("---")
    st.markdown("### 📈 Enrichment Impact on Market Reactions")
    enrichments = [
        ('is_repeat_offender', 'Repeat Offender'),
        ('high_severity_breach', 'High Severity'),
        ('has_executive_change', 'Exec Turnover'),
        ('has_any_regulatory_action', 'Regulatory Action'),
        ('in_hibp', 'Dark Web')
    ]
    impact_data = []
    for var, label in enrichments:
        with_feature = filtered_df[filtered_df[var]==1]['car_30d'].dropna().mean()
        without_feature = filtered_df[filtered_df[var]==0]['car_30d'].dropna().mean()
        impact_data.append({'Enrichment': label, 'With Feature': with_feature, 'Without Feature': without_feature, 'Difference': with_feature - without_feature})
    impact_df = pd.DataFrame(impact_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(name='With Feature', x=impact_df['Enrichment'], y=impact_df['With Feature'], marker_color='lightcoral'))
    fig.add_trace(go.Bar(name='Without Feature', x=impact_df['Enrichment'], y=impact_df['Without Feature'], marker_color='lightgreen'))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    fig.update_layout(title='Mean 30-Day CAR by Enrichment Feature', xaxis_title='Enrichment', yaxis_title='Mean CAR (%)', barmode='group', height=400)
    st.plotly_chart(fig, use_container_width=True)

# ---- TAB 4: TRENDS ----
with tab4:
    st.markdown("### 📈 Temporal Trends")
    yearly_trends = filtered_df.groupby('breach_year').agg({
        'car_30d': 'mean',
        'immediate_disclosure': 'mean',
        'is_repeat_offender': 'mean',
        'has_executive_change': 'mean',
        'total_regulatory_cost': 'sum'
    }).reset_index()
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Mean CAR Over Time', 'Immediate Disclosure Rate','Repeat Offender Rate','Annual Regulatory Penalties')
    )
    fig.add_trace(go.Scatter(x=yearly_trends['breach_year'], y=yearly_trends['car_30d'], mode='lines+markers', name='Mean CAR', line=dict(color='steelblue', width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=yearly_trends['breach_year'], y=yearly_trends['immediate_disclosure']*100, mode='lines+markers', name='Immediate %', line=dict(color='green', width=3)), row=1, col=2)
    fig.add_trace(go.Scatter(x=yearly_trends['breach_year'], y=yearly_trends['is_repeat_offender']*100, mode='lines+markers', name='Repeat %', line=dict(color='red', width=3)), row=2, col=1)
    fig.add_trace(go.Bar(x=yearly_trends['breach_year'], y=yearly_trends['total_regulatory_cost']/1e6, name='Penalties ($M)', marker_color='darkred'), row=2, col=2)
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_xaxes(title_text="Year", row=2, col=2)
    fig.update_yaxes(title_text="CAR (%)", row=1, col=1)
    fig.update_yaxes(title_text="Rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Rate (%)", row=2, col=1)
    fig.update_yaxes(title_text="Penalties ($M)", row=2, col=2)
    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><b>Data Breach Analytics Dashboard</b> | Dissertation Research 2025</p>
    <p>858 breaches • 6 enrichments • 98 variables</p>
</div>
""", unsafe_allow_html=True)