"""
Multi-Player Data Processor
============================

Handles loading, validation, cleaning, and feature engineering for
multi-player Understat shot data.

Classes
-------
MultiPlayerDataProcessor
    Main processor: load → validate → clean → engineer features.

Usage
-----
    from data_processor import MultiPlayerDataProcessor
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    processor = MultiPlayerDataProcessor(config)
    df = processor.load_from_csv('multi_player_data.csv')
    df_clean = processor.preprocess(df)
    df_features = processor.add_features(df_clean)
    report = processor.data_quality_report(df_features)
"""

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_distance(
    x: float,
    y: float,
    goal_x: float = 1.0,
    goal_y: float = 0.5,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
) -> float:
    """
    Calculate Euclidean distance from shot location to goal centre in metres.

    Parameters
    ----------
    x, y : float
        Normalised Understat coordinates (0–1).
    goal_x, goal_y : float
        Goal-centre normalised coordinates.
    pitch_length, pitch_width : float
        Pitch dimensions in metres.

    Returns
    -------
    float
        Distance in metres.
    """
    x_m = x * pitch_length
    y_m = y * pitch_width
    gx_m = goal_x * pitch_length
    gy_m = goal_y * pitch_width
    return float(np.sqrt((x_m - gx_m) ** 2 + (y_m - gy_m) ** 2))


def _calculate_angle(
    x: float,
    y: float,
    goal_y: float = 0.5,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
) -> float:
    """
    Calculate shot angle relative to goal centre (degrees, 0–90).

    The angle is measured from the perpendicular through the goal centre to
    the line connecting the shot location to the goal centre.

    Parameters
    ----------
    x, y : float
        Normalised coordinates.
    goal_y : float
        Goal-centre normalised Y.
    pitch_length, pitch_width : float
        Pitch dimensions in metres.

    Returns
    -------
    float
        Angle in degrees.
    """
    x_m = x * pitch_length
    y_m = y * pitch_width
    gy_m = goal_y * pitch_width
    dist_to_goal_line = (1.0 - x) * pitch_length
    angle_rad = np.arctan(np.abs(y_m - gy_m) / (dist_to_goal_line + 1e-6))
    return float(np.degrees(angle_rad))


def _bin_distance(distance: float, bins: List[Dict]) -> str:
    """Map a distance value to the correct bin label."""
    for b in bins:
        lo, hi = b['range']
        if lo <= distance < hi:
            return b['label']
    return bins[-1]['label']


def _bin_angle(angle: float, bins: List[Dict]) -> str:
    """Map an angle value to the correct bin label."""
    for b in bins:
        lo, hi = b['range']
        if lo <= angle < hi:
            return b['label']
    return bins[-1]['label']


def _standardize_name(name: str) -> str:
    """Strip whitespace and title-case a name string."""
    if not isinstance(name, str):
        return str(name)
    return ' '.join(name.strip().split())


# ============================================================================
# MAIN CLASS
# ============================================================================

