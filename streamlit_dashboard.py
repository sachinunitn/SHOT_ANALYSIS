"""
Multi-Player Shot Analysis Streamlit Dashboard
================================================

Production-ready, multi-tab Streamlit application for interactive
shot analysis across multiple players.

Tabs
----
1. 📊 Overview & Comparison
2. 🔍 Player Deep-Dive
3. 🗺️ Zone Analysis
4. 📈 Trend Analysis
5. 💾 Export & Data

Run
---
    streamlit run streamlit_dashboard.py

Requirements
------------
    pip install streamlit pandas numpy matplotlib mplsoccer scipy plotly seaborn
"""

import io
import warnings
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

warnings.filterwarnings('ignore')

# ============================================================================
# LOCAL IMPORTS
# ============================================================================

try:
    from multi_player_config import get_multi_player_config, MULTI_CONFIG
    from data_processor import MultiPlayerDataProcessor
    from advanced_metrics import ShotMetricsCalculator, PlayerComparison
    from visualizations import ShotVisualizer
    MODULES_OK = True
except ImportError as _import_err:
    MODULES_OK = False
    _IMPORT_ERROR = str(_import_err)


# ============================================================================
# PAGE CONFIGURATION (must be first Streamlit call)
# ============================================================================

st.set_page_config(
    page_title='Multi-Player Shot Analysis Dashboard',
    page_icon='⚽',
    layout='wide',
    initial_sidebar_state='expanded',
)


# ============================================================================
# CACHED DATA LOADING & PROCESSING
# ============================================================================

@st.cache_data(show_spinner='Loading & processing data…')
def load_data(filepath: str) -> pd.DataFrame:
    """Load, clean, and feature-engineer shot data from CSV."""
    config = get_multi_player_config()
    processor = MultiPlayerDataProcessor(config)
    df_raw = processor.load_from_csv(filepath)
    df_clean = processor.preprocess(df_raw)
    df_feat = processor.add_features(df_clean)
    return df_feat


@st.cache_data(show_spinner=False)
def compute_player_metrics(df_json: str) -> pd.DataFrame:
    """Compute per-player metrics from a JSON-serialised dataframe."""
    df = pd.read_json(io.StringIO(df_json), orient='split')
    config = get_multi_player_config()
    calculator = ShotMetricsCalculator(config)
    return calculator.per_player_metrics(df)


# ============================================================================
# HELPER: APPLY SIDEBAR FILTERS
# ============================================================================

def apply_filters(
    df: pd.DataFrame,
    selected_players: List[str],
    selected_results: List[str],
    selected_shot_types: List[str],
    selected_situations: List[str],
    date_range: Optional[Tuple] = None,
    selected_seasons: Optional[List[int]] = None,
    min_xg: float = 0.0,
) -> pd.DataFrame:
    """Apply all sidebar filters and return the filtered dataframe."""
    filtered = df.copy()

    if selected_players:
        filtered = filtered[filtered['player'].isin(selected_players)]
    if selected_results:
        filtered = filtered[filtered['result'].isin(selected_results)]
    if selected_shot_types and 'shotType' in filtered.columns:
        filtered = filtered[filtered['shotType'].isin(selected_shot_types)]
    if selected_situations and 'situation' in filtered.columns:
        filtered = filtered[filtered['situation'].isin(selected_situations)]
    if date_range and 'date' in filtered.columns:
        filtered['date'] = pd.to_datetime(filtered['date'], errors='coerce')
        start, end = date_range
        filtered = filtered[
            filtered['date'].between(pd.Timestamp(start), pd.Timestamp(end))
        ]
    if selected_seasons and 'season' in filtered.columns:
        filtered = filtered[filtered['season'].isin(selected_seasons)]
    if min_xg > 0 and 'xG' in filtered.columns:
        filtered = filtered[filtered['xG'] >= min_xg]

    return filtered.reset_index(drop=True)


# ============================================================================
# HELPER: SUMMARY METRIC CARDS
# ============================================================================

def render_kpi_cards(df: pd.DataFrame) -> None:
    """Render KPI cards in a 4-column row."""
    n_shots = len(df)
    n_goals = int(df['is_goal'].sum()) if 'is_goal' in df.columns else 0
    conv = round(n_goals / n_shots * 100, 1) if n_shots > 0 else 0.0
    xg = round(df['xG'].sum(), 2) if 'xG' in df.columns else 0.0
    xg_diff = round(n_goals - xg, 2)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('🎯 Total Shots', f'{n_shots:,}')
    col2.metric('⚽ Goals', f'{n_goals:,}')
    col3.metric('📊 Conversion Rate', f'{conv}%')
    col4.metric('🔢 xG Difference', f'+{xg_diff}' if xg_diff >= 0 else str(xg_diff))


