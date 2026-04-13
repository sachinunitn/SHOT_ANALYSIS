"""
Advanced Shot Metrics Module
==============================

Provides shot efficiency metrics, multi-player comparison framework,
statistical confidence intervals, percentile rankings, and benchmarking.

Classes
-------
ShotMetricsCalculator
    Per-player & per-segment efficiency calculations.
PlayerComparison
    Multi-player comparison with percentile ranking and benchmarking.

Usage
-----
    from advanced_metrics import ShotMetricsCalculator, PlayerComparison
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    calculator = ShotMetricsCalculator(config)
    metrics = calculator.calculate_all_metrics(df_features)
    comparison = calculator.compare_players(df_features, ['Haaland', 'Kane'])
"""

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _wilson_confidence_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """
    Wilson score confidence interval for a proportion.

    Returns (lower, upper) as percentages (0–100).
    Handles n=0 gracefully.
    """
    if total == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = successes / total
    denominator = 1 + z ** 2 / total
    centre = (p + z ** 2 / (2 * total)) / denominator
    margin = z * np.sqrt(p * (1 - p) / total + z ** 2 / (4 * total ** 2)) / denominator
    return (
        max(0.0, (centre - margin) * 100),
        min(100.0, (centre + margin) * 100),
    )


def _percentile_rank(value: float, series: pd.Series) -> float:
    """Return the percentile rank (0–100) of value within series."""
    clean = series.dropna()
    if len(clean) == 0:
        return 50.0
    return float(stats.percentileofscore(clean, value, kind='rank'))


# ============================================================================
# SHOT METRICS CALCULATOR
# ============================================================================

