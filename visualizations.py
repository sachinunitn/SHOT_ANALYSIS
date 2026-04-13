"""
Shot Visualizations Module
============================

Publication-quality interactive visualizations for multi-player shot analysis.
Uses Matplotlib/mplsoccer for pitch-based plots and Plotly for interactive charts.

Classes
-------
ShotVisualizer
    Main visualizer with heatmaps, pitch maps, radar charts, comparisons,
    scatter plots, histograms, and trend curves.

Usage
-----
    from visualizations import ShotVisualizer
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    viz = ShotVisualizer(config)
    fig = viz.plot_pitch_map(df, player='Erling Haaland')
    fig = viz.plot_distance_angle_heatmap(df, metric='conversion_rate')
    fig = viz.plot_radar_comparison(radar_dict)
"""

import warnings
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib.colors import Normalize, ListedColormap
from mplsoccer import Pitch, VerticalPitch

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

warnings.filterwarnings('ignore')


# ============================================================================
# COLOUR HELPERS
# ============================================================================

def _player_color(index: int, palette: Optional[List[str]] = None) -> str:
    """Return a colour for the player at the given index."""
    default = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf',
    ]
    palette = palette or default
    return palette[index % len(palette)]


# ============================================================================
# MAIN VISUALIZER CLASS
# ============================================================================