# ============================================================================
# TAB 1: OVERVIEW & COMPARISON
# ============================================================================

def render_tab_overview(
    df: pd.DataFrame,
    config: dict,
    viz: ShotVisualizer,
    calculator: ShotMetricsCalculator,
    comparison: PlayerComparison,
) -> None:
    """Multi-player overview and comparison tab."""

    st.subheader('📊 Multi-Player Overview')
    render_kpi_cards(df)
    st.markdown('---')

    players_in_data = sorted(df['player'].unique().tolist()) if 'player' in df.columns else []

    if len(players_in_data) == 0:
        st.warning('No players found in filtered data.')
        return

    # --- Comparison Table ---
    st.markdown('#### 🏆 Player Comparison Table')
    try:
        comp_table = comparison.build_comparison_table(df)
        display_cols = [c for c in [
            'shots', 'goals', 'conversion_rate', 'total_xg',
            'xg_per_shot', 'xg_difference', 'avg_distance', 'avg_angle',
            'benchmark',
        ] if c in comp_table.columns]
        st.dataframe(
            comp_table[display_cols].style.background_gradient(
                subset=['conversion_rate'] if 'conversion_rate' in display_cols else [],
                cmap='RdYlGn',
            ),
            use_container_width=True,
        )
    except Exception as exc:
        st.warning(f'Could not build comparison table: {exc}')

    st.markdown('---')

    # --- Comparison Bar Chart ---
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('#### Conversion Rate by Player')
        try:
            comp_table = comparison.build_comparison_table(df)
            fig = viz.plot_player_comparison_bars(comp_table, metric='conversion_rate')
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Chart error: {exc}')

    with col_right:
        st.markdown('#### xG per Shot by Player')
        try:
            fig = viz.plot_player_comparison_bars(comp_table, metric='xg_per_shot',
                                                   title='xG per Shot by Player')
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Chart error: {exc}')

    st.markdown('---')

    # --- Radar Chart ---
    st.markdown('#### 🕸️ Shooting Profile Radar')
    max_players_radar = config.get('STREAMLIT', {}).get('max_players_comparison', 5)
    radar_players = players_in_data[:max_players_radar]
    try:
        radar_dict = comparison.radar_data(df, players=radar_players)
        radar_metrics = config.get('RADAR', {}).get('metrics', [])
        labels = [m.get('label', m['key']) for m in radar_metrics]
        fig = viz.plot_radar_comparison(radar_dict, metric_labels=labels)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as exc:
        st.warning(f'Radar chart error: {exc}')


# ============================================================================
# TAB 2: PLAYER DEEP-DIVE
# ============================================================================

