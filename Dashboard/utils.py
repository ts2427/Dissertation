import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_data():
    """Load the enriched dataset"""
    df = pd.read_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')
    df['breach_date'] = pd.to_datetime(df['breach_date'])
    df['breach_year'] = df['breach_date'].dt.year
    return df

def create_summary_stats(df):
    """Create summary statistics"""
    stats = {
        'Total Breaches': len(df),
        'Unique Companies': df['org_name'].nunique(),
        'Date Range': f"{df['breach_date'].min().year} - {df['breach_date'].max().year}",
        'Breaches with CRSP Data': df['has_crsp_data'].sum(),
        'Mean CAR (30-day)': f"{df['car_30d'].mean():.2f}%",
        'Repeat Offenders': f"{df['is_repeat_offender'].sum()} ({df['is_repeat_offender'].mean()*100:.1f}%)",
        'Executive Turnover': f"{df['has_executive_change'].sum()} ({df['has_executive_change'].mean()*100:.1f}%)",
        'Regulatory Actions': f"{df['has_any_regulatory_action'].sum()} ({df['has_any_regulatory_action'].mean()*100:.1f}%)",
        'Total Penalties': f"${df['total_regulatory_cost'].sum()/1e9:.2f}B",
        'Dark Web Breaches': f"{df['in_hibp'].sum()} ({df['in_hibp'].mean()*100:.1f}%)"
    }
    return stats

def create_timeline_chart(df):
    """Create interactive timeline chart"""
    timeline = df.groupby('breach_year').size().reset_index(name='count')
    
    fig = px.bar(timeline, x='breach_year', y='count',
                 title='Data Breaches Over Time (2004-2025)',
                 labels={'breach_year': 'Year', 'count': 'Number of Breaches'},
                 color='count',
                 color_continuous_scale='Reds')
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of Breaches",
        showlegend=False,
        height=400
    )
    
    return fig

def create_car_distribution(df):
    """Create CAR distribution chart"""
    fig = go.Figure()
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=df['car_30d'].dropna(),
        nbinsx=50,
        name='30-Day CAR',
        marker_color='steelblue',
        opacity=0.7
    ))
    
    # Add mean line
    mean_car = df['car_30d'].mean()
    fig.add_vline(x=mean_car, line_dash="dash", line_color="red",
                  annotation_text=f"Mean: {mean_car:.2f}%",
                  annotation_position="top right")
    
    fig.update_layout(
        title='Distribution of 30-Day Cumulative Abnormal Returns',
        xaxis_title='CAR (%)',
        yaxis_title='Frequency',
        showlegend=False,
        height=400
    )
    
    return fig

def create_comparison_boxplot(df, group_var, group_labels, title):
    """Create comparison boxplot"""
    fig = go.Figure()
    
    for i, label in enumerate(group_labels):
        data = df[df[group_var] == i]['car_30d'].dropna()
        
        fig.add_trace(go.Box(
            y=data,
            name=label,
            boxmean='sd'
        ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title=title,
        yaxis_title='30-Day CAR (%)',
        showlegend=True,
        height=400
    )
    
    return fig

def create_enrichment_pie(df, column, labels, title, colors=None):
    """Create pie chart for enrichment data"""
    values = [df[column].sum(), len(df) - df[column].sum()]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors or ['#FF6B6B', '#4ECDC4']
    )])
    
    fig.update_layout(
        title=title,
        height=300
    )
    
    return fig

def create_correlation_heatmap(df, variables, var_names):
    """Create correlation heatmap"""
    corr_data = df[variables].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_data.values,
        x=var_names,
        y=var_names,
        colorscale='RdBu',
        zmid=0,
        text=corr_data.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title='Correlation Matrix',
        height=600,
        width=800
    )
    
    return fig

def create_scatter_with_trend(df, x_var, y_var, x_label, y_label, title):
    """Create scatter plot with trendline"""
    fig = px.scatter(df, x=x_var, y=y_var,
                     trendline="ols",
                     labels={x_var: x_label, y_var: y_label},
                     title=title)
    
    fig.update_layout(height=400)
    
    return fig

def format_large_number(num):
    """Format large numbers for display"""
    if num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    elif num >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"

def calculate_statistics(series):
    """Calculate descriptive statistics"""
    return {
        'Count': len(series),
        'Mean': series.mean(),
        'Std Dev': series.std(),
        'Min': series.min(),
        '25%': series.quantile(0.25),
        'Median': series.median(),
        '75%': series.quantile(0.75),
        'Max': series.max()
    }