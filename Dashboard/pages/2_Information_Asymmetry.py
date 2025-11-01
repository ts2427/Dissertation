import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats

st.set_page_config(page_title="Information Asymmetry", page_icon="📉", layout="wide")

st.title("📉 Information Asymmetry Analysis")

st.markdown("""
This page presents the **Essay 3 information asymmetry analysis**, examining how disclosure timing 
affects information uncertainty and the moderating role of governance.
""")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx')
    df['breach_date'] = pd.to_datetime(df['breach_date'])
    df['breach_year'] = df['breach_date'].dt.year
    return df

df = load_data()

# Filter to volatility sample
volatility_df = df[df['return_volatility_pre'].notna() & 
                   df['return_volatility_post'].notna()].copy()

st.info(f"📊 Information asymmetry sample: **{len(volatility_df)}** breaches with volatility data")

# ============================================================================
# VOLATILITY BASELINE
# ============================================================================

st.markdown("## 1. Volatility Changes Around Breaches")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Mean Pre-Breach Volatility", 
             f"{volatility_df['return_volatility_pre'].mean():.6f}")

with col2:
    st.metric("Mean Post-Breach Volatility", 
             f"{volatility_df['return_volatility_post'].mean():.6f}")

with col3:
    st.metric("Mean Volatility Change", 
             f"{volatility_df['volatility_change'].mean():.6f}")

with col4:
    # Paired t-test
    t_stat, p_val = stats.ttest_rel(volatility_df['return_volatility_post'], 
                                     volatility_df['return_volatility_pre'])
    st.metric("t-statistic", 
             f"{t_stat:.4f}",
             delta=f"p={p_val:.4f}")

st.markdown("---")

# Visualizations
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Before vs After Scatter")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=volatility_df['return_volatility_pre'],
        y=volatility_df['return_volatility_post'],
        mode='markers',
        marker=dict(color='steelblue', size=8, opacity=0.5),
        name='Breaches'
    ))
    
    # 45-degree line
    max_val = max(volatility_df['return_volatility_pre'].max(), 
                  volatility_df['return_volatility_post'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        name='45° line'
    ))
    
    fig.update_layout(
        xaxis_title="Pre-Breach Volatility",
        yaxis_title="Post-Breach Volatility",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Distribution of Changes")
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=volatility_df['volatility_change'],
        nbinsx=50,
        marker_color='steelblue',
        opacity=0.7
    ))
    
    fig.add_vline(x=0, line_dash="dash", line_color="red", line_width=2)
    fig.add_vline(x=volatility_df['volatility_change'].mean(), 
                  line_dash="dash", line_color="green", line_width=2,
                  annotation_text=f"Mean: {volatility_df['volatility_change'].mean():.4f}")
    
    fig.update_layout(
        xaxis_title="Volatility Change",
        yaxis_title="Frequency",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.markdown("### Box Plot Comparison")
    
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=volatility_df['return_volatility_pre'],
        name='Pre-Breach',
        marker_color='lightgreen',
        boxmean='sd'
    ))
    
    fig.add_trace(go.Box(
        y=volatility_df['return_volatility_post'],
        name='Post-Breach',
        marker_color='lightcoral',
        boxmean='sd'
    ))
    
    fig.update_layout(
        yaxis_title="Volatility",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# DISCLOSURE TIMING EFFECTS
# ============================================================================

st.markdown("---")
st.markdown("## 2. Disclosure Timing Effects on Uncertainty")

immediate_vol = volatility_df[volatility_df['immediate_disclosure']==1]['volatility_change'].dropna()
delayed_vol = volatility_df[volatility_df['delayed_disclosure']==1]['volatility_change'].dropna()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Immediate Disclosure", 
             f"{len(immediate_vol)} breaches",
             delta=f"Mean: {immediate_vol.mean():.6f}")

with col2:
    st.metric("Delayed Disclosure", 
             f"{len(delayed_vol)} breaches",
             delta=f"Mean: {delayed_vol.mean():.6f}")

with col3:
    t_stat, p_val = stats.ttest_ind(immediate_vol, delayed_vol)
    st.metric("Difference", 
             f"{immediate_vol.mean() - delayed_vol.mean():.6f}",
             delta=f"p-value: {p_val:.4f}")