def render_tab_deep_dive(
    df: pd.DataFrame,
    config: dict,
    viz: ShotVisualizer,
    calculator: ShotMetricsCalculator,
) -> None:
    """Individual player deep-dive tab."""

    players = sorted(df['player'].unique().tolist()) if 'player' in df.columns else []
    if not players:
        st.warning('No players found.')
        return

    selected = st.selectbox('Select Player', players, key='deep_dive_player')
    player_df = df[df['player'] == selected]

    if player_df.empty:
        st.warning(f'No data for {selected}.')
        return

    # KPI row
    st.markdown(f'#### 🔍 {selected} — Full Analysis')
    render_kpi_cards(player_df)
    st.markdown('---')

    col1, col2 = st.columns(2)

    # Pitch map
    with col1:
        st.markdown('**🎯 Shot Map**')
        try:
            fig = viz.plot_pitch_map(player_df, player=selected)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Pitch map error: {exc}')

    # Scatter distance vs angle
    with col2:
        st.markdown('**📍 Distance vs Angle**')
        color_choice = st.radio(
            'Colour by', ['result', 'xG'], horizontal=True,
            key='deep_scatter_color',
        )
        try:
            fig = viz.plot_scatter_distance_angle(
                player_df, color_by=color_choice, player=selected
            )
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Scatter error: {exc}')

    st.markdown('---')

    col3, col4 = st.columns(2)

    # Distance analysis
    with col3:
        st.markdown('**📏 Distance Analysis**')
        try:
            dist_metrics = calculator.metrics_by_segment(
                player_df, 'distance_bin',
                config.get('DISTANCE_BINS', {}).get('order', []),
            )
            st.dataframe(dist_metrics, use_container_width=True, hide_index=True)
            fig = viz.plot_conversion_by_distance(dist_metrics)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Distance analysis error: {exc}')

    # Angle analysis
    with col4:
        st.markdown('**📐 Angle Analysis**')
        try:
            angle_metrics = calculator.metrics_by_segment(
                player_df, 'angle_bin',
                config.get('ANGLE_BINS', {}).get('order', []),
            )
            st.dataframe(angle_metrics, use_container_width=True, hide_index=True)
            fig = viz.plot_conversion_by_angle(angle_metrics)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Angle analysis error: {exc}')

    st.markdown('---')

    # Combined heatmap
    st.markdown('**🔥 Combined Distance-Angle Heatmap**')
    heatmap_metric = st.selectbox(
        'Metric', ['goals', 'shots', 'conversion_rate', 'xg'],
        key='deep_heatmap_metric',
    )
    try:
        pivot = calculator.combined_heatmap_data(player_df, metric=heatmap_metric)
        fig = viz.plot_distance_angle_heatmap(pivot, metric=heatmap_metric,
                                               title=f'{selected} — {heatmap_metric}')
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as exc:
        st.warning(f'Combined heatmap error: {exc}')

    st.markdown('---')

    # Distribution histograms
    col5, col6 = st.columns(2)
    with col5:
        st.markdown('**📊 Distance Distribution**')
        try:
            fig = viz.plot_distribution(player_df, feature='distance',
                                         players=[selected])
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Distribution error: {exc}')

    with col6:
        st.markdown('**📊 Angle Distribution**')
        try:
            fig = viz.plot_distribution(player_df, feature='angle',
                                         players=[selected])
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Distribution error: {exc}')

    st.markdown('---')

    # xG Analysis
    st.markdown('**💡 xG Analysis**')
    try:
        xg_analysis = calculator.xg_analysis(player_df)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric('Total xG', f"{xg_analysis.get('total_xg', 0):.2f}")
        col_b.metric('Goals - xG', f"{xg_analysis.get('xg_difference', 0):+.2f}")
        col_c.metric(
            'Performance',
            xg_analysis.get('performance_label', 'N/A'),
        )
        if 'xg_breakdown' in xg_analysis:
            st.dataframe(xg_analysis['xg_breakdown'], use_container_width=True,
                         hide_index=True)
    except Exception as exc:
        st.warning(f'xG analysis error: {exc}')


# ============================================================================
# TAB 3: ZONE ANALYSIS
# ============================================================================