class MultiPlayerDataProcessor:
    """
    Intelligent data processor for multi-player Understat shot data.

    Pipeline
    --------
    load_from_csv → preprocess → add_features → data_quality_report

    Parameters
    ----------
    config : dict
        Full configuration dictionary (from ``get_multi_player_config()``).
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.data_cfg = config.get('DATA', {})
        self.dist_cfg = config.get('DISTANCE_BINS', {})
        self.angle_cfg = config.get('ANGLE_BINS', {})
        self.zone_cfg = config.get('ZONES', {})
        self.val_cfg = config.get('VALIDATION', {})
        self.feat_cfg = config.get('FEATURES', {})
        self.adv_cfg = config.get('ADVANCED', {})
        self._quality_log: List[str] = []

    # ------------------------------------------------------------------ #
    # 1. LOADING
    # ------------------------------------------------------------------ #

    def load_from_csv(self, filepath: str, sep: Optional[str] = None) -> pd.DataFrame:
        """
        Load shot data from a CSV file, auto-detecting the delimiter.

        Parameters
        ----------
        filepath : str
            Path to the CSV file.
        sep : str, optional
            Delimiter. Auto-detected if None.

        Returns
        -------
        pd.DataFrame
            Raw loaded dataframe.

        Raises
        ------
        FileNotFoundError
            If the file cannot be found.
        ValueError
            If the CSV has fewer than 2 columns after loading.
        """
        if sep is None:
            # Sniff delimiter from first line
            with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                first_line = fh.readline()
            sep = ';' if first_line.count(';') > first_line.count(',') else ','

        df = pd.read_csv(filepath, sep=sep, low_memory=False)
        df.columns = df.columns.str.strip()

        # Drop unnamed index columns that sometimes appear
        unnamed = [c for c in df.columns if c.startswith('Unnamed')]
        if unnamed:
            df = df.drop(columns=unnamed)

        if df.shape[1] < 2:
            raise ValueError(f"Could not parse CSV correctly. Got {df.shape[1]} column(s).")

        self._log(f"Loaded {len(df):,} rows × {df.shape[1]} columns from {filepath}")
        return df

    # ------------------------------------------------------------------ #
    # 2. PRE-PROCESSING / CLEANING
    # ------------------------------------------------------------------ #

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full cleaning pipeline.

        Steps
        -----
        1. Check required columns exist.
        2. Coerce coordinate columns to float.
        3. Remove rows with NULL coordinates, result, or player name.
        4. Remove outlier coordinates (outside 0–1 range).
        5. Standardise result and player-name strings.
        6. Fill optional missing values with sensible defaults.
        7. Remove duplicate entries.

        Parameters
        ----------
        df : pd.DataFrame
            Raw dataframe (output of ``load_from_csv``).

        Returns
        -------
        pd.DataFrame
            Cleaned dataframe.
        """
        df = df.copy()
        initial_rows = len(df)

        # 1. Ensure required columns
        required = self.val_cfg.get('required_columns', ['X', 'Y', 'result', 'player'])
        missing_cols = [c for c in required if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # 2. Coerce X, Y to float
        for col in ['X', 'Y']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 3. Drop rows with NULL critical values
        critical = ['X', 'Y', 'result', 'player']
        before = len(df)
        df = df.dropna(subset=[c for c in critical if c in df.columns])
        self._log(f"Removed {before - len(df)} rows with NULL critical values")

        # 4. Remove outlier/impossible coordinates
        x_min, x_max = self.val_cfg.get('x_range', (0.0, 1.0))
        y_min, y_max = self.val_cfg.get('y_range', (0.0, 1.0))
        before = len(df)

        # Accept coordinates in metres (>1) and normalise them
        df = self._handle_coordinate_scale(df)

        mask_valid = (
            df['X'].between(x_min, x_max) & df['Y'].between(y_min, y_max)
        )
        df = df[mask_valid]
        self._log(f"Removed {before - len(df)} rows with out-of-range coordinates")

        # 5. Standardise result values
        valid_results = self.val_cfg.get(
            'valid_results', {'Goal', 'MissedShots', 'SavedShot', 'BlockedShot'}
        )
        before = len(df)
        df = df[df['result'].isin(valid_results)]
        self._log(f"Removed {before - len(df)} rows with unknown result values")

        # 6. Standardise player / team names
        df['player'] = df['player'].apply(_standardize_name)
        for col in ['h_team', 'a_team']:
            if col in df.columns:
                df[col] = df[col].apply(_standardize_name)

        # 7. Fill optional missing values
        df = self._fill_optional_missing(df)

        # 8. Remove duplicates (same player, match, X, Y, result, minute)
        dup_cols = [c for c in ['player', 'match_id', 'X', 'Y', 'result', 'minute']
                    if c in df.columns]
        before = len(df)
        df = df.drop_duplicates(subset=dup_cols)
        self._log(f"Removed {before - len(df)} duplicate rows")

        # 9. Create is_goal flag
        df['is_goal'] = (df['result'] == 'Goal').astype(int)

        removed_total = initial_rows - len(df)
        self._log(
            f"Preprocessing complete: {len(df):,} rows kept "
            f"({removed_total} removed from {initial_rows:,})"
        )
        return df.reset_index(drop=True)

    def _handle_coordinate_scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise coordinates to the 0-1 range.

        Understat uses 0-1 normalised coordinates. Some CSV exports use raw
        metres (values up to ~105/68) or per-mille notation (values up to
        ~1000). This method handles all three cases per row so that datasets
        with mixed formats are handled correctly.
        """
        df = df.copy()
        pl = self.data_cfg.get('pitch_length', 105.0)
        pw = self.data_cfg.get('pitch_width', 68.0)

        for coord, pitch_dim in (('X', pl), ('Y', pw)):
            col = df[coord]
            max_val = col.max(skipna=True)

            if max_val > 2.0:
                # Determine scale factor per row
                # Values > pitch_dim are assumed per-mille (÷1000)
                # Values between 2 and pitch_dim are assumed metres
                if max_val > pitch_dim * 2:
                    # Per-mille encoding (0-1000 range)
                    self._log(
                        f"Mixed/per-mille {coord} coordinates detected "
                        f"(max={max_val:.1f}); normalising per-row"
                    )
                    df[coord] = df[coord].apply(
                        lambda v: v / 1000.0 if v > 1.0 else v
                    )
                else:
                    # Metre-scale
                    self._log(
                        f"Metre-scale {coord} coordinates detected "
                        f"(max={max_val:.1f}); normalising by {pitch_dim}"
                    )
                    df[coord] = df[coord] / pitch_dim

        # Clip to valid range
        df['X'] = df['X'].clip(0.0, 1.0)
        df['Y'] = df['Y'].clip(0.0, 1.0)
        return df

    def _fill_optional_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill optional columns with sensible defaults."""
        df = df.copy()
        fill_xg = self.val_cfg.get('fill_missing_xg', True)
        default_xg = self.val_cfg.get('default_xg', 0.05)

        if 'xG' in df.columns:
            df['xG'] = pd.to_numeric(df['xG'], errors='coerce')
            if fill_xg:
                df['xG'] = df['xG'].fillna(default_xg)
            df['xG'] = df['xG'].clip(0.0, 1.0)
        else:
            df['xG'] = default_xg

        if 'minute' in df.columns:
            df['minute'] = pd.to_numeric(df['minute'], errors='coerce').fillna(45)
            df['minute'] = df['minute'].clip(0, 120)
        else:
            df['minute'] = 45

        if 'shotType' not in df.columns:
            df['shotType'] = 'Unknown'
        else:
            df['shotType'] = df['shotType'].fillna('Unknown')

        if 'situation' not in df.columns:
            df['situation'] = 'OpenPlay'
        else:
            df['situation'] = df['situation'].fillna('OpenPlay')

        if 'season' in df.columns:
            df['season'] = pd.to_numeric(df['season'], errors='coerce').fillna(0).astype(int)

        if 'match_id' not in df.columns:
            # Create a synthetic match ID from date + teams if available
            if 'date' in df.columns and 'h_team' in df.columns:
                df['match_id'] = (
                    df['date'].astype(str) + '_' + df.get('h_team', '').astype(str)
                )
            else:
                df['match_id'] = 0

        return df

    # ------------------------------------------------------------------ #
    # 3. FEATURE ENGINEERING
    # ------------------------------------------------------------------ #

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived features: distance, angle, bins, zones, temporal, etc.

        Parameters
        ----------
        df : pd.DataFrame
            Cleaned dataframe (output of ``preprocess``).

        Returns
        -------
        pd.DataFrame
            Dataframe with additional feature columns.
        """
        df = df.copy()

        goal_x = self.data_cfg.get('goal_x', 1.0)
        goal_y = self.data_cfg.get('goal_y', 0.5)
        pl = self.data_cfg.get('pitch_length', 105.0)
        pw = self.data_cfg.get('pitch_width', 68.0)

        # --- Distance & Angle -------------------------------------------
        df['distance'] = df.apply(
            lambda r: _calculate_distance(r['X'], r['Y'], goal_x, goal_y, pl, pw),
            axis=1,
        )
        df['angle'] = df.apply(
            lambda r: _calculate_angle(r['X'], r['Y'], goal_y, pl, pw),
            axis=1,
        )

        # Remove impossible shots
        max_dist = self.feat_cfg.get('distance', {}).get('max_valid_dist', 80)
        before = len(df)
        df = df[df['distance'] <= max_dist]
        self._log(f"Removed {before - len(df)} rows with distance > {max_dist}m")

        # --- Distance & Angle Bins --------------------------------------
        dist_bins = self.dist_cfg.get('bins', [])
        angle_bins = self.angle_cfg.get('bins', [])
        df['distance_bin'] = df['distance'].apply(lambda d: _bin_distance(d, dist_bins))
        df['angle_bin'] = df['angle'].apply(lambda a: _bin_angle(a, angle_bins))

        # Make bins ordered categoricals
        dist_order = self.dist_cfg.get('order', [])
        angle_order = self.angle_cfg.get('order', [])
        if dist_order:
            df['distance_bin'] = pd.Categorical(
                df['distance_bin'], categories=dist_order, ordered=True
            )
        if angle_order:
            df['angle_bin'] = pd.Categorical(
                df['angle_bin'], categories=angle_order, ordered=True
            )

        # --- Zone Features ----------------------------------------------
        df = self._add_zone_features(df)

        # --- Temporal Features ------------------------------------------
        df = self._add_temporal_features(df)

        # --- Shot Quality / Context -------------------------------------
        df['xg_per_shot_label'] = df['xG'].apply(self._xg_quality_label)

        self._log(f"Feature engineering complete: {df.shape[1]} columns")
        return df.reset_index(drop=True)

    def _add_zone_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add penalty box, half-space, quadrant, and danger zone flags."""
        df = df.copy()

        # Penalty box flag
        pb_x = self.data_cfg.get('penalty_box_x', 0.835)
        pb_y_min = self.data_cfg.get('penalty_box_y_min', 0.21)
        pb_y_max = self.data_cfg.get('penalty_box_y_max', 0.79)
        df['in_penalty_box'] = (
            (df['X'] >= pb_x) & df['Y'].between(pb_y_min, pb_y_max)
        ).astype(int)

        # Six-yard box flag
        sb_x = self.data_cfg.get('six_yard_box_x', 0.943)
        sb_y_min = self.data_cfg.get('six_yard_box_y_min', 0.37)
        sb_y_max = self.data_cfg.get('six_yard_box_y_max', 0.63)
        df['in_six_yard_box'] = (
            (df['X'] >= sb_x) & df['Y'].between(sb_y_min, sb_y_max)
        ).astype(int)

        # Quadrant (left / center / right)
        quadrants = self.zone_cfg.get('quadrants', {
            'left':   {'y_min': 0.0,  'y_max': 0.35},
            'center': {'y_min': 0.35, 'y_max': 0.65},
            'right':  {'y_min': 0.65, 'y_max': 1.0},
        })

        def _quadrant(y: float) -> str:
            for name, bounds in quadrants.items():
                if bounds['y_min'] <= y < bounds['y_max']:
                    return name
            return 'center'

        df['quadrant'] = df['Y'].apply(_quadrant)

        # Half-space detection (y between 0.2-0.4 or 0.6-0.8)
        df['in_half_space'] = (
            (df['Y'].between(0.2, 0.4) | df['Y'].between(0.6, 0.8))
            & (df['X'] >= 0.7)
        ).astype(int)

        # Danger zone composite label
        df['zone_label'] = np.where(
            df['in_six_yard_box'] == 1, '6-Yard Box',
            np.where(
                df['in_penalty_box'] == 1, 'Penalty Box',
                np.where(df['in_half_space'] == 1, 'Half-Space', 'Outside Box'),
            ),
        )

        return df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add match period, home/away, and season labels."""
        df = df.copy()
        temp_cfg = self.feat_cfg.get('temporal', {})

        # Match period from minute
        if 'minute' in df.columns:
            period_bins = temp_cfg.get('period_bins', [0, 15, 30, 45, 60, 75, 90, 120])
            period_labels = temp_cfg.get(
                'period_labels', ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90', '90+']
            )
            df['match_period'] = pd.cut(
                df['minute'],
                bins=period_bins,
                labels=period_labels,
                right=False,
                include_lowest=True,
            )

        # Home / Away
        if 'h_a' in df.columns:
            df['home_away'] = df['h_a'].map({'h': 'Home', 'a': 'Away'}).fillna('Unknown')

        # Date parsing
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['match_year'] = df['date'].dt.year
            df['match_month'] = df['date'].dt.month

        return df

    @staticmethod
    def _xg_quality_label(xg: float) -> str:
        """Map an xG value to a quality label."""
        if xg >= 0.5:
            return 'High Quality (xG≥0.5)'
        elif xg >= 0.2:
            return 'Good Quality (0.2≤xG<0.5)'
        elif xg >= 0.1:
            return 'Moderate Quality (0.1≤xG<0.2)'
        else:
            return 'Low Quality (xG<0.1)'

    # ------------------------------------------------------------------ #
    # 4. INTELLIGENT BIN OPTIMISATION
    # ------------------------------------------------------------------ #

    def optimise_bins(
        self,
        df: pd.DataFrame,
        feature: str = 'distance',
        n_bins: int = 5,
    ) -> List[Dict]:
        """
        Suggest optimal bins based on the distribution of a feature.

        Uses quantile-based splitting so each bin contains approximately
        the same number of shots.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe with feature column.
        feature : str
            Column name ('distance' or 'angle').
        n_bins : int
            Number of bins to create.

        Returns
        -------
        list of dict
            Each dict has 'range' and 'label' keys.
        """
        if feature not in df.columns:
            return []

        quantiles = np.linspace(0, 100, n_bins + 1)
        edges = np.percentile(df[feature].dropna(), quantiles)
        edges = np.unique(np.round(edges, 1))

        bins = []
        for i in range(len(edges) - 1):
            lo = edges[i]
            hi = edges[i + 1] if i < len(edges) - 2 else float('inf')
            unit = 'm' if feature == 'distance' else '°'
            hi_label = f'{hi:.0f}' if hi != float('inf') else '+'
            bins.append({
                'range': (lo, hi),
                'label': f'{lo:.0f}-{hi_label}{unit}',
            })
        return bins

    # ------------------------------------------------------------------ #
    # 5. FILTERING HELPERS
    # ------------------------------------------------------------------ #

    def filter_by_player(self, df: pd.DataFrame, player: str) -> pd.DataFrame:
        """Return rows for a single player."""
        return df[df['player'] == player].copy()

    def filter_by_players(self, df: pd.DataFrame, players: List[str]) -> pd.DataFrame:
        """Return rows for a list of players."""
        return df[df['player'].isin(players)].copy()

    def filter_by_result(self, df: pd.DataFrame, results: List[str]) -> pd.DataFrame:
        """Return rows matching any of the given result types."""
        return df[df['result'].isin(results)].copy()

    def filter_by_season(self, df: pd.DataFrame, season: int) -> pd.DataFrame:
        """Return rows for a specific season."""
        if 'season' not in df.columns:
            return df
        return df[df['season'] == season].copy()

    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        Filter rows to a date range.

        Parameters
        ----------
        df : pd.DataFrame
            Data with 'date' column.
        start, end : str
            ISO date strings (YYYY-MM-DD).
        """
        if 'date' not in df.columns:
            return df
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        mask = df['date'].between(pd.Timestamp(start), pd.Timestamp(end))
        return df[mask].copy()

    # ------------------------------------------------------------------ #
    # 6. DATA QUALITY REPORT
    # ------------------------------------------------------------------ #

    def data_quality_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate a data quality report for the processed dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            Processed dataframe.

        Returns
        -------
        dict
            Quality metrics dictionary.
        """
        report = {
            'total_rows': len(df),
            'total_columns': df.shape[1],
            'unique_players': df['player'].nunique() if 'player' in df.columns else 0,
            'unique_matches': df['match_id'].nunique() if 'match_id' in df.columns else 0,
            'seasons': sorted(df['season'].unique().tolist()) if 'season' in df.columns else [],
            'result_distribution': (
                df['result'].value_counts().to_dict() if 'result' in df.columns else {}
            ),
            'missing_values': df.isnull().sum().to_dict(),
            'missing_pct': (df.isnull().mean() * 100).round(2).to_dict(),
            'coordinate_stats': {
                'x_min': float(df['X'].min()) if 'X' in df.columns else None,
                'x_max': float(df['X'].max()) if 'X' in df.columns else None,
                'y_min': float(df['Y'].min()) if 'Y' in df.columns else None,
                'y_max': float(df['Y'].max()) if 'Y' in df.columns else None,
            },
            'distance_stats': {
                'mean': float(df['distance'].mean()) if 'distance' in df.columns else None,
                'median': float(df['distance'].median()) if 'distance' in df.columns else None,
                'std': float(df['distance'].std()) if 'distance' in df.columns else None,
                'min': float(df['distance'].min()) if 'distance' in df.columns else None,
                'max': float(df['distance'].max()) if 'distance' in df.columns else None,
            },
            'angle_stats': {
                'mean': float(df['angle'].mean()) if 'angle' in df.columns else None,
                'median': float(df['angle'].median()) if 'angle' in df.columns else None,
                'std': float(df['angle'].std()) if 'angle' in df.columns else None,
                'min': float(df['angle'].min()) if 'angle' in df.columns else None,
                'max': float(df['angle'].max()) if 'angle' in df.columns else None,
            },
            'conversion_rate': (
                float(df['is_goal'].mean() * 100) if 'is_goal' in df.columns else None
            ),
            'total_xg': float(df['xG'].sum()) if 'xG' in df.columns else None,
            'processing_log': list(self._quality_log),
        }

        # Per-player summary
        if 'player' in df.columns and 'is_goal' in df.columns:
            player_summary = (
                df.groupby('player')
                .agg(
                    shots=('is_goal', 'count'),
                    goals=('is_goal', 'sum'),
                    xg=('xG', 'sum'),
                )
                .assign(conversion_rate=lambda x: (x['goals'] / x['shots'] * 100).round(1))
                .sort_values('shots', ascending=False)
            )
            report['player_summary'] = player_summary.to_dict()

        return report

    # ------------------------------------------------------------------ #
    # INTERNAL HELPERS
    # ------------------------------------------------------------------ #

    def _log(self, message: str) -> None:
        """Append a message to the quality log and optionally print it."""
        self._quality_log.append(message)
        if self.adv_cfg.get('verbose_logging', False):
            print(f"[DataProcessor] {message}")

    def get_available_players(self, df: pd.DataFrame) -> List[str]:
        """Return sorted list of unique player names."""
        return sorted(df['player'].unique().tolist())

    def get_available_seasons(self, df: pd.DataFrame) -> List[int]:
        """Return sorted list of unique seasons."""
        if 'season' not in df.columns:
            return []
        return sorted(df['season'].dropna().astype(int).unique().tolist())

    def get_available_teams(self, df: pd.DataFrame) -> List[str]:
        """Return sorted list of unique team names."""
        teams: set = set()
        for col in ['h_team', 'a_team']:
            if col in df.columns:
                teams.update(df[col].dropna().unique())
        return sorted(teams)


# ============================================================================
# MODULE SELF-TEST
# ============================================================================

if __name__ == '__main__':
    from multi_player_config import get_multi_player_config

    config = get_multi_player_config()
    processor = MultiPlayerDataProcessor(config)

    # Try to load sample data
    import os
    for fname in ['shot_data.csv', 'erling_haaland_2022_understat.csv']:
        if os.path.exists(fname):
            print(f"Loading {fname}…")
            df_raw = processor.load_from_csv(fname)
            df_clean = processor.preprocess(df_raw)
            df_feat = processor.add_features(df_clean)
            report = processor.data_quality_report(df_feat)
            print(f"✅ Processed {report['total_rows']:,} shots, "
                  f"{report['unique_players']} players")
            break
    else:
        print("No CSV file found for self-test; module imported OK")
