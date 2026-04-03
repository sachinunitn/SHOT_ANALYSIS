"""
Advanced Shot Analysis Dashboard using Streamlit & mplsoccer
=============================================================

This app provides interactive visualization and analysis of football shot data
from Understat, including:
- Pitch visualization with mplsoccer
- Distance-based shot analysis
- Angle-based shot analysis
- Combined distance-angle heatmap
- Interactive filters (player, team, match, result)

Libraries Required:
    pip install streamlit pandas numpy matplotlib mplsoccer scipy
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from mplsoccer import Pitch
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# 1. UTILITY FUNCTIONS - DISTANCE & ANGLE CALCULATIONS
# ============================================================================

def calculate_distance(x, y, goal_x=1.0, goal_y=0.5):
    """
    Calculate Euclidean distance from shot location to goal center.
    
    Parameters:
    -----------
    x : float
        Shot X coordinate (Understat format: 0-1, where 1 is goal line)
    y : float
        Shot Y coordinate (Understat format: 0-1, where 0.5 is center)
    goal_x : float
        Goal line X coordinate (default 1.0 for attacking direction)
    goal_y : float
        Goal center Y coordinate (default 0.5)
    
    Returns:
    --------
    float
        Distance in meters (assuming pitch is 105m x 68m)
    """
    # Convert normalized coordinates to meters
    # Understat uses normalized coordinates (0-1)
    # Standard pitch: 105m x 68m
    x_meters = x * 105
    y_meters = y * 68
    goal_x_meters = goal_x * 105
    goal_y_meters = goal_y * 68
    
    distance = np.sqrt((x_meters - goal_x_meters)**2 + (y_meters - goal_y_meters)**2)
    return distance


def calculate_angle(x, y, goal_y=0.5):
    """
    Calculate shot angle relative to goal center.
    
    Parameters:
    -----------
    x : float
        Shot X coordinate (0-1)
    y : float
        Shot Y coordinate (0-1)
    goal_y : float
        Goal center Y coordinate (default 0.5)
    
    Returns:
    --------
    float
        Angle in degrees (0-90°)
    """
    # Convert to meters
    x_meters = x * 105
    y_meters = y * 68
    goal_y_meters = goal_y * 68
    
    # Distance to goal line
    dist_to_goal = (1 - x) * 105
    
    # Angle from perpendicular
    angle_rad = np.arctan(np.abs(y_meters - goal_y_meters) / (dist_to_goal + 1e-6))
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg


def bin_distance(distance):
    """Bin distance into predefined categories."""
    if distance < 6:
        return '0-6m'
    elif distance < 12:
        return '6-12m'
    elif distance < 18:
        return '12-18m'
    elif distance < 24:
        return '18-24m'
    else:
        return '24+m'


def bin_angle(angle):
    """Bin angle into predefined categories."""
    if angle < 10:
        return '0-10°'
    elif angle < 20:
        return '10-20°'
    elif angle < 30:
        return '20-30°'
    elif angle < 40:
        return '30-40°'
    elif angle < 50:
        return '40-50°'
    else:
        return '50-60°'


# ============================================================================
# 2. DATA LOADING & PROCESSING
# ============================================================================

@st.cache_data
def load_and_process_data(filepath):
    """
    Load Understat CSV and compute distance/angle metrics.
    
    Parameters:
    -----------
    filepath : str
        Path to Understat CSV file
    
    Returns:
    --------
    pd.DataFrame
        Processed dataframe with distance, angle, and bin columns
    """
    df = pd.read_csv(filepath)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Map result to binary: 1 if goal, 0 otherwise
    df['is_goal'] = (df['result'] == 'Goal').astype(int)
    
    # Calculate distance and angle
    df['distance'] = df.apply(lambda row: calculate_distance(row['X'], row['Y']), axis=1)
    df['angle'] = df.apply(lambda row: calculate_angle(row['X'], row['Y']), axis=1)
    
    # Bin distance and angle
    df['distance_bin'] = df['distance'].apply(bin_distance)
    df['angle_bin'] = df['angle'].apply(bin_angle)
    
    return df


# ============================================================================
# 3. ANALYSIS FUNCTIONS
# ============================================================================

def get_distance_analysis(df):
    """
    Aggregate shots by distance bin.
    
    Returns:
    --------
    pd.DataFrame
        Summary with shots, goals, and conversion rate by distance
    """
    distance_order = ['0-6m', '6-12m', '12-18m', '18-24m', '24+m']
    
    analysis = df.groupby('distance_bin').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    analysis.columns = ['distance_bin', 'goals', 'shots']
    analysis['conversion_rate'] = (analysis['goals'] / analysis['shots'] * 100).round(1)
    
    # Ensure all bins are present
    analysis['distance_bin'] = pd.Categorical(analysis['distance_bin'], 
                                               categories=distance_order, 
                                               ordered=True)
    analysis = analysis.sort_values('distance_bin').reset_index(drop=True)
    
    return analysis


def get_angle_analysis(df):
    """
    Aggregate shots by angle bin.
    
    Returns:
    --------
    pd.DataFrame
        Summary with shots, goals, and conversion rate by angle
    """
    angle_order = ['0-10°', '10-20°', '20-30°', '30-40°', '40-50°', '50-60°']
    
    analysis = df.groupby('angle_bin').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    analysis.columns = ['angle_bin', 'goals', 'shots']
    analysis['conversion_rate'] = (analysis['goals'] / analysis['shots'] * 100).round(1)
    
    # Ensure all bins are present
    analysis['angle_bin'] = pd.Categorical(analysis['angle_bin'], 
                                            categories=angle_order, 
                                            ordered=True)
    analysis = analysis.sort_values('angle_bin').reset_index(drop=True)
    
    return analysis


def get_combined_analysis(df):
    """
    Create a 2D matrix of distance vs angle with goal counts.
    
    Returns:
    --------
    pd.DataFrame
        Pivot table with distance bins as rows, angle bins as columns
    """
    distance_order = ['0-6m', '6-12m', '12-18m', '18-24m', '24+m']
    angle_order = ['0-10°', '10-20°', '20-30°', '30-40°', '40-50°', '50-60°']
    
    # Create pivot table of goals by distance and angle
    pivot = df[df['is_goal'] == 1].pivot_table(
        index='distance_bin',
        columns='angle_bin',
        aggfunc='size',
        fill_value=0
    )
    
    # Reorder and fill missing categories
    pivot = pivot.reindex(index=distance_order, columns=angle_order, fill_value=0)
    
    return pivot


# ============================================================================
# 4. VISUALIZATION FUNCTIONS
# ============================================================================

def plot_pitch_with_shots(df, figsize=(10, 7)):
    """
    Plot football pitch with shot locations using mplsoccer.
    
    Color coding:
    - Red: Goals
    - Yellow: Shots (not goals)
    - Gray: Missed/Blocked shots
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create pitch (opta: 0-100 scale; Understat uses 0-1, so multiply by 100)
    pitch = Pitch(pitch_type='opta', 
                  pitch_color='#22844e',
                  line_color='white',
                  linewidth=1.5,
                  half=True)
    pitch.draw(ax=ax)
    
    # Separate shots by result
    goals = df[df['result'] == 'Goal']
    shots = df[df['result'] == 'MissedShots']
    saved = df[df['result'] == 'SavedShot']
    blocked = df[df['result'] == 'BlockedShot']
    post = df[df['result'] == 'ShotOnPost']
    
    # Plot shots with different colors (scale Understat 0-1 coords to opta 0-100)
    if len(blocked) > 0:
        pitch.scatter(blocked['X'] * 100, blocked['Y'] * 100, s=100, alpha=0.5, 
                     color='gray', edgecolors='black', linewidth=0.5, 
                     label='Blocked', ax=ax)
    
    if len(saved) > 0:
        pitch.scatter(saved['X'] * 100, saved['Y'] * 100, s=100, alpha=0.6, 
                     color='orange', edgecolors='black', linewidth=0.5, 
                     label='Saved', ax=ax)
    
    if len(shots) > 0:
        pitch.scatter(shots['X'] * 100, shots['Y'] * 100, s=100, alpha=0.6, 
                     color='yellow', edgecolors='black', linewidth=0.5, 
                     label='Missed', ax=ax)
    
    if len(post) > 0:
        pitch.scatter(post['X'] * 100, post['Y'] * 100, s=120, alpha=0.7, 
                     color='cyan', edgecolors='black', linewidth=0.5, 
                     label='Post', ax=ax)
    
    if len(goals) > 0:
        pitch.scatter(goals['X'] * 100, goals['Y'] * 100, s=150, alpha=0.9, 
                     color='red', edgecolors='darkred', linewidth=1.2, 
                     label='Goal', ax=ax, marker='*')
    
    ax.legend(loc='upper left', framealpha=0.9)
    ax.set_title('Shot Map', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig


def plot_distance_heatmap(distance_analysis, figsize=(10, 4)):
    """Plot conversion rate by distance as heatmap."""
    fig, ax = plt.subplots(figsize=figsize)
    
    data = distance_analysis[['distance_bin', 'conversion_rate']].set_index('distance_bin')
    
    # Create heatmap
    im = ax.imshow(data.T.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(data.index, rotation=0)
    ax.set_yticks([0])
    ax.set_yticklabels(['Conversion %'])
    
    # Add text annotations
    for i, (idx, row) in enumerate(data.iterrows()):
        ax.text(i, 0, f"{row['conversion_rate']:.1f}%", 
               ha='center', va='center', color='black', fontweight='bold')
    
    ax.set_title('Conversion Rate by Distance', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Conversion Rate (%)')
    plt.tight_layout()
    
    return fig


def plot_angle_heatmap(angle_analysis, figsize=(12, 4)):
    """Plot conversion rate by angle as heatmap."""
    fig, ax = plt.subplots(figsize=figsize)
    
    data = angle_analysis[['angle_bin', 'conversion_rate']].set_index('angle_bin')
    
    # Create heatmap
    im = ax.imshow(data.T.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(data.index, rotation=0)
    ax.set_yticks([0])
    ax.set_yticklabels(['Conversion %'])
    
    # Add text annotations
    for i, (idx, row) in enumerate(data.iterrows()):
        ax.text(i, 0, f"{row['conversion_rate']:.1f}%", 
               ha='center', va='center', color='black', fontweight='bold')
    
    ax.set_title('Conversion Rate by Angle', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Conversion Rate (%)')
    plt.tight_layout()
    
    return fig


def plot_combined_heatmap(combined_data, figsize=(12, 6)):
    """Plot 2D heatmap of goals by distance and angle."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create heatmap
    im = ax.imshow(combined_data.values, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(range(len(combined_data.columns)))
    ax.set_yticks(range(len(combined_data.index)))
    ax.set_xticklabels(combined_data.columns, rotation=45, ha='right')
    ax.set_yticklabels(combined_data.index)
    
    ax.set_xlabel('Angle', fontweight='bold')
    ax.set_ylabel('Distance', fontweight='bold')
    ax.set_title('Goals by Distance & Angle', fontsize=12, fontweight='bold')
    
    # Add text annotations
    for i in range(len(combined_data.index)):
        for j in range(len(combined_data.columns)):
            text = ax.text(j, i, int(combined_data.iloc[i, j]),
                          ha='center', va='center', color='black', fontweight='bold')
    
    plt.colorbar(im, ax=ax, label='Goals')
    plt.tight_layout()
    
    return fig


# ============================================================================
# 5. STREAMLIT APP CONFIGURATION & LAYOUT
# ============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Shot Analysis Dashboard",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title
    st.markdown("""
    # ⚽ Advanced Shot Analysis Dashboard
    *Powered by Understat data & mplsoccer visualization*
    """)
    
    # Load data
    try:
        df = load_and_process_data('erling_haaland_2022_understat.csv')
    except FileNotFoundError:
        st.error("Dataset not found. Please ensure 'erling_haaland_2022_understat.csv' is in the app directory.")
        return
    
    # ========================================================================
    # SIDEBAR: FILTERS
    # ========================================================================
    st.sidebar.markdown("## 🎯 Filters")
    
    # Player filter
    players = sorted(df['player'].unique())
    selected_player = st.sidebar.selectbox('Player', players, index=0)
    
    # Team filter
    teams = sorted(set(df['h_team'].unique()) | set(df['a_team'].unique()))
    selected_team = st.sidebar.multiselect('Team', teams, 
                                           default=teams)
    
    # Match filter
    matches = sorted(df['match_id'].unique())
    selected_matches = st.sidebar.multiselect('Match', matches, 
                                              default=list(matches))
    
    # Result filter
    results = sorted(df['result'].unique())
    selected_results = st.sidebar.multiselect('Shot Result', results, 
                                             default=results)
    
    # Apply filters
    filtered_df = df[
        (df['player'] == selected_player) &
        ((df['h_team'].isin(selected_team)) | (df['a_team'].isin(selected_team))) &
        (df['match_id'].isin(selected_matches)) &
        (df['result'].isin(selected_results))
    ]
    
    # Display filter summary
    st.sidebar.markdown(f"""
    ### 📊 Summary
    - **Shots**: {len(filtered_df)}
    - **Goals**: {filtered_df['is_goal'].sum()}
    - **Conversion**: {(filtered_df['is_goal'].sum() / len(filtered_df) * 100):.1f}%
    """)
    
    # ========================================================================
    # MAIN CONTENT: 3-COLUMN LAYOUT
    # ========================================================================
    
    col1, col2, col3 = st.columns([1.2, 1.2, 1.0], gap="medium")
    
    # COLUMN 1: PITCH VISUALIZATION
    with col1:
        st.markdown("### 🎯 Shot Map")
        fig_pitch = plot_pitch_with_shots(filtered_df)
        st.pyplot(fig_pitch, use_container_width=True)
    
    # COLUMN 2: DISTANCE ANALYSIS
    with col2:
        st.markdown("### 📏 Distance Analysis")
        distance_analysis = get_distance_analysis(filtered_df)
        st.dataframe(distance_analysis, use_container_width=True, hide_index=True)
        
        # Distance heatmap
        fig_dist = plot_distance_heatmap(distance_analysis, figsize=(8, 3))
        st.pyplot(fig_dist, use_container_width=True)
    
    # COLUMN 3: ANGLE ANALYSIS
    with col3:
        st.markdown("### 📐 Angle Analysis")
        angle_analysis = get_angle_analysis(filtered_df)
        st.dataframe(angle_analysis.drop('angle_bin', axis=1), 
                    use_container_width=True, hide_index=True)
        
        # Angle heatmap
        fig_angle = plot_angle_heatmap(angle_analysis, figsize=(10, 3))
        st.pyplot(fig_angle, use_container_width=True)
    
    # ========================================================================
    # BOTTOM: COMBINED ANALYSIS
    # ========================================================================
    st.markdown("---")
    st.markdown("### 🔥 Combined Distance-Angle Heatmap (Goals)")
    
    combined_analysis = get_combined_analysis(filtered_df)
    fig_combined = plot_combined_heatmap(combined_analysis)
    st.pyplot(fig_combined, use_container_width=True)
    
    # Display combined data as table
    st.markdown("#### Goals by Distance & Angle")
    st.dataframe(combined_analysis, use_container_width=True)
    
    # ========================================================================
    # DETAILED DATA TABLE
    # ========================================================================
    st.markdown("---")
    with st.expander("📋 View Detailed Shot Data"):
        display_cols = ['date', 'player', 'h_team', 'a_team', 'result', 
                       'X', 'Y', 'distance', 'angle', 'xG']
        st.dataframe(filtered_df[display_cols].sort_values('date', ascending=False), 
                    use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
