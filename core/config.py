# ─────────────────────────────────────────
# config.py — Central configuration
# ─────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")
WEBHOOK_URL_SINGLE = os.getenv("WEBHOOK_URL_SINGLE", "https://sandbox-automation.neailabs.com/webhook-test/n8n_single")
WEBHOOK_URL_GROUP = os.getenv("WEBHOOK_URL_GROUP", "https://sandbox-automation.neailabs.com/webhook-test/n8n_bulk")

# Confidence threshold from technical spec
CONFIDENCE_THRESHOLD = 0.85

# RFM Scoring Thresholds
RECENCY_THRESHOLDS = [7, 14, 30, 60]      # days
FREQUENCY_THRESHOLDS = [5, 3, 2, 1]       # purchase count
MONETARY_THRESHOLDS = [5000, 3000, 1500, 500]  # amount in rupees

# Segment Labels
SEGMENTS = ["VIP", "Loyal", "At Risk", "New", "Dormant"]

# Category Mappings
CATEGORY_MAP = {
    "ELECTRONICS": 0,
    "CLOTHING": 1,
    "FOOD": 2,
    "BEAUTY": 3,
    "SPORTS": 4
}

CATEGORY_REVERSE = {v: k for k, v in CATEGORY_MAP.items()}

# Segment to API value mapping
SEGMENT_API_MAP = {
    "VIP": "VIP",
    "Loyal": "LOYAL",
    "At Risk": "AT_RISK",
    "New": "NEW",
    "Dormant": "DORMANT"
}

SEGMENT_NUM_MAP = {
    "VIP": 4,
    "Loyal": 3,
    "At Risk": 2,
    "New": 1,
    "Dormant": 0
}