class ShotMetricsCalculator:
    """
    Calculate shot efficiency metrics for individual players and segments.

    Parameters
    ----------
    config : dict
        Full configuration dictionary.
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.bench_cfg = config.get('BENCHMARKS', {})
        self.stat_cfg = config.get('STATISTICS', {})
        self.dist_cfg = config.get('DISTANCE_BINS', {})
        self.angle_cfg = config.get('ANGLE_BINS', {})
        self.conf_level = self.stat_cfg.get('confidence_level', 0.95)
        self.min_sample_ci = self.stat_cfg.get('min_sample_ci', 5)

    # ------------------------------------------------------------------ #
    # 1. OVERALL METRICS
    # ------------------------------------------------------------------ #

    def calculate_all_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate a comprehensive metrics dictionary for all players combined.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered shot data.

        Returns
        -------
        dict
            Nested dictionary with overall, distance, angle, zone metrics.
        """
        return {
            'overall':        self.overall_metrics(df),
            'by_distance':    self.metrics_by_segment(df, 'distance_bin',
                                                      self.dist_cfg.get('order', [])),
            'by_angle':       self.metrics_by_segment(df, 'angle_bin',
                                                      self.angle_cfg.get('order', [])),
            'by_shot_type':   self._metrics_by_column(df, 'shotType'),
            'by_situation':   self._metrics_by_column(df, 'situation'),
            'by_period':      self._metrics_by_column(df, 'match_period'),
            'by_zone':        self._metrics_by_column(df, 'zone_label'),
            'xg_analysis':    self.xg_analysis(df),
            'per_player':     self.per_player_metrics(df),
        }

    def overall_metrics(self, df: pd.DataFrame) -> Dict:
        """Return high-level summary metrics for a dataframe."""
        n_shots = len(df)
        n_goals = int(df['is_goal'].sum()) if 'is_goal' in df.columns else 0
        total_xg = float(df['xG'].sum()) if 'xG' in df.columns else 0.0
        conv = n_goals / n_shots * 100 if n_shots > 0 else 0.0
        ci_lo, ci_hi = _wilson_confidence_interval(n_goals, n_shots, self.conf_level)

        result = {
            'shots':           n_shots,
            'goals':           n_goals,
            'conversion_rate': round(conv, 2),
            'conversion_ci_lower': round(ci_lo, 2),
            'conversion_ci_upper': round(ci_hi, 2),
            'total_xg':        round(total_xg, 3),
            'xg_per_shot':     round(total_xg / n_shots, 4) if n_shots > 0 else 0.0,
            'xg_difference':   round(n_goals - total_xg, 3),
            'avg_distance':    round(float(df['distance'].mean()), 2) if 'distance' in df.columns else None,
            'avg_angle':       round(float(df['angle'].mean()), 2) if 'angle' in df.columns else None,
            'performance_label': self._conversion_label(conv),
        }
        return result

    def metrics_by_segment(
        self,
        df: pd.DataFrame,
        segment_col: str,
        segment_order: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Calculate shot efficiency metrics grouped by a segment column.

        Parameters
        ----------
        df : pd.DataFrame
            Shot data.
        segment_col : str
            Column to group by (e.g. 'distance_bin').
        segment_order : list of str, optional
            Ordered list of segment labels.

        Returns
        -------
        pd.DataFrame
            Metrics per segment with shots, goals, conversion %, xG, etc.
        """
        if segment_col not in df.columns:
            return pd.DataFrame()

        agg = (
            df.groupby(segment_col, observed=False)
            .agg(
                shots=('is_goal', 'count'),
                goals=('is_goal', 'sum'),
                total_xg=('xG', 'sum'),
            )
            .reset_index()
        )
        agg.columns = [segment_col, 'shots', 'goals', 'total_xg']

        agg['conversion_rate'] = (agg['goals'] / agg['shots'].replace(0, np.nan) * 100).round(1)
        agg['xg_per_shot'] = (agg['total_xg'] / agg['shots'].replace(0, np.nan)).round(4)
        agg['xg_difference'] = (agg['goals'] - agg['total_xg']).round(3)

        # Confidence intervals
        ci_lo, ci_hi = zip(
            *agg.apply(
                lambda r: _wilson_confidence_interval(
                    int(r['goals']), int(r['shots']), self.conf_level
                ),
                axis=1,
            )
        )
        agg['ci_lower'] = [round(v, 1) for v in ci_lo]
        agg['ci_upper'] = [round(v, 1) for v in ci_hi]

        # Mark small sample sizes
        min_sample = self.bench_cfg.get('minimum_shots_for_analysis', 5)
        agg['small_sample'] = agg['shots'] < min_sample

        if segment_order:
            agg[segment_col] = pd.Categorical(
                agg[segment_col], categories=segment_order, ordered=True
            )
            agg = agg.sort_values(segment_col)

        return agg.reset_index(drop=True)

    def _metrics_by_column(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Wrapper for metrics_by_segment with no fixed ordering."""
        return self.metrics_by_segment(df, col)

    # ------------------------------------------------------------------ #
    # 2. XG ANALYSIS
    # ------------------------------------------------------------------ #

    def xg_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Detailed xG vs actual goals analysis.

        Returns
        -------
        dict
            xG metrics including overperformance and category breakdown.
        """
        if 'xG' not in df.columns or 'is_goal' not in df.columns:
            return {}

        total_xg = float(df['xG'].sum())
        total_goals = int(df['is_goal'].sum())
        diff = total_goals - total_xg

        xg_bins = pd.cut(
            df['xG'],
            bins=[0, 0.05, 0.10, 0.20, 0.50, 1.01],
            labels=['<0.05', '0.05-0.10', '0.10-0.20', '0.20-0.50', '>0.50'],
            include_lowest=True,
        )
        xg_breakdown = df.groupby(xg_bins, observed=False).agg(
            shots=('is_goal', 'count'),
            goals=('is_goal', 'sum'),
            total_xg=('xG', 'sum'),
        ).reset_index()
        xg_breakdown.columns = ['xg_band', 'shots', 'goals', 'total_xg']
        xg_breakdown['expected_goals'] = xg_breakdown['total_xg'].round(2)
        xg_breakdown['over_performance'] = (
            xg_breakdown['goals'] - xg_breakdown['total_xg']
        ).round(2)

        return {
            'total_xg':         round(total_xg, 3),
            'total_goals':      total_goals,
            'xg_difference':    round(diff, 3),
            'overperformance_pct': round(diff / total_xg * 100, 1) if total_xg > 0 else 0.0,
            'xg_per_shot':      round(total_xg / len(df), 4) if len(df) > 0 else 0.0,
            'performance_label': self._xg_performance_label(diff),
            'xg_breakdown':     xg_breakdown,
        }

    # ------------------------------------------------------------------ #
    # 3. PER-PLAYER METRICS
    # ------------------------------------------------------------------ #

    def per_player_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate summary metrics for every player in the dataset.

        Returns
        -------
        pd.DataFrame
            One row per player with key statistics.
        """
        if 'player' not in df.columns:
            return pd.DataFrame()

        rows = []
        for player, grp in df.groupby('player'):
            m = self.overall_metrics(grp)
            m['player'] = player
            # Additional per-player stats
            if 'in_penalty_box' in grp.columns:
                m['penalty_box_pct'] = round(grp['in_penalty_box'].mean() * 100, 1)
            if 'shotType' in grp.columns:
                dominant = grp['shotType'].mode()
                m['dominant_foot'] = dominant.iloc[0] if len(dominant) > 0 else 'Unknown'
            rows.append(m)

        return pd.DataFrame(rows).set_index('player')

    # ------------------------------------------------------------------ #
    # 4. COMBINED DISTANCE-ANGLE PIVOT
    # ------------------------------------------------------------------ #

    def combined_heatmap_data(
        self,
        df: pd.DataFrame,
        metric: str = 'goals',
        player: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Build a pivot table of a metric by distance-bin × angle-bin.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered data.
        metric : str
            'goals', 'shots', 'conversion_rate', or 'xg'.
        player : str, optional
            Filter to a single player.

        Returns
        -------
        pd.DataFrame
            Pivot table (distance_bin rows × angle_bin columns).
        """
        if player:
            df = df[df['player'] == player]

        dist_order = self.dist_cfg.get('order', [])
        angle_order = self.angle_cfg.get('order', [])

        if metric == 'goals':
            pivot = df[df['is_goal'] == 1].pivot_table(
                index='distance_bin', columns='angle_bin',
                aggfunc='size', fill_value=0,
            )
        elif metric == 'shots':
            pivot = df.pivot_table(
                index='distance_bin', columns='angle_bin',
                aggfunc='size', fill_value=0,
            )
        elif metric == 'conversion_rate':
            goals_piv = df[df['is_goal'] == 1].pivot_table(
                index='distance_bin', columns='angle_bin',
                aggfunc='size', fill_value=0,
            )
            shots_piv = df.pivot_table(
                index='distance_bin', columns='angle_bin',
                aggfunc='size', fill_value=0,
            )
            pivot = (goals_piv / shots_piv.replace(0, np.nan) * 100).round(1).fillna(0)
        elif metric == 'xg':
            pivot = df.pivot_table(
                index='distance_bin', columns='angle_bin',
                values='xG', aggfunc='sum', fill_value=0,
            ).round(2)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        pivot = pivot.reindex(index=dist_order, columns=angle_order, fill_value=0)
        return pivot

    # ------------------------------------------------------------------ #
    # 5. CUMULATIVE DISTRIBUTION
    # ------------------------------------------------------------------ #

    def cumulative_distribution(
        self,
        df: pd.DataFrame,
        feature: str = 'distance',
        player: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Compute cumulative distribution of shots and goals over a feature.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered data.
        feature : str
            Column to compute CDF over.
        player : str, optional
            Filter to a single player.

        Returns
        -------
        pd.DataFrame
            Columns: feature, cumulative_shots, cumulative_goals,
                     cumulative_conversion.
        """
        if player:
            df = df[df['player'] == player]
        if feature not in df.columns:
            return pd.DataFrame()

        n_bins = self.stat_cfg.get('cumulative_bins', 50)
        min_val = float(df[feature].min())
        max_val = float(df[feature].max())
        thresholds = np.linspace(min_val, max_val, n_bins + 1)

        cum_shots, cum_goals = [], []
        for t in thresholds:
            sub = df[df[feature] <= t]
            cum_shots.append(len(sub))
            cum_goals.append(int(sub['is_goal'].sum()) if 'is_goal' in sub.columns else 0)

        result = pd.DataFrame({
            feature: thresholds,
            'cumulative_shots': cum_shots,
            'cumulative_goals': cum_goals,
        })
        result['cumulative_conversion'] = (
            result['cumulative_goals'] / result['cumulative_shots'].replace(0, np.nan) * 100
        ).fillna(0).round(1)
        return result

    # ------------------------------------------------------------------ #
    # 6. LABEL HELPERS
    # ------------------------------------------------------------------ #

    def _conversion_label(self, rate: float) -> str:
        """Return a performance label for a conversion rate."""
        benchmarks = self.bench_cfg.get('conversion_rate', {})
        for level, bounds in benchmarks.items():
            if bounds.get('min', 0) <= rate < bounds.get('max', 100):
                return benchmarks[level].get('label', level.title())
        return 'Unknown'

    def _xg_performance_label(self, diff: float) -> str:
        """Return a performance label based on goals - xG difference."""
        for level, bounds in self.bench_cfg.get('xg_performance', {}).items():
            lo = bounds.get('min', float('-inf'))
            hi = bounds.get('max', float('inf'))
            if lo <= diff < hi:
                return bounds.get('label', level.title())
        return 'Unknown'


# ============================================================================
# PLAYER COMPARISON
# ============================================================================

class PlayerComparison:
    """
    Multi-player comparison framework.

    Parameters
    ----------
    config : dict
        Full configuration dictionary.
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.calculator = ShotMetricsCalculator(config)
        self.bench_cfg = config.get('BENCHMARKS', {})
        self.stat_cfg = config.get('STATISTICS', {})
        self.radar_cfg = config.get('RADAR', {})

    # ------------------------------------------------------------------ #
    # 1. COMPARISON TABLE
    # ------------------------------------------------------------------ #

    def build_comparison_table(
        self,
        df: pd.DataFrame,
        players: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Build a side-by-side comparison table for multiple players.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered shot data.
        players : list of str, optional
            Player names to include.  If None, includes all players.

        Returns
        -------
        pd.DataFrame
            Comparison table with key metrics per player.
        """
        if players:
            df = df[df['player'].isin(players)]

        per_player = self.calculator.per_player_metrics(df)
        if per_player.empty:
            return per_player

        # Add percentile ranks within this cohort
        numeric_cols = [
            'conversion_rate', 'total_xg', 'xg_per_shot', 'shots',
        ]
        for col in numeric_cols:
            if col in per_player.columns:
                per_player[f'{col}_pct'] = per_player[col].apply(
                    lambda v: round(_percentile_rank(v, per_player[col]), 1)
                )

        # Add benchmark label
        if 'conversion_rate' in per_player.columns:
            per_player['benchmark'] = per_player['conversion_rate'].apply(
                self.calculator._conversion_label
            )

        return per_player.sort_values('goals', ascending=False)

    # ------------------------------------------------------------------ #
    # 2. RADAR DATA
    # ------------------------------------------------------------------ #

    def radar_data(
        self,
        df: pd.DataFrame,
        players: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Build normalised radar chart data (0–1 scale) for each player.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered shot data.
        players : list of str, optional
            Players to include.

        Returns
        -------
        dict
            {player_name: {metric_key: normalised_value, …}}
        """
        if players:
            df = df[df['player'].isin(players)]

        metrics_def = self.radar_cfg.get('metrics', [])
        per_player_df = self.calculator.per_player_metrics(df)

        result: Dict[str, Dict[str, float]] = {}
        for player in per_player_df.index:
            player_data: Dict[str, float] = {}
            player_grp = df[df['player'] == player]
            m = self.calculator.overall_metrics(player_grp)

            for metric_def in metrics_def:
                key = metric_def['key']
                scale = metric_def.get('scale', (0, 1))
                raw_val = self._extract_metric(m, player_grp, key)
                # Normalise to 0–1
                lo, hi = scale
                span = hi - lo
                norm = (raw_val - lo) / span if span > 0 else 0.0
                player_data[key] = float(np.clip(norm, 0.0, 1.0))
            result[player] = player_data

        return result

    def _extract_metric(self, overall: Dict, df_player: pd.DataFrame, key: str) -> float:
        """Extract a raw metric value given its key."""
        if key == 'conversion_rate':
            return overall.get('conversion_rate', 0.0)
        elif key == 'xg_per_shot':
            return overall.get('xg_per_shot', 0.0)
        elif key == 'xg_overperformance':
            return overall.get('xg_difference', 0.0)
        elif key == 'penalty_box_pct':
            if 'in_penalty_box' in df_player.columns and len(df_player) > 0:
                return float(df_player['in_penalty_box'].mean() * 100)
            return 0.0
        elif key == 'avg_shot_quality':
            return float(df_player['xG'].mean()) if 'xG' in df_player.columns else 0.0
        elif key == 'shot_volume':
            return float(len(df_player))
        return 0.0

    # ------------------------------------------------------------------ #
    # 3. BENCHMARKING
    # ------------------------------------------------------------------ #

    def benchmark_players(
        self,
        df: pd.DataFrame,
        players: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Assign benchmark tier (Elite / Good / Average / Below Average)
        and percentile to each player.

        Returns
        -------
        pd.DataFrame
            Player × benchmark metrics.
        """
        table = self.build_comparison_table(df, players)
        if table.empty:
            return table

        min_shots = self.bench_cfg.get('minimum_shots_for_percentile', 20)
        eligible = table[table['shots'] >= min_shots].copy()

        if eligible.empty:
            eligible = table.copy()

        # Overall percentile score (average of ranked metrics)
        rank_cols = [c for c in eligible.columns if c.endswith('_pct')]
        if rank_cols:
            eligible['overall_percentile'] = eligible[rank_cols].mean(axis=1).round(1)

        return eligible.sort_values('overall_percentile', ascending=False)

    # ------------------------------------------------------------------ #
    # 4. TREND ANALYSIS
    # ------------------------------------------------------------------ #

    def rolling_conversion_trend(
        self,
        df: pd.DataFrame,
        player: str,
        window: int = 5,
    ) -> pd.DataFrame:
        """
        Calculate rolling conversion rate for a player (shot-by-shot order).

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered data.
        player : str
            Player name.
        window : int
            Rolling window size (shots).

        Returns
        -------
        pd.DataFrame
            Columns: date (or index), conversion_rate (rolling).
        """
        player_df = df[df['player'] == player].copy()
        if 'date' in player_df.columns:
            player_df = player_df.sort_values('date')

        player_df = player_df.reset_index(drop=True)
        player_df['rolling_conversion'] = (
            player_df['is_goal']
            .rolling(window, min_periods=1)
            .mean() * 100
        ).round(1)

        cols = ['rolling_conversion']
        if 'date' in player_df.columns:
            cols = ['date'] + cols
        return player_df[cols]

    def form_summary(self, df: pd.DataFrame, player: str, n_shots: int = 10) -> Dict:
        """
        Return recent form summary (last n_shots) for a player.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered data.
        player : str
            Player name.
        n_shots : int
            How many recent shots to use.

        Returns
        -------
        dict
            Recent performance metrics.
        """
        player_df = df[df['player'] == player].copy()
        if 'date' in player_df.columns:
            player_df = player_df.sort_values('date', ascending=False)
        recent = player_df.head(n_shots)
        return self.calculator.overall_metrics(recent)


# ============================================================================
# MODULE SELF-TEST
# ============================================================================

if __name__ == '__main__':
    import os
    from data_processor import MultiPlayerDataProcessor
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    processor = MultiPlayerDataProcessor(config)
    calculator = ShotMetricsCalculator(config)
    comparison = PlayerComparison(config)

    for fname in ['shot_data.csv', 'erling_haaland_2022_understat.csv']:
        if os.path.exists(fname):
            df_raw = processor.load_from_csv(fname)
            df_clean = processor.preprocess(df_raw)
            df_feat = processor.add_features(df_clean)

            metrics = calculator.calculate_all_metrics(df_feat)
            print(f"✅ Overall metrics: {metrics['overall']}")

            table = comparison.build_comparison_table(df_feat)
            print(f"✅ Comparison table ({len(table)} players):")
            print(table[['shots', 'goals', 'conversion_rate']].head())
            break