# Visualization
col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=immediate_vol,
        name='Immediate',
        marker_color='lightgreen',
        boxmean='sd'
    ))
    
    fig.add_trace(go.Box(
        y=delayed_vol,
        name='Delayed',
        marker_color='lightcoral',
        boxmean='sd'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    
    fig.update_layout(
        title="Volatility Change by Disclosure Timing",
        yaxis_title="Volatility Change",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=immediate_vol,
        nbinsx=30,
        name='Immediate',
        marker_color='green',
        opacity=0.5
    ))
    
    fig.add_trace(go.Histogram(
        x=delayed_vol,
        nbinsx=30,
        name='Delayed',
        marker_color='red',
        opacity=0.5
    ))
    
    fig.add_vline(x=0, line_dash="solid", line_color="black", line_width=1)
    fig.add_vline(x=immediate_vol.mean(), line_dash="dash", line_color="green", line_width=2)
    fig.add_vline(x=delayed_vol.mean(), line_dash="dash", line_color="red", line_width=2)
    
    fig.update_layout(
        title="Distribution Comparison",
        xaxis_title="Volatility Change",
        yaxis_title="Frequency",
        barmode='overlay',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# GOVERNANCE MODERATORS
# ============================================================================

st.markdown("---")
st.markdown("## 3. Governance Moderating Effects")

st.markdown("""
Examining how governance mechanisms moderate the relationship between disclosure timing and information asymmetry.
""")

# Create tabs for each governance mechanism
tabs = st.tabs(["Prior Breaches (Reputation)", "Executive Turnover (Accountability)", 
                "Regulatory Action (Enforcement)", "Combined View"])

with tabs[0]:
    st.markdown("### Prior Breach History as Governance Proxy")
    
    st.markdown("""
    **Hypothesis:** Firms with prior breaches (poor reputation) experience larger volatility increases, 
    especially with delayed disclosure.
    """)
    
    # Split by prior breaches and disclosure timing
    first_immediate = volatility_df[(volatility_df['is_first_breach']==1) & 
                                    (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    first_delayed = volatility_df[(volatility_df['is_first_breach']==1) & 
                                  (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    repeat_immediate = volatility_df[(volatility_df['is_repeat_offender']==1) & 
                                     (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    repeat_delayed = volatility_df[(volatility_df['is_repeat_offender']==1) & 
                                   (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create 2x2 matrix
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=first_immediate, name='First-Time, Immediate', 
                            marker_color='lightgreen'))
        fig.add_trace(go.Box(y=first_delayed, name='First-Time, Delayed', 
                            marker_color='yellow'))
        fig.add_trace(go.Box(y=repeat_immediate, name='Repeat, Immediate', 
                            marker_color='orange'))
        fig.add_trace(go.Box(y=repeat_delayed, name='Repeat, Delayed', 
                            marker_color='darkred'))
        
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(
            title="Volatility Change: Prior Breaches × Disclosure Timing",
            yaxis_title="Volatility Change",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        
        st.markdown("**First-Time Breaches:**")
        st.write(f"• Immediate: {first_immediate.mean():.6f} (n={len(first_immediate)})")
        st.write(f"• Delayed: {first_delayed.mean():.6f} (n={len(first_delayed)})")
        
        st.markdown("**Repeat Offenders:**")
        st.write(f"• Immediate: {repeat_immediate.mean():.6f} (n={len(repeat_immediate)})")
        st.write(f"• Delayed: {repeat_delayed.mean():.6f} (n={len(repeat_delayed)})")
        
        st.markdown("**Interaction Effect:**")
        if len(repeat_delayed) > 0 and len(first_immediate) > 0:
            interaction = (repeat_delayed.mean() - repeat_immediate.mean()) - \
                         (first_delayed.mean() - first_immediate.mean())
            st.write(f"• {interaction:.6f}")

with tabs[1]:
    st.markdown("### Executive Turnover as Accountability Signal")
    
    st.markdown("""
    **Hypothesis:** Firms with executive turnover (strong accountability) show reduced volatility increases, 
    suggesting the market perceives better governance.
    """)
    
    # Split by executive turnover and disclosure timing
    no_exec_imm = volatility_df[(volatility_df['has_executive_change']==0) & 
                                (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    no_exec_del = volatility_df[(volatility_df['has_executive_change']==0) & 
                                (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    exec_imm = volatility_df[(volatility_df['has_executive_change']==1) & 
                             (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    exec_del = volatility_df[(volatility_df['has_executive_change']==1) & 
                             (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=no_exec_imm, name='No Turnover, Immediate', 
                            marker_color='lightblue'))
        fig.add_trace(go.Box(y=no_exec_del, name='No Turnover, Delayed', 
                            marker_color='gray'))
        fig.add_trace(go.Box(y=exec_imm, name='Turnover, Immediate', 
                            marker_color='lightgreen'))
        fig.add_trace(go.Box(y=exec_del, name='Turnover, Delayed', 
                            marker_color='orange'))
        
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(
            title="Volatility Change: Executive Turnover × Disclosure Timing",
            yaxis_title="Volatility Change",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        
        st.markdown("**No Executive Turnover:**")
        st.write(f"• Immediate: {no_exec_imm.mean():.6f} (n={len(no_exec_imm)})")
        st.write(f"• Delayed: {no_exec_del.mean():.6f} (n={len(no_exec_del)})")
        
        st.markdown("**With Executive Turnover:**")
        st.write(f"• Immediate: {exec_imm.mean():.6f} (n={len(exec_imm)})")
        st.write(f"• Delayed: {exec_del.mean():.6f} (n={len(exec_del)})")
        
        st.markdown("**Interaction Effect:**")
        if len(exec_del) > 0 and len(no_exec_imm) > 0:
            interaction = (exec_del.mean() - exec_imm.mean()) - \
                         (no_exec_del.mean() - no_exec_imm.mean())
            st.write(f"• {interaction:.6f}")

with tabs[2]:
    st.markdown("### Regulatory Enforcement as Governance Mechanism")
    
    st.markdown("""
    **Hypothesis:** Firms facing regulatory action experience different volatility patterns, 
    reflecting market expectations of enforcement and penalties.
    """)
    
    # Split by regulatory action and disclosure timing
    no_reg_imm = volatility_df[(volatility_df['has_any_regulatory_action']==0) & 
                               (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    no_reg_del = volatility_df[(volatility_df['has_any_regulatory_action']==0) & 
                               (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    reg_imm = volatility_df[(volatility_df['has_any_regulatory_action']==1) & 
                            (volatility_df['immediate_disclosure']==1)]['volatility_change'].dropna()
    reg_del = volatility_df[(volatility_df['has_any_regulatory_action']==1) & 
                            (volatility_df['delayed_disclosure']==1)]['volatility_change'].dropna()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Box(y=no_reg_imm, name='No Action, Immediate', 
                            marker_color='lightgreen'))
        fig.add_trace(go.Box(y=no_reg_del, name='No Action, Delayed', 
                            marker_color='yellow'))
        fig.add_trace(go.Box(y=reg_imm, name='Regulatory Action, Immediate', 
                            marker_color='orange'))
        fig.add_trace(go.Box(y=reg_del, name='Regulatory Action, Delayed', 
                            marker_color='darkred'))
        
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        fig.update_layout(
            title="Volatility Change: Regulatory Action × Disclosure Timing",
            yaxis_title="Volatility Change",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Statistics")
        
        st.markdown("**No Regulatory Action:**")
        st.write(f"• Immediate: {no_reg_imm.mean():.6f} (n={len(no_reg_imm)})")
        st.write(f"• Delayed: {no_reg_del.mean():.6f} (n={len(no_reg_del)})")
        
        st.markdown("**With Regulatory Action:**")
        if len(reg_imm) > 0:
            st.write(f"• Immediate: {reg_imm.mean():.6f} (n={len(reg_imm)})")
        if len(reg_del) > 0:
            st.write(f"• Delayed: {reg_del.mean():.6f} (n={len(reg_del)})")

with tabs[3]:
    st.markdown("### Combined Governance View")
    
    # Create heatmap of mean volatility changes across all combinations
    governance_combos = []
    
    for prior in [0, 1]:
        for exec_change in [0, 1]:
            for disclosure in [0, 1]:
                subset = volatility_df[
                    (volatility_df['is_repeat_offender'] == prior) &
                    (volatility_df['has_executive_change'] == exec_change) &
                    (volatility_df['immediate_disclosure'] == disclosure)
                ]['volatility_change'].dropna()
                
                if len(subset) > 0:
                    governance_combos.append({
                        'Prior Breaches': 'Yes' if prior else 'No',
                        'Exec Turnover': 'Yes' if exec_change else 'No',
                        'Immediate Disclosure': 'Yes' if disclosure else 'No',
                        'Mean Volatility Change': subset.mean(),
                        'N': len(subset)
                    })
    
    combo_df = pd.DataFrame(governance_combos)
    
    st.dataframe(combo_df.style.background_gradient(subset=['Mean Volatility Change'], 
                                                    cmap='RdYlGn_r'),
                use_container_width=True)

# ============================================================================
# SUMMARY
# ============================================================================

st.markdown("---")
st.markdown("## 📋 Key Findings Summary")

st.markdown("""
<div style='background-color: #e8f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;'>
<h4>Main Results:</h4>
<ul>
    <li><b>Baseline Effect:</b> Data breaches significantly increase return volatility, indicating heightened information asymmetry</li>
    <li><b>Disclosure Timing:</b> Immediate vs delayed disclosure shows different impacts on information uncertainty</li>
    <li><b>Reputation Effect:</b> Repeat offenders experience different volatility patterns than first-time breaches</li>
    <li><b>Accountability Signal:</b> Executive turnover moderates the volatility response</li>
    <li><b>Enforcement Effect:</b> Regulatory actions influence information resolution</li>
</ul>
</div>
""", unsafe_allow_html=True)