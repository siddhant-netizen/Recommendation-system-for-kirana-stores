import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from core.config import SEGMENTS

FEATURE_COLS = [
    "recency_days", "frequency", "monetary",
    "avg_order_value", "browse_count", "cart_abandon_count"
]

def segment_customers(df):
    """
    Uses KMeans clustering to automatically discover
    customer segments from behavioral features.
    Returns df with 'cluster' and 'segment' columns added.
    """
    if df.empty:
        print("⚠️ No customer data to segment")
        return df

    if len(df) < 5:
        print(f"⚠️ Only {len(df)} customers — using simplified segmentation")

    X = df[FEATURE_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Dynamically adjust clusters based on available customers
    n_clusters = min(5, len(df))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Score each cluster
    # Lower recency + higher frequency + higher monetary = better segment
    cluster_stats = df.groupby("cluster").agg({
        "recency_days": "mean",
        "frequency": "mean",
        "monetary": "mean"
    })

    cluster_stats["score"] = (
        -cluster_stats["recency_days"] +
        cluster_stats["frequency"] * 10 +
        cluster_stats["monetary"] / 100
    )

    # Rank clusters by score and assign segment labels
    ranked = cluster_stats["score"].rank(
        ascending=False, method="first"
    ).astype(int)

    segment_labels = {i+1: seg for i, seg in enumerate(SEGMENTS)}
    cluster_to_segment = {
        cluster: segment_labels.get(rank, "New")
        for cluster, rank in ranked.items()
    }

    df["segment"] = df["cluster"].map(cluster_to_segment)

    # Print segment distribution
    print("\nSegment Distribution:")
    dist = df["segment"].value_counts()
    for seg, count in dist.items():
        print(f"  {seg}: {count} customers")

    return df