def render_tab_zones(
    df: pd.DataFrame,
    config: dict,
    viz: ShotVisualizer,
    calculator: ShotMetricsCalculator,
) -> None:
    """Spatial zone analysis tab."""

    st.subheader('🗺️ Zone Analysis')

    col1, col2 = st.columns(2)

    # Pitch density heatmap
    with col1:
        st.markdown('**Shot Density (All Shots)**')
        try:
            fig = viz.plot_pitch_heatmap(df, show_goals_only=False)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Density heatmap error: {exc}')

    with col2:
        st.markdown('**Goal Density (Goals Only)**')
        try:
            fig = viz.plot_pitch_heatmap(df, show_goals_only=True)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Goal density heatmap error: {exc}')

    st.markdown('---')

    # Zone label metrics
    st.markdown('**⬛ Zone Efficiency (Penalty Box / Half-Space / Outside)**')
    try:
        zone_metrics = calculator.metrics_by_segment(df, 'zone_label')
        if not zone_metrics.empty:
            st.dataframe(zone_metrics, use_container_width=True, hide_index=True)
            fig = viz.plot_metric_bars(
                zone_metrics, 'zone_label', 'conversion_rate',
                title='Conversion Rate by Zone',
            )
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    except Exception as exc:
        st.warning(f'Zone metrics error: {exc}')

    st.markdown('---')

    # Quadrant analysis
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('**⬅️ Quadrant Analysis (Left/Center/Right)**')
        try:
            quad_metrics = calculator.metrics_by_segment(df, 'quadrant')
            if not quad_metrics.empty:
                st.dataframe(quad_metrics, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f'Quadrant error: {exc}')

    with col4:
        st.markdown('**🔥 Combined Heatmap (All Players)**')
        hm_metric = st.selectbox(
            'Metric', ['goals', 'shots', 'conversion_rate', 'xg'],
            key='zone_heatmap_metric',
        )
        try:
            pivot = calculator.combined_heatmap_data(df, metric=hm_metric)
            fig = viz.plot_distance_angle_heatmap(
                pivot, metric=hm_metric,
                title=f'All Players — {hm_metric}',
            )
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Combined heatmap error: {exc}')

    st.markdown('---')

    # Shot-type breakdown
    st.markdown('**🦶 Shot Type Breakdown**')
    try:
        shot_type_metrics = calculator.metrics_by_segment(df, 'shotType')
        if not shot_type_metrics.empty:
            col5, col6 = st.columns(2)
            with col5:
                st.dataframe(shot_type_metrics, use_container_width=True, hide_index=True)
            with col6:
                fig = viz.plot_metric_bars(
                    shot_type_metrics, 'shotType', 'conversion_rate',
                    title='Conversion Rate by Shot Type',
                    color='#9467bd',
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
    except Exception as exc:
        st.warning(f'Shot type analysis error: {exc}')


# ============================================================================
# TAB 4: TREND ANALYSIS
# ============================================================================

def render_tab_trends(
    df: pd.DataFrame,
    config: dict,
    viz: ShotVisualizer,
    calculator: ShotMetricsCalculator,
    comparison: PlayerComparison,
) -> None:
    """Form and trend analysis tab."""

    st.subheader('📈 Trend & Form Analysis')

    players = sorted(df['player'].unique().tolist()) if 'player' in df.columns else []
    if not players:
        st.warning('No players found.')
        return

    selected = st.selectbox('Select Player for Trend', players, key='trend_player')
    window = st.slider('Rolling Window (shots)', 3, 20,
                       config.get('STREAMLIT', {}).get('default_rolling_window', 5),
                       key='trend_window')

    player_df = df[df['player'] == selected]

    col1, col2 = st.columns(2)

    # Rolling conversion trend
    with col1:
        st.markdown(f'**Rolling Conversion Rate — {selected}**')
        try:
            trend_df = comparison.rolling_conversion_trend(df, selected, window=window)
            fig = viz.plot_rolling_trend(trend_df, selected, window=window)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'Trend error: {exc}')

    # Recent form
    with col2:
        st.markdown('**📋 Recent Form Summary (Last 10 shots)**')
        try:
            form = comparison.form_summary(df, selected, n_shots=10)
            form_display = {
                'Shots': form.get('shots', 0),
                'Goals': form.get('goals', 0),
                'Conversion': f"{form.get('conversion_rate', 0):.1f}%",
                'xG': f"{form.get('total_xg', 0):.2f}",
                'xG Diff': f"{form.get('xg_difference', 0):+.2f}",
                'Performance': form.get('performance_label', 'N/A'),
            }
            st.table(pd.DataFrame.from_dict(
                form_display, orient='index', columns=['Value']
            ))
        except Exception as exc:
            st.warning(f'Form summary error: {exc}')

    st.markdown('---')

    # CDF Curves
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f'**Cumulative Distance Curve — {selected}**')
        try:
            cdf = calculator.cumulative_distribution(player_df, 'distance')
            fig = viz.plot_cumulative_curve(cdf, 'distance', selected)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'CDF error: {exc}')

    with col4:
        st.markdown(f'**Cumulative Angle Curve — {selected}**')
        try:
            cdf = calculator.cumulative_distribution(player_df, 'angle')
            fig = viz.plot_cumulative_curve(cdf, 'angle', selected)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except Exception as exc:
            st.warning(f'CDF error: {exc}')

    st.markdown('---')

    # Situation / period breakdown
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(f'**Game Situation Breakdown — {selected}**')
        try:
            sit_metrics = calculator.metrics_by_segment(player_df, 'situation')
            if not sit_metrics.empty:
                st.dataframe(sit_metrics, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f'Situation error: {exc}')

    with col6:
        st.markdown(f'**Match Period Breakdown — {selected}**')
        try:
            period_metrics = calculator.metrics_by_segment(player_df, 'match_period')
            if not period_metrics.empty:
                st.dataframe(period_metrics, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f'Period error: {exc}')


# ============================================================================
# TAB 5: EXPORT & DATA
# ============================================================================