class ShotVisualizer:
    """
    Multi-player shot analysis visualizer.

    Parameters
    ----------
    config : dict
        Full configuration dictionary (from ``get_multi_player_config()``).
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.viz_cfg = config.get('VISUALIZATION', {})
        self.color_cfg = config.get('COLORS', {})
        self.dist_cfg = config.get('DISTANCE_BINS', {})
        self.angle_cfg = config.get('ANGLE_BINS', {})
        self.player_colors = self.color_cfg.get('players', [])
        self.result_colors = self.color_cfg.get('shot_results', {
            'Goal':        '#FF4444',
            'MissedShots': '#FFFF44',
            'SavedShot':   '#FF9944',
            'BlockedShot': '#CCCCCC',
        })

    # ------------------------------------------------------------------ #
    # 1. PITCH MAP (mplsoccer)
    # ------------------------------------------------------------------ #

    def plot_pitch_map(
        self,
        df: pd.DataFrame,
        player: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot shot locations on a football pitch.

        Parameters
        ----------
        df : pd.DataFrame
            Shot data with X, Y, result columns.
        player : str, optional
            If given, filter to this player only.
        title : str, optional
            Chart title. Auto-generated if None.
        figsize : tuple, optional
            Figure dimensions.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if player:
            df = df[df['player'] == player]

        fs = figsize or self.viz_cfg.get('pitch', {}).get('figsize', (12, 8))
        fig, ax = plt.subplots(figsize=fs)

        pitch = Pitch(
            pitch_type='uefa',
            pitch_color=self.color_cfg.get('pitch', {}).get('surface', '#22844e'),
            line_color=self.color_cfg.get('pitch', {}).get('lines', 'white'),
            linewidth=1.5,
        )
        pitch.draw(ax=ax)

        pcfg = self.viz_cfg.get('pitch', {})
        shot_size = pcfg.get('shot_marker_size', 100)
        goal_size = pcfg.get('goal_marker_size', 150)
        shot_alpha = pcfg.get('shot_alpha', 0.6)
        goal_alpha = pcfg.get('goal_alpha', 0.9)

        result_groups = {
            'BlockedShot': ('gray',   'Blocked', shot_size, shot_alpha, 'o'),
            'SavedShot':   ('orange', 'Saved',   shot_size, shot_alpha, 'o'),
            'MissedShots': ('yellow', 'Missed',  shot_size, shot_alpha, 'o'),
            'Goal':        ('red',    'Goal',    goal_size, goal_alpha, '*'),
        }

        for result, (color, label, size, alpha, marker) in result_groups.items():
            sub = df[df['result'] == result]
            if len(sub) > 0:
                pitch.scatter(
                    sub['X'] * 105, sub['Y'] * 68,
                    s=size, alpha=alpha, color=color,
                    edgecolors='black', linewidth=0.5,
                    label=label, ax=ax, marker=marker,
                )

        ax.legend(loc='upper left', framealpha=0.9, fontsize=9)
        if title is None:
            title = f"Shot Map — {player}" if player else "Shot Map (All Players)"
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 2. PITCH HEATMAP (kernel density)
    # ------------------------------------------------------------------ #

    def plot_pitch_heatmap(
        self,
        df: pd.DataFrame,
        player: Optional[str] = None,
        show_goals_only: bool = False,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot a KDE heatmap of shot density on the pitch.

        Parameters
        ----------
        df : pd.DataFrame
            Shot data.
        player : str, optional
            Filter to one player.
        show_goals_only : bool
            If True, show only goals.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if player:
            df = df[df['player'] == player]
        if show_goals_only:
            df = df[df['result'] == 'Goal']

        fs = figsize or self.viz_cfg.get('pitch', {}).get('figsize', (12, 8))
        fig, ax = plt.subplots(figsize=fs)

        pitch = Pitch(
            pitch_type='uefa',
            pitch_color=self.color_cfg.get('pitch', {}).get('surface', '#22844e'),
            line_color=self.color_cfg.get('pitch', {}).get('lines', 'white'),
            linewidth=1.5,
        )
        pitch.draw(ax=ax)

        if len(df) > 0:
            pitch.kdeplot(
                df['X'] * 105, df['Y'] * 68,
                ax=ax,
                fill=True,
                cmap='hot',
                alpha=0.6,
                levels=10,
                thresh=0.05,
            )

        suffix = ' (Goals Only)' if show_goals_only else ''
        name = f" — {player}" if player else " (All Players)"
        ax.set_title(f"Shot Density Heatmap{name}{suffix}",
                     fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 3. DISTANCE-ANGLE COMBINED HEATMAP
    # ------------------------------------------------------------------ #

    def plot_distance_angle_heatmap(
        self,
        pivot_data: pd.DataFrame,
        metric: str = 'goals',
        title: Optional[str] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot a 2-D heatmap of distance-bin × angle-bin.

        Parameters
        ----------
        pivot_data : pd.DataFrame
            Pivot table (distance_bin rows × angle_bin columns).
            Produced by ``ShotMetricsCalculator.combined_heatmap_data``.
        metric : str
            Label for colour bar (e.g. 'goals', 'conversion_rate', 'xG').
        title : str, optional
            Chart title.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        cmap_key = 'goals' if metric == 'goals' else 'conversion'
        cmap = self.color_cfg.get('heatmaps', {}).get(cmap_key, 'YlOrRd')

        fs = figsize or self.viz_cfg.get('heatmap', {}).get('figsize', (14, 8))
        fig, ax = plt.subplots(figsize=fs)

        data = pivot_data.values.astype(float)
        im = ax.imshow(data, cmap=cmap, aspect='auto')

        ax.set_xticks(range(len(pivot_data.columns)))
        ax.set_yticks(range(len(pivot_data.index)))
        ax.set_xticklabels(pivot_data.columns, rotation=45, ha='right')
        ax.set_yticklabels(pivot_data.index)
        ax.set_xlabel('Angle', fontweight='bold')
        ax.set_ylabel('Distance', fontweight='bold')

        fmt = '.1f' if metric == 'conversion_rate' else ('d' if data.max() >= 1 else '.2f')
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                text = f"{val:{fmt}}" if fmt != 'd' else str(int(val))
                ax.text(j, i, text, ha='center', va='center',
                        color='black', fontweight='bold', fontsize=9)

        unit = '%' if metric == 'conversion_rate' else ''
        plt.colorbar(im, ax=ax, label=f'{metric.replace("_", " ").title()} {unit}')

        if title is None:
            title = f'{metric.replace("_", " ").title()} by Distance & Angle'
        ax.set_title(title, fontsize=13, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 4. 1-D METRIC BAR CHARTS
    # ------------------------------------------------------------------ #

    def plot_metric_bars(
        self,
        segment_df: pd.DataFrame,
        segment_col: str,
        metric: str = 'conversion_rate',
        title: Optional[str] = None,
        figsize: Optional[Tuple] = None,
        color: str = '#1f77b4',
    ) -> plt.Figure:
        """
        Plot a horizontal bar chart for a metric by segment.

        Parameters
        ----------
        segment_df : pd.DataFrame
            Output of ``ShotMetricsCalculator.metrics_by_segment``.
        segment_col : str
            Column used as Y-axis labels.
        metric : str
            Column to plot on X-axis.
        title : str, optional
            Chart title.
        figsize : tuple, optional
            Figure size.
        color : str
            Bar colour.

        Returns
        -------
        matplotlib.figure.Figure
        """
        fs = figsize or (10, 5)
        fig, ax = plt.subplots(figsize=fs)

        sub = segment_df.dropna(subset=[metric]).copy()
        bars = ax.barh(sub[segment_col].astype(str), sub[metric], color=color, alpha=0.8)

        # Add CI whiskers if available
        if 'ci_lower' in sub.columns and metric == 'conversion_rate':
            xerr_lo = (sub['conversion_rate'] - sub['ci_lower']).clip(lower=0)
            xerr_hi = (sub['ci_upper'] - sub['conversion_rate']).clip(lower=0)
            ax.errorbar(
                sub['conversion_rate'], sub[segment_col].astype(str),
                xerr=[xerr_lo, xerr_hi],
                fmt='none', color='black', capsize=4, linewidth=1.5,
            )

        # Annotate bars
        for bar, val in zip(bars, sub[metric]):
            unit = '%' if 'rate' in metric else ''
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f'{val:.1f}{unit}', va='center', ha='left', fontsize=9)

        ax.set_xlabel(metric.replace('_', ' ').title())
        ax.set_title(title or metric.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 5. MULTI-PLAYER COMPARISON BARS
    # ------------------------------------------------------------------ #

    def plot_player_comparison_bars(
        self,
        comparison_df: pd.DataFrame,
        metric: str = 'conversion_rate',
        title: Optional[str] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Side-by-side bar chart comparing multiple players on a metric.

        Parameters
        ----------
        comparison_df : pd.DataFrame
            Output of ``PlayerComparison.build_comparison_table``.
        metric : str
            Metric column to plot.
        title : str, optional
            Chart title.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if metric not in comparison_df.columns:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, f"Metric '{metric}' not found",
                    ha='center', va='center', transform=ax.transAxes)
            return fig

        fs = figsize or self.viz_cfg.get('comparison', {}).get('figsize', (14, 6))
        sub = comparison_df[[metric]].dropna().sort_values(metric, ascending=False)
        colors = [_player_color(i, self.player_colors) for i in range(len(sub))]

        fig, ax = plt.subplots(figsize=fs)
        bars = ax.bar(sub.index.astype(str), sub[metric], color=colors, alpha=0.85)

        for bar, val in zip(bars, sub[metric]):
            unit = '%' if 'rate' in metric else ''
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                    f'{val:.1f}{unit}', ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(title or f'{metric.replace("_", " ").title()} by Player',
                     fontsize=13, fontweight='bold')
        plt.xticks(rotation=20, ha='right')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 6. RADAR CHART
    # ------------------------------------------------------------------ #

    def plot_radar_comparison(
        self,
        radar_dict: Dict[str, Dict[str, float]],
        metric_labels: Optional[List[str]] = None,
        title: str = 'Player Shooting Profile Comparison',
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot a radar (spider) chart comparing players across metrics.

        Parameters
        ----------
        radar_dict : dict
            {player: {metric_key: normalised_0_to_1_value, …}}
        metric_labels : list of str, optional
            Human-readable metric labels (same order as keys).
        title : str
            Chart title.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if not radar_dict:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data for radar chart',
                    ha='center', va='center', transform=ax.transAxes)
            return fig

        players = list(radar_dict.keys())
        first = radar_dict[players[0]]
        metric_keys = list(first.keys())
        n = len(metric_keys)

        if metric_labels is None:
            radar_metrics = self.config.get('RADAR', {}).get('metrics', [])
            key_to_label = {m['key']: m['label'] for m in radar_metrics}
            metric_labels = [key_to_label.get(k, k.replace('_', ' ').title())
                             for k in metric_keys]

        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        angles += angles[:1]  # close the polygon

        fs = figsize or self.viz_cfg.get('radar', {}).get('figsize', (10, 10))
        fig, ax = plt.subplots(figsize=fs, subplot_kw={'polar': True})

        for idx, player in enumerate(players):
            values = [radar_dict[player].get(k, 0) for k in metric_keys]
            values += values[:1]
            color = _player_color(idx, self.player_colors)
            ax.plot(angles, values, 'o-', linewidth=2, color=color, label=player)
            ax.fill(angles, values, alpha=0.1, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7, color='gray')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.set_title(title, fontsize=13, fontweight='bold', y=1.08)
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 7. SCATTER PLOT (distance vs angle)
    # ------------------------------------------------------------------ #

    def plot_scatter_distance_angle(
        self,
        df: pd.DataFrame,
        color_by: str = 'result',
        player: Optional[str] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Scatter plot of distance vs angle, coloured by result or xG.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered shot data.
        color_by : str
            'result' or 'xG'.
        player : str, optional
            Filter to one player.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if player:
            df = df[df['player'] == player]

        fs = figsize or self.viz_cfg.get('scatter', {}).get('figsize', (12, 8))
        fig, ax = plt.subplots(figsize=fs)

        if color_by == 'xG' and 'xG' in df.columns:
            scatter = ax.scatter(
                df['distance'], df['angle'],
                c=df['xG'], cmap='RdYlGn', alpha=0.6, s=70,
                edgecolors='black', linewidth=0.3,
            )
            plt.colorbar(scatter, ax=ax, label='xG')
        else:
            # Colour by result
            for result, color in self.result_colors.items():
                sub = df[df['result'] == result]
                if len(sub):
                    ax.scatter(sub['distance'], sub['angle'],
                               c=color, alpha=0.6, s=70, label=result,
                               edgecolors='black', linewidth=0.3)
            ax.legend(fontsize=9)

        ax.set_xlabel('Distance (m)', fontsize=11)
        ax.set_ylabel('Angle (°)', fontsize=11)
        title = f'Distance vs Angle — {player}' if player else 'Distance vs Angle'
        ax.set_title(title, fontsize=13, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 8. DISTRIBUTION HISTOGRAMS
    # ------------------------------------------------------------------ #

    def plot_distribution(
        self,
        df: pd.DataFrame,
        feature: str = 'distance',
        players: Optional[List[str]] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Overlaid distribution histograms for one or more players.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered data.
        feature : str
            'distance' or 'angle'.
        players : list of str, optional
            Players to include.  If None, includes all.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if players:
            df = df[df['player'].isin(players)]
        else:
            players = sorted(df['player'].unique().tolist())

        fs = figsize or self.viz_cfg.get('histogram', {}).get('figsize', (12, 6))
        fig, ax = plt.subplots(figsize=fs)

        bins = self.viz_cfg.get('histogram', {}).get('bins', 20)
        alpha = self.viz_cfg.get('histogram', {}).get('alpha', 0.5)

        for idx, player in enumerate(players):
            data = df[df['player'] == player][feature].dropna()
            color = _player_color(idx, self.player_colors)
            ax.hist(data, bins=bins, alpha=alpha, color=color, label=player, density=True)

        unit = 'm' if feature == 'distance' else '°'
        ax.set_xlabel(f'{feature.title()} ({unit})', fontsize=11)
        ax.set_ylabel('Density', fontsize=11)
        ax.set_title(f'{feature.title()} Distribution', fontsize=13, fontweight='bold')
        if players:
            ax.legend(fontsize=9)
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 9. CUMULATIVE GOAL CURVES
    # ------------------------------------------------------------------ #

    def plot_cumulative_curve(
        self,
        cdf_df: pd.DataFrame,
        feature: str = 'distance',
        player: Optional[str] = None,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot cumulative shots and goals up to each distance/angle value.

        Parameters
        ----------
        cdf_df : pd.DataFrame
            Output of ``ShotMetricsCalculator.cumulative_distribution``.
        feature : str
            Feature name (x-axis label).
        player : str, optional
            Player name (for title).
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        fs = figsize or (12, 6)
        fig, ax1 = plt.subplots(figsize=fs)
        ax2 = ax1.twinx()

        unit = 'm' if feature == 'distance' else '°'
        ax1.plot(cdf_df[feature], cdf_df['cumulative_shots'],
                 color='#1f77b4', label='Cumulative Shots', linewidth=2)
        ax1.plot(cdf_df[feature], cdf_df['cumulative_goals'],
                 color='#d62728', label='Cumulative Goals', linewidth=2, linestyle='--')
        ax2.plot(cdf_df[feature], cdf_df['cumulative_conversion'],
                 color='#2ca02c', label='Conversion %', linewidth=1.5, linestyle=':')

        ax1.set_xlabel(f'{feature.title()} ({unit})', fontsize=11)
        ax1.set_ylabel('Cumulative Count', fontsize=11)
        ax2.set_ylabel('Conversion Rate (%)', fontsize=11, color='#2ca02c')
        ax2.tick_params(axis='y', labelcolor='#2ca02c')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)

        title = f'Cumulative {feature.title()} Analysis'
        if player:
            title += f' — {player}'
        ax1.set_title(title, fontsize=13, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 10. ROLLING TREND CHART
    # ------------------------------------------------------------------ #

    def plot_rolling_trend(
        self,
        trend_df: pd.DataFrame,
        player: str,
        window: int = 5,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        Plot rolling conversion rate trend for a player.

        Parameters
        ----------
        trend_df : pd.DataFrame
            Output of ``PlayerComparison.rolling_conversion_trend``.
        player : str
            Player name (used in title).
        window : int
            Window size used.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        fs = figsize or self.viz_cfg.get('trend', {}).get('figsize', (14, 6))
        fig, ax = plt.subplots(figsize=fs)

        x = trend_df.get('date', pd.RangeIndex(len(trend_df)))
        ax.plot(x, trend_df['rolling_conversion'],
                color='#1f77b4', linewidth=2, label=f'{window}-shot rolling avg')
        ax.axhline(y=trend_df['rolling_conversion'].mean(), color='red',
                   linestyle='--', linewidth=1, alpha=0.7, label='Season average')
        ax.fill_between(x, trend_df['rolling_conversion'],
                        trend_df['rolling_conversion'].mean(),
                        alpha=0.1, color='#1f77b4')

        ax.set_ylabel('Conversion Rate (%)', fontsize=11)
        ax.set_title(f'Form Trend — {player} ({window}-shot rolling window)',
                     fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        plt.xticks(rotation=30, ha='right')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 11. CONVERSION RATE BY DISTANCE HEATMAP (1-D)
    # ------------------------------------------------------------------ #

    def plot_conversion_by_distance(
        self,
        segment_df: pd.DataFrame,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        1-D heatmap showing conversion rate per distance bin.

        Parameters
        ----------
        segment_df : pd.DataFrame
            Output of ``ShotMetricsCalculator.metrics_by_segment``
            with segment_col='distance_bin'.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        fs = figsize or (10, 4)
        fig, ax = plt.subplots(figsize=fs)

        data = segment_df.set_index(segment_df.columns[0])['conversion_rate'].fillna(0)
        im = ax.imshow(data.values.reshape(1, -1),
                       cmap='RdYlGn', aspect='auto', vmin=0, vmax=50)
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data.index, rotation=0)
        ax.set_yticks([0])
        ax.set_yticklabels(['Conv %'])
        for i, (label, val) in enumerate(data.items()):
            ax.text(i, 0, f'{val:.1f}%', ha='center', va='center',
                    color='black', fontweight='bold')
        plt.colorbar(im, ax=ax, label='Conversion Rate (%)')
        ax.set_title('Conversion Rate by Distance', fontsize=12, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 12. CONVERSION RATE BY ANGLE HEATMAP (1-D)
    # ------------------------------------------------------------------ #

    def plot_conversion_by_angle(
        self,
        segment_df: pd.DataFrame,
        figsize: Optional[Tuple] = None,
    ) -> plt.Figure:
        """
        1-D heatmap showing conversion rate per angle bin.

        Parameters
        ----------
        segment_df : pd.DataFrame
            Output of ``ShotMetricsCalculator.metrics_by_segment``
            with segment_col='angle_bin'.
        figsize : tuple, optional
            Figure size.

        Returns
        -------
        matplotlib.figure.Figure
        """
        fs = figsize or (12, 4)
        fig, ax = plt.subplots(figsize=fs)

        data = segment_df.set_index(segment_df.columns[0])['conversion_rate'].fillna(0)
        im = ax.imshow(data.values.reshape(1, -1),
                       cmap='RdYlGn', aspect='auto', vmin=0, vmax=50)
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data.index, rotation=0)
        ax.set_yticks([0])
        ax.set_yticklabels(['Conv %'])
        for i, (label, val) in enumerate(data.items()):
            ax.text(i, 0, f'{val:.1f}%', ha='center', va='center',
                    color='black', fontweight='bold')
        plt.colorbar(im, ax=ax, label='Conversion Rate (%)')
        ax.set_title('Conversion Rate by Angle', fontsize=12, fontweight='bold')
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------ #
    # 13. PLOTLY INTERACTIVE HEATMAP
    # ------------------------------------------------------------------ #

    def plot_interactive_heatmap(
        self,
        pivot_data: pd.DataFrame,
        metric: str = 'goals',
        title: Optional[str] = None,
    ):
        """
        Interactive Plotly heatmap of distance × angle.

        Parameters
        ----------
        pivot_data : pd.DataFrame
            Pivot table from ``ShotMetricsCalculator.combined_heatmap_data``.
        metric : str
            Metric label.
        title : str, optional
            Chart title.

        Returns
        -------
        plotly.graph_objects.Figure or None
            None if Plotly is not installed.
        """
        if not PLOTLY_AVAILABLE:
            return None

        color_scale = 'YlOrRd' if metric == 'goals' else 'RdYlGn'
        title = title or f'{metric.replace("_", " ").title()} by Distance & Angle'

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_data.values.tolist(),
                x=list(pivot_data.columns.astype(str)),
                y=list(pivot_data.index.astype(str)),
                colorscale=color_scale,
                text=pivot_data.values.tolist(),
                texttemplate='%{text:.1f}' if metric != 'goals' else '%{text}',
                showscale=True,
                colorbar={'title': metric.replace('_', ' ').title()},
            )
        )
        fig.update_layout(
            title=title,
            xaxis_title='Angle',
            yaxis_title='Distance',
            height=450,
        )
        return fig

    # ------------------------------------------------------------------ #
    # 14. PLOTLY SCATTER
    # ------------------------------------------------------------------ #

    def plot_interactive_scatter(
        self,
        df: pd.DataFrame,
        color_by: str = 'result',
        player: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """
        Interactive Plotly scatter plot of distance vs angle.

        Returns
        -------
        plotly.graph_objects.Figure or None
        """
        if not PLOTLY_AVAILABLE:
            return None

        if player:
            df = df[df['player'] == player]

        color_col = color_by if color_by in df.columns else 'result'
        hover_data = [c for c in ['xG', 'shotType', 'situation', 'player', 'date']
                      if c in df.columns]
        title = title or (
            f'Distance vs Angle — {player}' if player else 'Distance vs Angle'
        )

        fig = px.scatter(
            df,
            x='distance',
            y='angle',
            color=color_col,
            hover_data=hover_data,
            title=title,
            labels={'distance': 'Distance (m)', 'angle': 'Angle (°)'},
            opacity=0.65,
            height=500,
        )
        fig.update_traces(marker={'size': 8, 'line': {'width': 0.5, 'color': 'black'}})
        return fig


# ============================================================================
# MODULE SELF-TEST
# ============================================================================

if __name__ == '__main__':
    import os
    from data_processor import MultiPlayerDataProcessor
    from advanced_metrics import ShotMetricsCalculator, PlayerComparison
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    processor = MultiPlayerDataProcessor(config)
    calculator = ShotMetricsCalculator(config)
    viz = ShotVisualizer(config)

    for fname in ['shot_data.csv', 'erling_haaland_2022_understat.csv']:
        if os.path.exists(fname):
            df_raw = processor.load_from_csv(fname)
            df_clean = processor.preprocess(df_raw)
            df_feat = processor.add_features(df_clean)

            fig = viz.plot_pitch_map(df_feat)
            print("✅ Pitch map created")
            plt.close(fig)

            pivot = calculator.combined_heatmap_data(df_feat, metric='goals')
            fig = viz.plot_distance_angle_heatmap(pivot, metric='goals')
            print("✅ Heatmap created")
            plt.close(fig)
            break
