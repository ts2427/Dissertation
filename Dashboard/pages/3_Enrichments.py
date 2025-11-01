# 3_Enrichments.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats

st.set_page_config(page_title="Enrichment Analysis", page_icon="💎", layout="wide")
st.title("💎 Enrichment Variables: Deep Dive")
st.markdown("This page provides a comprehensive analysis of the **6 novel enrichments** that make this dataset unique.")

# -------------------------
# Helpers & Data loading
# -------------------------
def safe_sum(df, col):
    return int(df[col].sum()) if col in df.columns else 0

def safe_mean(df, col):
    return float(df[col].mean()) if col in df.columns else 0.0

@st.cache_data
def load_data():
    df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx')
    # parse dates
    df['breach_date'] = pd.to_datetime(df['breach_date'], errors='coerce')
    df['breach_year'] = df['breach_date'].dt.year

    # normalize booleans (fill NaN and cast)
    bool_cols = [
        'is_repeat_offender', 'is_first_breach', 'has_executive_change',
        'has_any_regulatory_action', 'in_hibp', 'has_cyber_insurance_disclosure',
        'pii_breach', 'health_breach', 'financial_breach',
        'ransomware', 'nation_state', 'insider_threat', 'complex_breach',
        'has_ftc_action', 'has_fcc_action', 'has_state_ag_action'
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # Ensure numeric CAR column exists (and convert to percentage if it is in decimal form)
    if 'car_30d' in df.columns:
        # If mean less than 1, assume decimal and convert to percent
        if df['car_30d'].dropna().empty:
            pass
        elif abs(df['car_30d'].dropna().mean()) < 1:
            df['car_30d'] = df['car_30d'] * 100

    return df

df = load_data()

# Sidebar selector
st.sidebar.markdown("### Select Enrichment")
enrichment_choice = st.sidebar.radio(
    "Choose enrichment to explore:",
    ["Overview", "Prior Breach History", "Breach Severity", "Executive Turnover",
     "Regulatory Enforcement", "Dark Web Presence", "Cyber Insurance"]
)

# =======================
# OVERVIEW
# =======================
if enrichment_choice == "Overview":
    st.markdown("## 📊 Enrichment Overview")

    st.markdown(
        """
        <div style='background-color: #e8f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;'>
        <h3>Six Novel Enrichments</h3>
        <p>This dissertation introduces <b>six unique data enrichments</b> that provide unprecedented insights 
        into data breach consequences and governance:</p>
        </div>
        """, unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔄 Repeat Offenders",
                  f"{safe_sum(df, 'is_repeat_offender')} ({safe_mean(df, 'is_repeat_offender')*100:.1f}%)")
        st.metric("⚠️ High Severity Breaches",
                  f"{safe_sum(df, 'high_severity_breach')} ({safe_mean(df, 'high_severity_breach')*100:.1f}%)")
    with col2:
        st.metric("👔 Executive Turnover",
                  f"{safe_sum(df, 'has_executive_change')} ({safe_mean(df, 'has_executive_change')*100:.1f}%)")
        st.metric("⚖️ Regulatory Actions",
                  f"{safe_sum(df, 'has_any_regulatory_action')} ({safe_mean(df, 'has_any_regulatory_action')*100:.1f}%)")
    with col3:
        st.metric("🕸️ Dark Web Breaches",
                  f"{safe_sum(df, 'in_hibp')} ({safe_mean(df, 'in_hibp')*100:.1f}%)")
        st.metric("🛡️ Cyber Insurance",
                  f"{safe_sum(df, 'has_cyber_insurance_disclosure')} ({safe_mean(df, 'has_cyber_insurance_disclosure')*100:.1f}%)")

    st.markdown("---")
    st.markdown("### Enrichment Coverage")

    coverage_data = pd.DataFrame({
        'Enrichment': ['Prior Breaches', 'Severity', 'Exec Turnover', 'Regulatory', 'Dark Web', 'Insurance'],
        'Coverage (%)': [
            safe_mean(df, 'is_repeat_offender')*100,
            100.0,
            safe_mean(df, 'has_executive_change')*100,
            safe_mean(df, 'has_any_regulatory_action')*100,
            safe_mean(df, 'in_hibp')*100,
            safe_mean(df, 'has_cyber_insurance_disclosure')*100
        ],
        'Count': [
            safe_sum(df, 'is_repeat_offender'),
            len(df),
            safe_sum(df, 'has_executive_change'),
            safe_sum(df, 'has_any_regulatory_action'),
            safe_sum(df, 'in_hibp'),
            safe_sum(df, 'has_cyber_insurance_disclosure')
        ]
    })

    fig = px.bar(coverage_data, x='Enrichment', y='Coverage (%)', text='Count',
                 color='Coverage (%)', color_continuous_scale='Blues', title='Enrichment Coverage Across Dataset')
    fig.update_traces(texttemplate='%{text} breaches', textposition='outside')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Impact on Market Reactions")

    impact_data = []
    enrichments = [
        ('is_repeat_offender', 'Repeat Offender'),
        ('high_severity_breach', 'High Severity'),
        ('has_executive_change', 'Exec Turnover'),
        ('has_any_regulatory_action', 'Regulatory Action'),
        ('in_hibp', 'Dark Web')
    ]

    for var, label in enrichments:
        if var in df.columns:
            with_feature = df[df[var] == 1]['car_30d'].dropna().mean()
            without_feature = df[df[var] == 0]['car_30d'].dropna().mean()
        else:
            with_feature = np.nan
            without_feature = np.nan
        difference = with_feature - without_feature
        impact_data.append({'Enrichment': label, 'With Feature': with_feature, 'Without Feature': without_feature, 'Difference': difference})

    impact_df = pd.DataFrame(impact_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(name='With Feature', x=impact_df['Enrichment'], y=impact_df['With Feature'], marker_color='lightcoral'))
    fig.add_trace(go.Bar(name='Without Feature', x=impact_df['Enrichment'], y=impact_df['Without Feature'], marker_color='lightgreen'))
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    fig.update_layout(title='Mean 30-Day CAR by Enrichment Feature', xaxis_title='Enrichment', yaxis_title='Mean CAR (%)', barmode='group', height=400)
    st.plotly_chart(fig, use_container_width=True)

# =======================
# PRIOR BREACH HISTORY
# =======================
elif enrichment_choice == "Prior Breach History":
    st.markdown("## 🔄 Prior Breach History Analysis")
    st.info("📊 67% of breaches are repeat offenders with prior breach history")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Repeat Offenders", f"{safe_sum(df, 'is_repeat_offender')}", help=f"{safe_mean(df, 'is_repeat_offender')*100:.1f}%")
    with col2:
        st.metric("First-Time Breaches", f"{safe_sum(df, 'is_first_breach')}", help=f"{safe_mean(df, 'is_first_breach')*100:.1f}%")
    with col3:
        if 'prior_breaches_total' in df.columns:
            st.metric("Mean Prior Breaches", f"{df['prior_breaches_total'].mean():.1f}")
        else:
            st.metric("Mean Prior Breaches", "N/A")
    with col4:
        if 'prior_breaches_total' in df.columns:
            st.metric("Max Prior Breaches", f"{df['prior_breaches_total'].max():.0f}")
        else:
            st.metric("Max Prior Breaches", "N/A")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if 'prior_breaches_total' in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df['prior_breaches_total'], nbinsx=50, marker_color='steelblue', opacity=0.7))
            fig.add_vline(x=df['prior_breaches_total'].mean(), line_dash="dash", line_color="red", annotation_text=f"Mean: {df['prior_breaches_total'].mean():.1f}")
            fig.update_layout(title='Distribution of Prior Breaches', xaxis_title='Number of Prior Breaches', yaxis_title='Frequency', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No prior_breaches_total column available.")

    with col2:
        pie_data = pd.DataFrame({
            'Type': ['First-Time', 'Repeat Offender'],
            'Count': [safe_sum(df, 'is_first_breach'), safe_sum(df, 'is_repeat_offender')]
        })
        fig = px.pie(pie_data, values='Count', names='Type', color='Type',
                     color_discrete_map={'First-Time': 'lightgreen', 'Repeat Offender': 'lightcoral'})
        fig.update_layout(title='Breach Classification', height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Market Reaction: First-Time vs Repeat Offenders")
    first_time_car = df[df.get('is_first_breach', 0) == 1]['car_30d'].dropna()
    repeat_car = df[df.get('is_repeat_offender', 0) == 1]['car_30d'].dropna()

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=first_time_car, name='First-Time', marker_color='lightgreen', boxmean='sd'))
        fig.add_trace(go.Box(y=repeat_car, name='Repeat Offender', marker_color='lightcoral', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title='CARs by Prior Breach Status', yaxis_title='30-Day CAR (%)', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Statistics")
        if not first_time_car.empty:
            st.metric("First-Time Mean CAR", f"{first_time_car.mean():.4f}%")
        else:
            st.metric("First-Time Mean CAR", "N/A")
        if not repeat_car.empty:
            st.metric("Repeat Offender Mean CAR", f"{repeat_car.mean():.4f}%")
        else:
            st.metric("Repeat Offender Mean CAR", "N/A")

        if (not first_time_car.empty) and (not repeat_car.empty):
            t_stat, p_val = stats.ttest_ind(first_time_car, repeat_car, equal_var=False, nan_policy='omit')
            st.write(f"**t-statistic:** {t_stat:.4f}")
            st.write(f"**p-value:** {p_val:.4f}")
        else:
            st.write("Insufficient data for t-test.")

    st.markdown("---")
    st.markdown("### Top 10 Repeat Offenders")
    if 'org_name' in df.columns and 'prior_breaches_total' in df.columns:
        top_repeaters = df.groupby('org_name')['prior_breaches_total'].max().nlargest(10).reset_index()
        top_repeaters.columns = ['Company', 'Total Prior Breaches']
        fig = px.bar(top_repeaters, x='Total Prior Breaches', y='Company', orientation='h', color='Total Prior Breaches', color_continuous_scale='Reds')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient columns for top repeaters chart.")

# =======================
# BREACH SEVERITY
# =======================
elif enrichment_choice == "Breach Severity":
    st.markdown("## ⚠️ Breach Severity Classification")
    st.info("📊 100% of breaches classified across 10 severity dimensions (where data exists)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PII Breaches", f"{safe_sum(df, 'pii_breach')} ({safe_mean(df, 'pii_breach')*100:.1f}%)")
        st.metric("Health Breaches", f"{safe_sum(df, 'health_breach')} ({safe_mean(df, 'health_breach')*100:.1f}%)")
        st.metric("Financial Breaches", f"{safe_sum(df, 'financial_breach')} ({safe_mean(df, 'financial_breach')*100:.1f}%)")
    with col2:
        st.metric("Ransomware", f"{safe_sum(df, 'ransomware')} ({safe_mean(df, 'ransomware')*100:.1f}%)")
        st.metric("Nation-State", f"{safe_sum(df, 'nation_state')} ({safe_mean(df, 'nation_state')*100:.1f}%)")
        st.metric("Insider Threat", f"{safe_sum(df, 'insider_threat')} ({safe_mean(df, 'insider_threat')*100:.1f}%)")
    with col3:
        st.metric("High Severity", f"{safe_sum(df, 'high_severity_breach')} ({safe_mean(df, 'high_severity_breach')*100:.1f}%)")
        if 'combined_severity_score' in df.columns:
            st.metric("Mean Severity Score", f"{df['combined_severity_score'].mean():.2f}")
            st.metric("Complex Breaches (>1 type)", f"{safe_sum(df, 'complex_breach')} ({safe_mean(df, 'complex_breach')*100:.1f}%)")
        else:
            st.metric("Mean Severity Score", "N/A")
            st.metric("Complex Breaches (>1 type)", f"{safe_sum(df, 'complex_breach')} ({safe_mean(df, 'complex_breach')*100:.1f}%)")

    st.markdown("---")
    st.markdown("### Breach Type Distribution")
    types = ['pii_breach','health_breach','financial_breach','ip_breach','ransomware','nation_state','insider_threat','ddos_attack','phishing','malware']
    counts = [safe_sum(df, t) for t in types]
    labels = ['PII','Health','Financial','IP','Ransomware','Nation-State','Insider','DDoS','Phishing','Malware']
    breach_types = pd.DataFrame({'Type': labels, 'Count': counts}).sort_values('Count', ascending=False)
    fig = px.bar(breach_types, x='Type', y='Count', color='Count', color_continuous_scale='Reds', title='Breach Types Across Dataset')
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if 'combined_severity_score' in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df['combined_severity_score'].dropna(), nbinsx=30, marker_color='darkred', opacity=0.7))
            fig.add_vline(x=df['combined_severity_score'].mean(), line_dash="dash", line_color="black", annotation_text=f"Mean: {df['combined_severity_score'].mean():.2f}")
            fig.update_layout(title='Distribution of Severity Scores', xaxis_title='Combined Severity Score', yaxis_title='Frequency', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 'combined_severity_score' column available.")

    with col2:
        low_sev = df[df.get('high_severity_breach', 0) == 0]['car_30d'].dropna()
        high_sev = df[df.get('high_severity_breach', 0) == 1]['car_30d'].dropna()
        fig = go.Figure()
        fig.add_trace(go.Box(y=low_sev, name='Low Severity', marker_color='lightgreen', boxmean='sd'))
        fig.add_trace(go.Box(y=high_sev, name='High Severity', marker_color='darkred', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title='CARs by Breach Severity', yaxis_title='30-Day CAR (%)', height=400)
        st.plotly_chart(fig, use_container_width=True)

# =======================
# EXECUTIVE TURNOVER
# =======================
elif enrichment_choice == "Executive Turnover":
    st.markdown("## 👔 Executive Turnover Analysis")
    st.info("📊 49% of breaches experience executive changes within 1 year")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("With Turnover", f"{safe_sum(df, 'has_executive_change')}", help=f"{safe_mean(df, 'has_executive_change')*100:.1f}%")
    with col2:
        # safe negation
        no_turn_count = len(df) - safe_sum(df, 'has_executive_change')
        st.metric("No Turnover", f"{no_turn_count}")
    with col3:
        if 'days_to_first_change' in df.columns:
            st.metric("Mean Days to Change", f"{df['days_to_first_change'].mean():.0f}")
        else:
            st.metric("Mean Days to Change", "N/A")
    with col4:
        if 'days_to_first_change' in df.columns:
            st.metric("Median Days to Change", f"{df['days_to_first_change'].median():.0f}")
        else:
            st.metric("Median Days to Change", "N/A")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if 'days_to_first_change' in df.columns:
            turnover_data = df[df['has_executive_change'] == 1]['days_to_first_change'].dropna()
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=turnover_data, nbinsx=30, marker_color='orange', opacity=0.7))
            if not turnover_data.empty:
                fig.add_vline(x=turnover_data.median(), line_dash="dash", line_color="red", annotation_text=f"Median: {turnover_data.median():.0f} days")
            fig.update_layout(title='Days Until Executive Change', xaxis_title='Days', yaxis_title='Frequency', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 'days_to_first_change' column available.")

    with col2:
        pie_data = pd.DataFrame({
            'Status': ['Executive Turnover', 'No Turnover'],
            'Count': [safe_sum(df, 'has_executive_change'), no_turn_count]
        })
        fig = px.pie(pie_data, values='Count', names='Status', color='Status',
                     color_discrete_map={'Executive Turnover': 'orange', 'No Turnover': 'lightgray'})
        fig.update_layout(title='Executive Turnover Distribution', height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Market Reaction by Executive Turnover")
    no_turnover = df[df.get('has_executive_change', 0) == 0]['car_30d'].dropna()
    has_turnover = df[df.get('has_executive_change', 0) == 1]['car_30d'].dropna()

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=no_turnover, name='No Turnover', marker_color='lightgray', boxmean='sd'))
        fig.add_trace(go.Box(y=has_turnover, name='Executive Turnover', marker_color='orange', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title='CARs by Executive Turnover Status', yaxis_title='30-Day CAR (%)', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Statistics")
        if not no_turnover.empty:
            st.metric("No Turnover Mean CAR", f"{no_turnover.mean():.4f}%")
        else:
            st.metric("No Turnover Mean CAR", "N/A")
        if not has_turnover.empty:
            st.metric("With Turnover Mean CAR", f"{has_turnover.mean():.4f}%")
            if (len(has_turnover) > 1) and (len(no_turnover) > 1):
                t_stat, p_val = stats.ttest_ind(no_turnover, has_turnover, equal_var=False, nan_policy='omit')
                st.write(f"**t-statistic:** {t_stat:.4f}")
                st.write(f"**p-value:** {p_val:.4f}")
        else:
            st.metric("With Turnover Mean CAR", "N/A")

# =======================
# REGULATORY ENFORCEMENT
# =======================
elif enrichment_choice == "Regulatory Enforcement":
    st.markdown("## ⚖️ Regulatory Enforcement Analysis")
    st.info("📊 7.6% of breaches resulted in regulatory enforcement actions totaling $6.9B")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Actions", f"{safe_sum(df, 'has_any_regulatory_action')}", help=f"{safe_mean(df, 'has_any_regulatory_action')*100:.1f}%")
    with col2:
        st.metric("FTC Actions", f"{safe_sum(df, 'has_ftc_action')}")
    with col3:
        st.metric("FCC Actions", f"{safe_sum(df, 'has_fcc_action')}")
    with col4:
        st.metric("State AG Actions", f"{safe_sum(df, 'has_state_ag_action')}")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_pen = df['total_regulatory_cost'].sum() if 'total_regulatory_cost' in df.columns else 0.0
        st.metric("Total Penalties", f"${total_pen/1e9:.2f}B")
    with col2:
        penalty_breaches = df[df.get('total_regulatory_cost', 0) > 0]
        st.metric("Mean Penalty (if penalized)", f"${penalty_breaches['total_regulatory_cost'].mean()/1e6:.1f}M" if not penalty_breaches.empty else "N/A")
    with col3:
        st.metric("Median Penalty (if penalized)", f"${penalty_breaches['total_regulatory_cost'].median()/1e6:.1f}M" if not penalty_breaches.empty else "N/A")

    st.markdown("---")
    st.markdown("### Top 10 Largest Penalties")
    if 'total_regulatory_cost' in df.columns:
        top_penalties = df.nlargest(10, 'total_regulatory_cost')[['org_name', 'breach_date', 'total_regulatory_cost']].copy()
        top_penalties['total_regulatory_cost_millions'] = top_penalties['total_regulatory_cost'] / 1e6
        fig = px.bar(top_penalties, x='total_regulatory_cost_millions', y='org_name', orientation='h', color='total_regulatory_cost_millions', color_continuous_scale='Reds', title='Largest Regulatory Penalties ($M)')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No 'total_regulatory_cost' column available.")

    st.markdown("---")
    st.markdown("### Market Reaction by Regulatory Action")
    no_reg = df[df.get('has_any_regulatory_action', 0) == 0]['car_30d'].dropna()
    has_reg = df[df.get('has_any_regulatory_action', 0) == 1]['car_30d'].dropna()

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=no_reg, name='No Regulatory Action', marker_color='lightgreen', boxmean='sd'))
        fig.add_trace(go.Box(y=has_reg, name='Regulatory Action', marker_color='darkred', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title='CARs by Regulatory Action Status', yaxis_title='30-Day CAR (%)', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Statistics")
        if not no_reg.empty:
            st.metric("No Action Mean CAR", f"{no_reg.mean():.4f}%")
        else:
            st.metric("No Action Mean CAR", "N/A")
        if not has_reg.empty:
            st.metric("With Action Mean CAR", f"{has_reg.mean():.4f}%")
            if (len(has_reg) > 1) and (len(no_reg) > 1):
                t_stat, p_val = stats.ttest_ind(no_reg, has_reg, equal_var=False, nan_policy='omit')
                st.write(f"**t-statistic:** {t_stat:.4f}")
                st.write(f"**p-value:** {p_val:.4f}")
        else:
            st.metric("With Action Mean CAR", "N/A")

    st.markdown("---")
    st.markdown("### Regulatory Agency Breakdown")
    agency_data = pd.DataFrame({
        'Agency': ['FTC', 'FCC', 'State AG'],
        'Actions': [safe_sum(df, 'has_ftc_action'), safe_sum(df, 'has_fcc_action'), safe_sum(df, 'has_state_ag_action')],
        'Total Penalties ($M)': [
            df['ftc_settlement_amount'].sum()/1e6 if 'ftc_settlement_amount' in df.columns else 0.0,
            df['fcc_fine_amount'].sum()/1e6 if 'fcc_fine_amount' in df.columns else 0.0,
            df['ag_settlement_amount'].sum()/1e6 if 'ag_settlement_amount' in df.columns else 0.0
        ]
    })
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(agency_data, x='Agency', y='Actions', color='Actions', color_continuous_scale='Blues', title='Number of Actions by Agency')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(agency_data, x='Agency', y='Total Penalties ($M)', color='Total Penalties ($M)', color_continuous_scale='Reds', title='Total Penalties by Agency ($M)')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# =======================
# DARK WEB PRESENCE
# =======================
elif enrichment_choice == "Dark Web Presence":
    st.markdown("## 🕸️ Dark Web Presence Analysis")
    st.info("📊 2.9% of breaches found in Have I Been Pwned database with 2.3B credentials exposed")

    hibp_breaches = df[df.get('in_hibp', 0) == 1]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Breaches in HIBP", f"{safe_sum(df, 'in_hibp')}", help=f"{safe_mean(df, 'in_hibp')*100:.1f}%")
    with col2:
        if not hibp_breaches.empty and 'hibp_pwn_count' in hibp_breaches.columns:
            st.metric("Total Credentials", f"{hibp_breaches['hibp_pwn_count'].sum()/1e9:.2f}B")
        else:
            st.metric("Total Credentials", "0.00B")
    with col3:
        if not hibp_breaches.empty and 'hibp_pwn_count' in hibp_breaches.columns:
            st.metric("Mean per Breach", f"{hibp_breaches['hibp_pwn_count'].mean()/1e6:.1f}M")
        else:
            st.metric("Mean per Breach", "N/A")
    with col4:
        if not hibp_breaches.empty and 'hibp_pwn_count' in hibp_breaches.columns:
            st.metric("Median per Breach", f"{hibp_breaches['hibp_pwn_count'].median()/1e6:.1f}M")
        else:
            st.metric("Median per Breach", "N/A")

    st.markdown("---")
    if not hibp_breaches.empty and 'hibp_pwn_count' in hibp_breaches.columns:
        st.markdown("### Top 10 Breaches by Credentials Exposed")
        top_hibp = hibp_breaches.nlargest(10, 'hibp_pwn_count')[['org_name', 'hibp_pwn_count', 'hibp_breach_date']].copy()
        top_hibp['credentials_millions'] = top_hibp['hibp_pwn_count'] / 1e6

        # properly-indented plot block
        fig = px.bar(
            top_hibp,
            x='credentials_millions',
            y='org_name',
            orientation='h',
            color='credentials_millions',
            color_continuous_scale='Reds',
            title='Largest Dark Web Breaches (Millions of Credentials)'
        )
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

    st.markdown("### Market Reaction by Dark Web Presence")
    not_hibp = df[df.get('in_hibp', 0) == 0]['car_30d'].dropna()
    in_hibp_car = df[df.get('in_hibp', 0) == 1]['car_30d'].dropna()

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=not_hibp, name='Not in HIBP', marker_color='lightgreen', boxmean='sd'))
        if not in_hibp_car.empty:
            fig.add_trace(go.Box(y=in_hibp_car, name='In HIBP', marker_color='darkred', boxmean='sd'))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(title='CARs by Dark Web Presence', yaxis_title='30-Day CAR (%)', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Statistics")
        if not not_hibp.empty:
            st.metric("Not in HIBP Mean CAR", f"{not_hibp.mean():.4f}%")
        else:
            st.metric("Not in HIBP Mean CAR", "N/A")
        if not in_hibp_car.empty:
            st.metric("In HIBP Mean CAR", f"{in_hibp_car.mean():.4f}%")
            st.metric("Difference", f"{not_hibp.mean() - in_hibp_car.mean():.4f}%")
            if (len(not_hibp) > 1) and (len(in_hibp_car) > 1):
                t_stat, p_val = stats.ttest_ind(not_hibp, in_hibp_car, equal_var=False, nan_policy='omit')
                st.write(f"**t-statistic:** {t_stat:.4f}")
                st.write(f"**p-value:** {p_val:.4f}")
        else:
            st.write("Insufficient data for statistical comparison")

    if not hibp_breaches.empty and 'hibp_pwn_count' in hibp_breaches.columns:
        st.markdown("---")
        st.markdown("### Dark Web Breach Details")
        hibp_details = hibp_breaches[['org_name', 'breach_date', 'hibp_breach_name', 'hibp_pwn_count', 'hibp_data_classes']].copy()
        hibp_details['credentials_millions'] = hibp_details['hibp_pwn_count'] / 1e6
        hibp_details = hibp_details.sort_values('hibp_pwn_count', ascending=False)
        st.dataframe(
            hibp_details[['org_name', 'breach_date', 'hibp_breach_name', 'credentials_millions', 'hibp_data_classes']].rename(columns={
                'org_name': 'Company', 'breach_date': 'Breach Date', 'hibp_breach_name': 'HIBP Name',
                'credentials_millions': 'Credentials (M)', 'hibp_data_classes': 'Data Types'
            }),
            use_container_width=True,
            height=400
        )

# =======================
# CYBER INSURANCE
# =======================
elif enrichment_choice == "Cyber Insurance":
    st.markdown("## 🛡️ Cyber Insurance Disclosure Analysis")
    st.warning("📊 0.8% of breaches have cyber insurance disclosures in SEC filings (sparse data)")

    insurance_breaches = df[df.get('has_cyber_insurance_disclosure', 0) == 1]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("With Insurance Disclosure", f"{safe_sum(df, 'has_cyber_insurance_disclosure')}", help=f"{safe_mean(df, 'has_cyber_insurance_disclosure')*100:.1f}%")
    with col2:
        no_ins_count = len(df) - safe_sum(df, 'has_cyber_insurance_disclosure')
        st.metric("Without Disclosure", f"{no_ins_count}")
    with col3:
        st.metric("Total 10-Ks Checked", f"{int(df['num_10k_filings_checked'].sum())}" if 'num_10k_filings_checked' in df.columns else "N/A")
    with col4:
        st.metric("Mean per Breach", f"{df['num_10k_filings_checked'].mean():.1f}" if 'num_10k_filings_checked' in df.columns else "N/A")

    st.markdown("---")
    if not insurance_breaches.empty:
        st.markdown("### Companies with Cyber Insurance Disclosures")
        for company in insurance_breaches['org_name'].unique():
            st.write(f"• {company}")

        st.markdown("---")
        st.markdown("### Market Reaction by Insurance Status")

        no_insurance = df[df.get('has_cyber_insurance_disclosure', 0) == 0]['car_30d'].dropna()
        has_insurance = df[df.get('has_cyber_insurance_disclosure', 0) == 1]['car_30d'].dropna()

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Box(y=no_insurance, name='No Insurance Disclosure', marker_color='lightgray', boxmean='sd'))
            if not has_insurance.empty:
                fig.add_trace(go.Box(y=has_insurance, name='Insurance Disclosed', marker_color='lightblue', boxmean='sd'))
            fig.add_hline(y=0, line_dash="dash", line_color="black")
            fig.update_layout(title='CARs by Insurance Disclosure Status', yaxis_title='30-Day CAR (%)', height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Statistics")
            if not no_insurance.empty:
                st.metric("No Insurance Mean CAR", f"{no_insurance.mean():.4f}%")
            else:
                st.metric("No Insurance Mean CAR", "N/A")
            if not has_insurance.empty:
                st.metric("With Insurance Mean CAR", f"{has_insurance.mean():.4f}%")
                st.metric("Difference", f"{no_insurance.mean() - has_insurance.mean():.4f}%")
                if (len(no_insurance) > 1) and (len(has_insurance) > 1):
                    t_stat, p_val = stats.ttest_ind(no_insurance, has_insurance, equal_var=False, nan_policy='omit')
                    st.write(f"**t-statistic:** {t_stat:.4f}")
                    st.write(f"**p-value:** {p_val:.4f}")
            else:
                st.write("Insufficient data for statistical comparison.")
    else:
        st.info("No companies with cyber insurance disclosures found in the dataset.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><b>Enrichment Analysis</b> | Six Novel Data Dimensions</p>
    <p>Providing unprecedented insights into breach consequences and governance</p>
</div>
""", unsafe_allow_html=True)