def render_tab_export(
    df: pd.DataFrame,
    config: dict,
    calculator: ShotMetricsCalculator,
    comparison: PlayerComparison,
) -> None:
    """Export and data download tab."""

    st.subheader('💾 Export & Data')

    export_cfg = config.get('EXPORT', {})
    available_cols = [c for c in export_cfg.get('export_columns', []) if c in df.columns]
    if not available_cols:
        available_cols = list(df.columns)

    st.markdown('#### 📥 Download Filtered Shot Data')
    col1, col2 = st.columns(2)
    with col1:
        selected_cols = st.multiselect(
            'Select columns to include',
            options=list(df.columns),
            default=available_cols,
            key='export_cols',
        )

    with col2:
        export_format = st.radio(
            'Export format', ['CSV', 'JSON'], horizontal=True, key='export_fmt'
        )

    if selected_cols:
        export_df = df[selected_cols].copy()
        if export_format == 'CSV':
            data_bytes = export_df.to_csv(index=False).encode('utf-8')
            mime = 'text/csv'
            filename = 'shot_analysis_export.csv'
        else:
            data_bytes = export_df.to_json(orient='records', indent=2).encode('utf-8')
            mime = 'application/json'
            filename = 'shot_analysis_export.json'

        st.download_button(
            label=f'⬇️ Download {export_format}',
            data=data_bytes,
            file_name=filename,
            mime=mime,
        )

    st.markdown('---')
    st.markdown('#### 📊 Download Player Summary Report')
    try:
        summary_df = comparison.build_comparison_table(df)
        summary_csv = summary_df.to_csv(index=True).encode('utf-8')
        st.download_button(
            label='⬇️ Download Player Summary CSV',
            data=summary_csv,
            file_name='player_summary.csv',
            mime='text/csv',
        )
        st.dataframe(summary_df, use_container_width=True)
    except Exception as exc:
        st.warning(f'Summary export error: {exc}')

    st.markdown('---')
    st.markdown('#### 🔍 Data Quality Report')
    with st.expander('Show data quality info'):
        st.write(f'**Total rows:** {len(df):,}')
        st.write(f'**Players:** {df["player"].nunique() if "player" in df.columns else "N/A"}')
        st.write(f'**Columns:** {df.shape[1]}')
        missing = df.isnull().sum()
        if missing.sum() > 0:
            st.warning('Missing values detected:')
            st.dataframe(
                missing[missing > 0].rename('Missing Count').to_frame(),
                use_container_width=True,
            )
        else:
            st.success('No missing values in the filtered dataset.')

    st.markdown('---')
    with st.expander('📋 View Raw Filtered Data'):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# SIDEBAR
# ============================================================================

def build_sidebar(df: pd.DataFrame, config: dict) -> Dict:
    """
    Build the sidebar with all filters and return filter state.

    Returns
    -------
    dict
        Filter selections.
    """
    st.sidebar.markdown('## ⚙️ Filters')

    # Player multi-select
    all_players = sorted(df['player'].unique().tolist()) if 'player' in df.columns else []
    selected_players = st.sidebar.multiselect(
        '🧑‍⚽ Players',
        all_players,
        default=all_players,
        key='sb_players',
    )

    # Season filter
    selected_seasons: List[int] = []
    if 'season' in df.columns:
        all_seasons = sorted(df['season'].dropna().astype(int).unique().tolist())
        selected_seasons = st.sidebar.multiselect(
            '📅 Season',
            all_seasons,
            default=all_seasons,
            key='sb_seasons',
        )

    # Date range
    date_range = None
    if 'date' in df.columns:
        df_dates = pd.to_datetime(df['date'], errors='coerce').dropna()
        if len(df_dates) > 0:
            min_date = df_dates.min().date()
            max_date = df_dates.max().date()
            st.sidebar.markdown('📅 Date Range')
            start_date = st.sidebar.date_input('From', min_date, key='sb_start')
            end_date = st.sidebar.date_input('To', max_date, key='sb_end')
            date_range = (start_date, end_date)

    # Result type filter
    all_results = sorted(df['result'].unique().tolist()) if 'result' in df.columns else []
    selected_results = st.sidebar.multiselect(
        '⚽ Shot Result',
        all_results,
        default=all_results,
        key='sb_results',
    )

    # Shot type filter
    all_shot_types: List[str] = []
    selected_shot_types: List[str] = []
    if 'shotType' in df.columns:
        all_shot_types = sorted(df['shotType'].dropna().unique().tolist())
        selected_shot_types = st.sidebar.multiselect(
            '🦶 Shot Type',
            all_shot_types,
            default=all_shot_types,
            key='sb_shot_types',
        )

    # Situation filter
    all_situations: List[str] = []
    selected_situations: List[str] = []
    if 'situation' in df.columns:
        all_situations = sorted(df['situation'].dropna().unique().tolist())
        selected_situations = st.sidebar.multiselect(
            '📌 Situation',
            all_situations,
            default=all_situations,
            key='sb_situations',
        )

    # Minimum xG toggle
    st.sidebar.markdown('---')
    min_xg = 0.0
    if st.sidebar.checkbox('Filter by minimum xG', key='sb_min_xg_check'):
        min_xg = st.sidebar.slider('Min xG', 0.0, 1.0, 0.05, 0.01, key='sb_min_xg')

    return {
        'players':     selected_players,
        'seasons':     selected_seasons,
        'date_range':  date_range,
        'results':     selected_results,
        'shot_types':  selected_shot_types,
        'situations':  selected_situations,
        'min_xg':      min_xg,
    }


