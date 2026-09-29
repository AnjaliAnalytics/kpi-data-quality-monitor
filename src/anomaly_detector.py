import numpy as np
import pandas as pd
from typing import Dict, List, Any

def calculate_baseline(history_series: pd.Series, method: str = "z_score") -> Dict[str, float]:
    """Calculates statistical baselines (mean, std dev, rolling averages, IQR)."""
    if history_series.empty:
        return {"mean": 0.0, "std": 0.0, "rolling_7d": 0.0, "median": 0.0, "iqr": 0.0}

    mean_val = float(history_series.mean())
    std_val = float(history_series.std()) if len(history_series) > 1 else 0.0
    rolling_7d = float(history_series.tail(7).mean())
    
    q25, q75 = np.percentile(history_series, [25, 75])
    iqr_val = float(q75 - q25)
    median_val = float(np.median(history_series))

    return {
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "rolling_7d": round(rolling_7d, 2),
        "median": round(median_val, 2),
        "iqr": round(iqr_val, 2)
    }

def calculate_change(current_val: float, baseline_val: float) -> float:
    """Calculates percentage change between current metric value and baseline value."""
    if baseline_val == 0:
        return 0.0
    return round(((current_val - baseline_val) / baseline_val) * 100.0, 2)

def calculate_severity(deviation_pct: float, critical_thresh: float = 30.0, warning_thresh: float = 15.0) -> str:
    """Classifies anomaly severity based on percentage breach thresholds."""
    abs_dev = abs(deviation_pct)
    if abs_dev >= critical_thresh:
        return "CRITICAL"
    elif abs_dev >= warning_thresh:
        return "WARNING"
    else:
        return "INFO"

def detect_anomaly(
    current_value: float, 
    history_df: pd.DataFrame, 
    anomaly_config: dict
) -> Dict[str, Any]:
    """
    Evaluates whether today's KPI value breaches statistical threshold limits (Z-Score or IQR).
    Returns a structured dictionary formatted for LLM consumption and incident logging.
    """
    method = anomaly_config.get("method", "z_score")
    threshold = anomaly_config.get("threshold", 2.0)
    sev_rules = anomaly_config.get("severity_rules", {})
    
    crit_thresh = sev_rules.get("critical_deviation_pct", 30.0)
    warn_thresh = sev_rules.get("warning_deviation_pct", 15.0)

    values = history_df["metric_value"] if not history_df.empty else pd.Series([current_value])
    baselines = calculate_baseline(values, method=method)

    is_anomaly = False
    z_score = 0.0
    expected_value = baselines["rolling_7d"] if baselines["rolling_7d"] > 0 else baselines["mean"]

    if method == "z_score":
        if baselines["std"] > 0:
            z_score = round((current_value - baselines["mean"]) / baselines["std"], 2)
            if abs(z_score) >= threshold:
                is_anomaly = True
    elif method == "iqr":
        q25 = baselines["median"] - (0.5 * baselines["iqr"])
        q75 = baselines["median"] + (0.5 * baselines["iqr"])
        lower_bound = q25 - (threshold * baselines["iqr"])
        upper_bound = q75 + (threshold * baselines["iqr"])
        if current_value < lower_bound or current_value > upper_bound:
            is_anomaly = True

    change_pct = calculate_change(current_value, expected_value)
    severity = calculate_severity(change_pct, crit_thresh, warn_thresh) if is_anomaly else "NORMAL"

    return {
        "current_value": round(current_value, 2),
        "expected_value": round(expected_value, 2),
        "change_percent": change_pct,
        "z_score": z_score,
        "is_anomaly": is_anomaly,
        "severity": severity,
        "baselines": baselines
    }