import numpy as np
import random
import xgboost as xgb
from core.config import CATEGORY_REVERSE, SEGMENT_NUM_MAP

FEATURE_COLS = [
    "recency_days", "frequency", "monetary",
    "avg_order_value", "dominant_category",
    "segment_num", "browse_count", "cart_abandon_count"
]

def train_offer_matcher(offers):
    """
    Trains an optimized XGBoost Classifier on high-affinity synthetic data
    resembling real-world Kirana store purchase trends.
    """
    if not offers:
        print("❌ No offers available to train on")
        return None

    X_train = []
    y_train = []

    # Generate 1,000 synthetic training examples matching strategic behavior distributions
    for _ in range(1000):
        offer_idx = random.randint(0, len(offers) - 1)
        o = offers[offer_idx]

        target_seg = o.get("targetSegment", "ALL_CUSTOMERS").upper().replace(" ", "_")
        target_cat = o.get("applicableCategory", "FOOD").upper()

        # Identify numerical equivalents safely
        seg_num = SEGMENT_NUM_MAP.get(target_seg.title().replace("_", " "), 1)
        cat_num = next(
            (k for k, v in CATEGORY_REVERSE.items() if v.upper() == target_cat), 0
        )

        # Synthesize true customer affinity behaviors
        # VIP/LOYAL segment telemetry
        if "VIP" in target_seg or "LOYAL" in target_seg:
            recency = random.randint(1, 14)
            frequency = random.randint(6, 25)
            browse_count = random.randint(3, 10)
            cart_abandon_count = random.randint(0, 1)
        # AT_RISK/DORMANT segment telemetry
        elif "RISK" in target_seg or "DORMANT" in target_seg:
            recency = random.randint(30, 120)
            frequency = random.randint(1, 4)
            browse_count = random.randint(0, 2)
            cart_abandon_count = random.randint(1, 3)
        # Fallback profile settings for general segments
        else:
            recency = random.randint(5, 45)
            frequency = random.randint(2, 10)
            browse_count = random.randint(1, 5)
            cart_abandon_count = random.randint(0, 2)

        monetary = frequency * random.randint(300, 2500)
        avg_order = monetary / frequency if frequency > 0 else 0

        X_train.append([
            recency, frequency, monetary, avg_order,
            cat_num,  # Match customer dominant category to offer category rule
            seg_num,
            browse_count, cart_abandon_count
        ])
        y_train.append(offer_idx)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    num_classes = len(offers)

    # 🎛️ XGBOOST TUNING UPGRADES
    xgb_model = xgb.XGBClassifier(
        n_estimators=150,            # Fewer trees needed than RF due to gradient boosting
        max_depth=5,                 # Shallower trees prevent overfitting
        learning_rate=0.1,           # Step size shrinkage to prevent overshooting
        objective="multi:softprob",  # Output probabilities for confidence scoring
        num_class=num_classes,       # Dynamically handles the number of active offers
        subsample=0.8,               # Randomly sample 80% of data per tree for variance reduction
        colsample_bytree=0.8,        # Randomly sample 80% of features per tree
        random_state=42,
        eval_metric="mlogloss"       # Standard loss function evaluation for multi-class
    )
    
    xgb_model.fit(X_train, y_train)
    print("✅ Optimized XGBoost Model trained successfully")

    return xgb_model

def predict_offer(xgb_model, customer_row, offers):
    """
    Predicts the best targeted offer using XGBoost probability scoring thresholds.
    Returns (offer, confidence_score).
    """
    if xgb_model is None or not offers:
        return None, 0

    seg_num = SEGMENT_NUM_MAP.get(customer_row["segment"], 0)

    X = np.array([[
        customer_row["recency_days"],
        customer_row["frequency"],
        customer_row["monetary"],
        customer_row["avg_order_value"],
        customer_row["dominant_category"],
        seg_num,
        customer_row["browse_count"],
        customer_row["cart_abandon_count"]
    ]])

    # 🚀 HIGH-CONFIDENCE PERFORMANCE GATEWAY
    probabilities = xgb_model.predict_proba(X)[0]
    best_offer_idx = np.argmax(probabilities)
    confidence = round(probabilities[best_offer_idx] * 100)

    # If the engine's absolute highest probability is still a weak guess (< 35%),
    # fallback to a safe general coupon instead of throwing garbage recommendations
    if confidence < 35:
        general_offers = [o for o in offers if o.get("targetSegment") in ["ALL_CUSTOMERS", "New"]]
        fallback_offer = general_offers[0] if general_offers else offers[0]
        return fallback_offer, confidence

    return offers[best_offer_idx], confidence

def get_offer_feature_importance(xgb_model, offers):
    """
    Returns verified system attribute impacts from the XGBoost model to isolate recommendation telemetry logs.
    """
    if xgb_model is None:
        return {}

    # XGBoost handles feature importances identically to Scikit-Learn via this attribute
    importances = xgb_model.feature_importances_
    return {
        col: round(float(imp), 4)
        for col, imp in zip(FEATURE_COLS, importances)
    }