# ============================================================================
# MAIN APP ENTRY POINT
# ============================================================================

def main() -> None:
    """Main Streamlit application."""

    # Check that modules loaded correctly
    if not MODULES_OK:
        st.error(f'Module import error: {_IMPORT_ERROR}')
        st.info('Please ensure all required modules are present.')
        return

    config = get_multi_player_config()
    st_cfg = config.get('STREAMLIT', {})

    # --- Title ---
    st.markdown('# ⚽ Multi-Player Shot Analysis Dashboard')
    st.markdown('*Powered by Understat data · mplsoccer · Plotly*')
    st.markdown('---')

    # --- Data source selection ---
    import os
    available_files = [
        f for f in ['shot_data.csv', 'erling_haaland_2022_understat.csv']
        if os.path.exists(f)
    ]

    if not available_files:
        st.error(
            'No data file found. Please upload a CSV file or place '
            "'shot_data.csv' / 'erling_haaland_2022_understat.csv' "
            'in the application directory.'
        )
        uploaded = st.file_uploader('Upload CSV', type='csv')
        if uploaded:
            tmp_path = f'/tmp/{uploaded.name}'
            with open(tmp_path, 'wb') as fh:
                fh.write(uploaded.read())
            available_files = [tmp_path]
        else:
            return

    data_source = st.selectbox(
        '📂 Data Source', available_files, key='data_source'
    ) if len(available_files) > 1 else available_files[0]

    # --- Load data ---
    try:
        df_full = load_data(data_source)
    except Exception as exc:
        st.error(f'Failed to load data: {exc}')
        return

    if df_full.empty:
        st.warning('Loaded dataset is empty.')
        return

    # --- Sidebar filters ---
    filters = build_sidebar(df_full, config)

    # --- Apply filters ---
    df = apply_filters(
        df_full,
        selected_players=filters['players'],
        selected_results=filters['results'],
        selected_shot_types=filters['shot_types'],
        selected_situations=filters['situations'],
        date_range=filters.get('date_range'),
        selected_seasons=filters.get('seasons') or None,
        min_xg=filters['min_xg'],
    )

    # Sidebar summary
    n_shots = len(df)
    n_goals = int(df['is_goal'].sum()) if 'is_goal' in df.columns else 0
    conv = f"{n_goals / n_shots * 100:.1f}%" if n_shots > 0 else '0.0%'
    st.sidebar.markdown('---')
    st.sidebar.markdown('### 📊 Filtered Summary')
    st.sidebar.markdown(f'- **Shots:** {n_shots:,}')
    st.sidebar.markdown(f'- **Goals:** {n_goals:,}')
    st.sidebar.markdown(f'- **Conversion:** {conv}')
    st.sidebar.markdown(
        f'- **Players:** {df["player"].nunique() if "player" in df.columns else 0}'
    )

    if df.empty:
        st.warning('No data matches the selected filters. Please broaden your selection.')
        return

    # --- Instantiate modules ---
    viz = ShotVisualizer(config)
    calculator = ShotMetricsCalculator(config)
    comparison = PlayerComparison(config)

    # --- Tabs ---
    tab_labels = st_cfg.get('tabs', [
        '📊 Overview & Comparison',
        '🔍 Player Deep-Dive',
        '🗺️ Zone Analysis',
        '📈 Trend Analysis',
        '💾 Export & Data',
    ])
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

    with tab1:
        render_tab_overview(df, config, viz, calculator, comparison)

    with tab2:
        render_tab_deep_dive(df, config, viz, calculator)

    with tab3:
        render_tab_zones(df, config, viz, calculator)

    with tab4:
        render_tab_trends(df, config, viz, calculator, comparison)

    with tab5:
        render_tab_export(df, config, calculator, comparison)


if __name__ == '__main__':
    main()
