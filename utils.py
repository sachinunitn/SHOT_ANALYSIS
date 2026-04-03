"""
Utility Functions for Shot Analysis
====================================

This module provides additional helper functions for shot analysis,
including data validation, metrics computation, and export utilities.

Usage:
    from utils import validate_data, calculate_xg_binned, export_analysis
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate Understat data format.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to validate
    
    Returns:
    --------
    Tuple[bool, List[str]]
        (is_valid, list_of_errors)
    """
    required_columns = ['X', 'Y', 'result', 'player', 'match_id']
    errors = []
    
    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing columns: {', '.join(missing_cols)}")
    
    # Check data types
    if 'X' in df.columns and not pd.api.types.is_numeric_dtype(df['X']):
        errors.append("Column 'X' must be numeric")
    
    if 'Y' in df.columns and not pd.api.types.is_numeric_dtype(df['Y']):
        errors.append("Column 'Y' must be numeric")
    
    # Check value ranges
    if 'X' in df.columns:
        if (df['X'] < 0).any() or (df['X'] > 1).any():
            errors.append("Column 'X' values should be between 0 and 1")
    
    if 'Y' in df.columns:
        if (df['Y'] < 0).any() or (df['Y'] > 1).any():
            errors.append("Column 'Y' values should be between 0 and 1")
    
    # Check result values
    valid_results = {'Goal', 'MissedShots', 'SavedShot', 'BlockedShot'}
    if 'result' in df.columns:
        invalid_results = set(df['result'].unique()) - valid_results
        if invalid_results:
            print(f"Warning: Unknown result types found: {invalid_results}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def check_data_quality(df: pd.DataFrame) -> Dict[str, any]:
    """
    Assess data quality with statistics.
    
    Returns:
    --------
    Dict with quality metrics
    """
    return {
        'total_shots': len(df),
        'unique_players': df['player'].nunique(),
        'unique_matches': df['match_id'].nunique(),
        'missing_values': df.isnull().sum().to_dict(),
        'shot_result_distribution': df['result'].value_counts().to_dict(),
        'x_range': (df['X'].min(), df['X'].max()),
        'y_range': (df['Y'].min(), df['Y'].max()),
    }


# ============================================================================
# ADVANCED METRICS
# ============================================================================

def calculate_xg_binned(df: pd.DataFrame, distance_bin: str) -> float:
    """
    Calculate total expected goals for a specific distance bin.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Shot data with distance_bin and xG columns
    distance_bin : str
        Distance bin (e.g., '0-6m')
    
    Returns:
    --------
    float
        Sum of xG for the bin
    """
    return df[df['distance_bin'] == distance_bin]['xG'].sum()


def calculate_underperformance(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate goal underperformance vs xG.
    
    Returns:
    --------
    Dict with metrics
    """
    total_goals = df['is_goal'].sum()
    total_xg = df['xG'].sum()
    
    return {
        'total_goals': total_goals,
        'total_xg': total_xg,
        'difference': total_goals - total_xg,
        'overperformance_pct': ((total_goals - total_xg) / total_xg * 100) if total_xg > 0 else 0
    }


def calculate_shot_efficiency_by_assist(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze conversion rate by assist type.
    
    Returns:
    --------
    pd.DataFrame
        Efficiency by assist type
    """
    assist_analysis = df.groupby('lastAction').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    assist_analysis.columns = ['assist_type', 'goals', 'shots']
    assist_analysis['conversion_rate'] = (
        assist_analysis['goals'] / assist_analysis['shots'] * 100
    ).round(1)
    
    return assist_analysis.sort_values('conversion_rate', ascending=False)


def calculate_shot_efficiency_by_situation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze conversion rate by game situation (open play, penalty, corner, etc.).
    
    Returns:
    --------
    pd.DataFrame
        Efficiency by situation
    """
    situation_analysis = df.groupby('situation').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    situation_analysis.columns = ['situation', 'goals', 'shots']
    situation_analysis['conversion_rate'] = (
        situation_analysis['goals'] / situation_analysis['shots'] * 100
    ).round(1)
    
    return situation_analysis.sort_values('conversion_rate', ascending=False)


def calculate_shot_efficiency_by_foot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze conversion rate by shot type (left foot, right foot, head).
    
    Returns:
    --------
    pd.DataFrame
        Efficiency by shot type
    """
    foot_analysis = df.groupby('shotType').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    foot_analysis.columns = ['shot_type', 'goals', 'shots']
    foot_analysis['conversion_rate'] = (
        foot_analysis['goals'] / foot_analysis['shots'] * 100
    ).round(1)
    
    return foot_analysis.sort_values('conversion_rate', ascending=False)


# ============================================================================
# TIME-BASED ANALYSIS
# ============================================================================

def analyze_shots_by_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze shot efficiency by match period.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Must have 'minute' column
    
    Returns:
    --------
    pd.DataFrame
        Statistics by 15-minute periods
    """
    df = df.copy()
    df['period'] = pd.cut(df['minute'], 
                          bins=[0, 15, 30, 45, 60, 75, 90, 120],
                          labels=['0-15', '15-30', '30-45', '45-60', 
                                  '60-75', '75-90', '90+'])
    
    period_analysis = df.groupby('period').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    period_analysis.columns = ['period', 'goals', 'shots']
    period_analysis['conversion_rate'] = (
        period_analysis['goals'] / period_analysis['shots'] * 100
    ).round(1)
    
    return period_analysis


def analyze_home_away(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare shot efficiency between home and away matches.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Must have 'h_a' column ('h' for home, 'a' for away)
    
    Returns:
    --------
    pd.DataFrame
        Home vs Away comparison
    """
    ha_analysis = df.groupby('h_a').agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    ha_analysis.columns = ['location', 'goals', 'shots']
    ha_analysis['location'] = ha_analysis['location'].map({'h': 'Home', 'a': 'Away'})
    ha_analysis['conversion_rate'] = (
        ha_analysis['goals'] / ha_analysis['shots'] * 100
    ).round(1)
    
    return ha_analysis


# ============================================================================
# EXPORT & REPORTING
# ============================================================================

def export_to_csv(df: pd.DataFrame, filename: str) -> bool:
    """
    Export filtered analysis to CSV.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to export
    filename : str
        Output filename
    
    Returns:
    --------
    bool
        Success status
    """
    try:
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False


def generate_summary_report(df: pd.DataFrame) -> str:
    """
    Generate a text summary report of shot analysis.
    
    Returns:
    --------
    str
        Formatted report
    """
    total_shots = len(df)
    total_goals = df['is_goal'].sum()
    conversion_rate = (total_goals / total_shots * 100) if total_shots > 0 else 0
    total_xg = df['xG'].sum()
    avg_distance = df['distance'].mean()
    avg_angle = df['angle'].mean()
    
    report = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║              SHOT ANALYSIS SUMMARY REPORT                ║
    ╚══════════════════════════════════════════════════════════╝
    
    OVERALL STATISTICS
    ─────────────────────────────────────────────────────────
    Total Shots:              {total_shots:>6}
    Goals Scored:             {total_goals:>6}
    Conversion Rate:          {conversion_rate:>5.1f}%
    Expected Goals (xG):      {total_xg:>6.2f}
    
    SPATIAL STATISTICS
    ─────────────────────────────────────────────────────────
    Average Distance:         {avg_distance:>6.2f} meters
    Average Angle:            {avg_angle:>6.2f} degrees
    Min Distance:             {df['distance'].min():>6.2f} meters
    Max Distance:             {df['distance'].max():>6.2f} meters
    
    SHOT BREAKDOWN
    ─────────────────────────────────────────────────────────
    """
    
    for result, count in df['result'].value_counts().items():
        percentage = (count / total_shots * 100)
        report += f"    {result:<20} {count:>6} ({percentage:>5.1f}%)\n"
    
    report += "\n    ══════════════════════════════════════════════════════════\n"
    
    return report


def print_analysis_summary(df: pd.DataFrame):
    """
    Print analysis summary to console.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Filtered shot data
    """
    print(generate_summary_report(df))


# ============================================================================
# COMPARISON UTILITIES
# ============================================================================

def compare_players(df: pd.DataFrame, players: List[str]) -> pd.DataFrame:
    """
    Compare statistics across multiple players.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Full shot data
    players : List[str]
        List of player names to compare
    
    Returns:
    --------
    pd.DataFrame
        Comparative statistics
    """
    comparison = df[df['player'].isin(players)].groupby('player').agg({
        'is_goal': ['sum', 'count'],
        'distance': 'mean',
        'angle': 'mean',
        'xG': 'sum'
    }).reset_index()
    
    comparison.columns = ['player', 'goals', 'shots', 'avg_distance', 
                         'avg_angle', 'total_xg']
    comparison['conversion_rate'] = (
        comparison['goals'] / comparison['shots'] * 100
    ).round(1)
    
    return comparison.sort_values('goals', ascending=False)


# ============================================================================
# DISTANCE-ANGLE ADVANCED ANALYSIS
# ============================================================================

def get_optimal_shooting_zone(df: pd.DataFrame) -> Dict[str, any]:
    """
    Identify the most efficient shooting zone (distance-angle combination).
    
    Returns:
    --------
    Dict with optimal zone info
    """
    optimal = df.groupby(['distance_bin', 'angle_bin']).agg({
        'is_goal': ['sum', 'count']
    }).reset_index()
    
    optimal.columns = ['distance_bin', 'angle_bin', 'goals', 'shots']
    optimal['conversion_rate'] = (
        optimal['goals'] / optimal['shots'] * 100
    ).round(1)
    
    best = optimal.loc[optimal['conversion_rate'].idxmax()]
    
    return {
        'distance_bin': best['distance_bin'],
        'angle_bin': best['angle_bin'],
        'conversion_rate': best['conversion_rate'],
        'goals': int(best['goals']),
        'shots': int(best['shots'])
    }


if __name__ == "__main__":
    # Example usage
    print("Shot Analysis Utilities Module")
    print("Import these functions in your Streamlit app or scripts")
