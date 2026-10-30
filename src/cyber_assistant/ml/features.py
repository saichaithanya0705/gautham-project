"""Domain feature engineering for CIC-IDS2017 network flow records."""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

# Core raw numeric features from the dataset that provide high discriminatory value
RAW_NUMERIC_FEATURES = [
    "protocol",
    "flow_duration",
    "total_fwd_packets",
    "total_backward_packets",
    "fwd_packets_length_total",
    "bwd_packets_length_total",
    "fwd_packet_length_max",
    "fwd_packet_length_min",
    "fwd_packet_length_mean",
    "fwd_packet_length_std",
    "bwd_packet_length_max",
    "bwd_packet_length_min",
    "bwd_packet_length_mean",
    "bwd_packet_length_std",
    "flow_bytes_s",
    "flow_packets_s",
    "flow_iat_mean",
    "flow_iat_std",
    "flow_iat_max",
    "flow_iat_min",
    "fwd_iat_mean",
    "fwd_iat_std",
    "bwd_iat_mean",
    "bwd_iat_std",
    "fwd_header_length",
    "bwd_header_length",
    "fwd_packets_s",
    "bwd_packets_s",
    "packet_length_min",
    "packet_length_max",
    "packet_length_mean",
    "packet_length_std",
    "packet_length_variance",
    "fin_flag_count",
    "syn_flag_count",
    "rst_flag_count",
    "psh_flag_count",
    "ack_flag_count",
    "urg_flag_count",
    "down_up_ratio",
    "avg_packet_size",
    "init_fwd_win_bytes",
    "init_bwd_win_bytes",
    "fwd_act_data_packets",
    "fwd_seg_size_min",
    "active_mean",
    "active_std",
    "idle_mean",
    "idle_std",
]

ENGINEERED_FEATURE_NAMES = [
    "fwd_bwd_packet_ratio",
    "fwd_bwd_byte_ratio",
    "bytes_per_packet",
    "payload_asymmetry",
    "log_flow_duration",
    "log_flow_bytes_s",
    "log_flow_packets_s",
    "syn_ratio",
    "rst_ratio",
    "fin_ack_ratio",
    "iat_spread",
    "iat_variability",
    "active_idle_ratio",
    "idle_duration_fraction",
    "init_win_ratio",
    "is_single_packet_flow",
]

ALL_MODEL_FEATURES = RAW_NUMERIC_FEATURES + ENGINEERED_FEATURE_NAMES


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and engineer security features from raw CIC-IDS2017 flow DataFrame.

    Handles clean ratio computation, log-scaling, and NaN/inf sanitization.
    """
    out = df.copy()

    # Ensure required raw columns exist, fill with 0 if absent
    for col in RAW_NUMERIC_FEATURES:
        if col not in out.columns:
            out[col] = 0.0
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    # Sanitize raw flow rates against infinity/NaN
    out["flow_bytes_s"] = np.nan_to_num(out["flow_bytes_s"].to_numpy(), nan=0.0, posinf=1e9, neginf=0.0)
    out["flow_packets_s"] = np.nan_to_num(out["flow_packets_s"].to_numpy(), nan=0.0, posinf=1e9, neginf=0.0)

    total_fwd_pkts = out["total_fwd_packets"].to_numpy(dtype=float)
    total_bwd_pkts = out["total_backward_packets"].to_numpy(dtype=float)
    total_pkts = total_fwd_pkts + total_bwd_pkts
    fwd_len = out["fwd_packets_length_total"].to_numpy(dtype=float)
    bwd_len = out["bwd_packets_length_total"].to_numpy(dtype=float)
    total_len = fwd_len + bwd_len
    duration = out["flow_duration"].to_numpy(dtype=float)

    # 1. Directional Ratios & Asymmetry
    out["fwd_bwd_packet_ratio"] = total_fwd_pkts / (total_bwd_pkts + 1.0)
    out["fwd_bwd_byte_ratio"] = fwd_len / (bwd_len + 1.0)
    out["bytes_per_packet"] = total_len / (total_pkts + 1.0)
    out["payload_asymmetry"] = np.abs(fwd_len - bwd_len) / (total_len + 1.0)

    # 2. Rate & Log Transformations
    out["log_flow_duration"] = np.log10(np.maximum(0.0, duration) + 1.0)
    out["log_flow_bytes_s"] = np.log10(np.maximum(0.0, out["flow_bytes_s"].to_numpy(dtype=float)) + 1.0)
    out["log_flow_packets_s"] = np.log10(np.maximum(0.0, out["flow_packets_s"].to_numpy(dtype=float)) + 1.0)

    # 3. Flag Distribution Profiles
    syn_flags = out["syn_flag_count"].to_numpy(dtype=float)
    rst_flags = out["rst_flag_count"].to_numpy(dtype=float)
    fin_flags = out["fin_flag_count"].to_numpy(dtype=float)
    ack_flags = out["ack_flag_count"].to_numpy(dtype=float)

    out["syn_ratio"] = syn_flags / (total_fwd_pkts + 1.0)
    out["rst_ratio"] = rst_flags / (total_pkts + 1.0)
    out["fin_ack_ratio"] = (fin_flags + ack_flags) / (total_pkts + 1.0)

    # 4. Inter-Arrival Time (IAT) Dynamics
    iat_max = out["flow_iat_max"].to_numpy(dtype=float)
    iat_min = out["flow_iat_min"].to_numpy(dtype=float)
    iat_std = out["flow_iat_std"].to_numpy(dtype=float)
    iat_mean = out["flow_iat_mean"].to_numpy(dtype=float)

    out["iat_spread"] = iat_max - iat_min
    out["iat_variability"] = iat_std / (iat_mean + 1.0)

    # 5. Idleness & Window Metrics
    act_mean = out["active_mean"].to_numpy(dtype=float)
    idle_mean = out["idle_mean"].to_numpy(dtype=float)
    out["active_idle_ratio"] = (act_mean + 1.0) / (idle_mean + 1.0)
    out["idle_duration_fraction"] = (idle_mean * 1000.0) / (duration + 1.0)

    fwd_win = np.maximum(0.0, out["init_fwd_win_bytes"].to_numpy(dtype=float))
    bwd_win = np.maximum(0.0, out["init_bwd_win_bytes"].to_numpy(dtype=float))
    out["init_win_ratio"] = (fwd_win + 1.0) / (bwd_win + 1.0)

    # 6. Single packet indicator (common in scanning)
    out["is_single_packet_flow"] = ((total_pkts <= 1.0) | (duration == 0.0)).astype(float)

    # Replace any potential inf or NaN in engineered features
    for col in ENGINEERED_FEATURE_NAMES:
        out[col] = np.nan_to_num(out[col].to_numpy(), nan=0.0, posinf=1e6, neginf=-1e6)

    return out[ALL_MODEL_FEATURES]


def extract_single_flow_features(flow_dict: dict[str, Any]) -> pd.DataFrame:
    """Convenience helper to extract features for a single flow dictionary."""
    df = pd.DataFrame([flow_dict])
    return extract_features(df)
