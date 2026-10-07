# 🏪 Kirana Store AI Recommendation & Autonomous Retention Engine

An enterprise-grade, hyper-local recommendation engine and customer retention system designed specifically for Indian Kirana retail stores. The platform integrates directly with **Twenty CRM** (open-source CRM), combines **RFM behavioral analytics**, **XGBoost machine learning**, **local Google Maps neighborhood intelligence**, **environmental & cultural event triggers**, and **autonomous GenAI campaign creation**.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Prerequisites & Environment Configuration](#-prerequisites--environment-configuration)
3. [Twenty CRM Setup Guide (New Instance)](#-twenty-crm-setup-guide-new-instance)
   - [Required Custom Objects & Fields](#required-custom-objects--schema-definitions)
   - [API Key Generation](#api-key-generation)
4. [Core Functionalities & How They Work](#-core-functionalities--how-they-work)
   - [1. Feature Engineering & Telemetry](#1-feature-engineering--telemetry-corefeature_engineerpy)
   - [2. Customer Segmentation](#2-customer-segmentation-coresegmentationpy)
   - [3. Customer Group Sync](#3-customer-group-sync-coregroup_syncpy)
   - [4. Neighborhood Locality Profiling](#4-neighborhood-locality-profiling-corelocality_scorerpy)
   - [5. Autonomous Environmental & Cultural AI Campaigns](#5-autonomous-environmental--cultural-ai-campaigns-coreai_marketerpy--context_fetcherpy)
   - [6. XGBoost Offer Recommendation Engine](#6-xgboost-offer-recommendation-engine-corerecommenderpy)
   - [7. Behavior Drift Detection & Win-Back Triggers](#7-behavior-drift-detection--win-back-triggers-coreoffer_generatorpy)
5. [⚠️ Critical Notice: Webhook Dispatch Architecture](#️-critical-notice-webhook-dispatch-architecture)
6. [Step-by-Step Execution Guide](#-step-by-step-execution-guide)
7. [Repository Structure](#-repository-structure)

---

## 🏗️ Architecture Overview

The engine operates on a **Dual-Paradigm Architecture**:

```
                                  ┌───────────────────────────────┐
                                  │      Twenty CRM Instance      │
                                  │ (Customers, Purchases, Offers)│
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │   core/data_fetcher   │
                                      └───────────┬───────────┘
                                                  │
             ┌────────────────────────────────────┴────────────────────────────────────┐
             ▼                                                                         ▼
   [ PARADIGM 1: CUSTOMER TELEMETRY ]                                [ PARADIGM 2: HYPERLOCAL CONTEXT ]
  ┌────────────────────────────────────┐                           ┌─────────────────────────────────────┐
  │ 1. Feature Engineering (RFM, Cart) │                           │ 1. Weather Signal (Open-Meteo)      │
  │ 2. KMeans Cluster Segmentation     │                           │ 2. Cultural Signal (Calendarific)   │
  │ 3. Group Sync to Twenty CRM        │                           │ 3. Locality Scorer (Google Reviews) │
  │ 4. XGBoost Offer Matcher           │                           │ 4. Autonomous GenAI Marketer        │
  │ 5. Behavior Drift Detection        │                           │    (Gemini 2.5 Flash Campaign Gen)  │
  └─────────────────┬──────────────────┘                           └──────────────────┬──────────────────┘
                    │                                                                 │
                    └─────────────────────────────┬───────────────────────────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │  Confidence Blending  │
                                      │  (60% ML + 40% Local) │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │   Twenty CRM Sync     │
                                      │  (customeroffers join)│
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                 ┌─────────────────────────────────┐
                                 │       Webhook Dispatcher        │
                                 │ 🚨 BOTH Single & Group Webhooks │
                                 └─────────────────────────────────┘
```

---

## 🔑 Prerequisites & Environment Configuration

### System Requirements
- Python 3.10+
- Access to a running instance of **Twenty CRM** (default: `http://localhost:3000`)
- Valid API keys for external data providers

### Dependencies (`requirements.txt`)
```text
requests>=2.31.0
httpx>=0.27.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=2.0.0
google-generativeai>=0.8.0
apify-client>=1.0.0
python-dotenv>=1.0.0
```

### Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
# Twenty CRM
TWENTY_API_KEY=your_twenty_crm_jwt_token_here
TWENTY_BASE_URL=http://localhost:3000

# Webhooks (n8n, Zapier, or custom receiver)
WEBHOOK_URL_SINGLE=https://sandbox-automation.neailabs.com/webhook-test/n8n_single
WEBHOOK_URL_GROUP=https://sandbox-automation.neailabs.com/webhook-test/n8n_bulk

# External Context Providers
GOOGLE_API_KEY=your_google_places_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
APIFY_API_KEY=your_apify_api_token_here
CALENDARIFIC_API_KEY=your_calendarific_api_key_here
```

---

## 🏢 Twenty CRM Setup Guide (New Instance)

When provisioning a **fresh Twenty CRM instance**, the default installation does not contain the specialized custom objects needed for Kirana store telemetry. You must configure the following custom objects and fields.

### 1. API Key Generation
1. Open Twenty CRM web dashboard (e.g., `http://localhost:3000`).
2. Navigate to **Settings** (`⚙️`) -> **Developers** -> **API Keys**.
3. Create a new API Key with full Read & Write permissions across workspace objects.
4. Copy the generated JWT Bearer token into your `.env` file as `TWENTY_API_KEY`.

### 2. Required Custom Objects & Schema Definitions

Configure the following 5 objects via the Twenty CRM Data Model settings or REST API:

#### A. `customers` Object (`/rest/customers`)
Stores primary customer profile telemetry and device metadata:
| Field Identifier | Type | Constraints / Description |
| :--- | :--- | :--- |
| `name` | Text | Customer first name |
| `lastName` | Text | Customer last name |
| `email` | Email | Composite object (`{"primaryEmail": "user@test.com"}`) |
| `phone` | Phone | Composite object (`{"primaryPhoneNumber": "+91..."}`) |
| `city` | Text | Resident city (e.g. `Pune`, `Nagpur`, `Mumbai`) |
| `primaryCountry` | Text | E.g. `India` |
| `mobileOs` | Text / Enum | `Android`, `iOS` |
| `deviceModel` | Text | Device model (e.g. `OnePlus Nord`, `iPhone 15`) |
| `gender` | Enum | `MALE`, `FEMALE`, `OTHER` |
| `behavioralTags` | Array / Text | E.g. `["tech_affinity", "deal_seeker"]` |
| `mlFeatureVector` | JSON | Model weights & propensity (e.g. `{"propensity_score": 0.95}`) |
| `customerGroupsId` | Relation | Foreign key link to `customerGroups` object |

#### B. `purchases` Object (`/rest/purchases`)
Logs transaction events, browsing sessions, and cart drops:
| Field Identifier | Type | Constraints / Description |
| :--- | :--- | :--- |
| `name` | Text | Activity descriptor (e.g. `PURCHASE - Food`) |
| `customerId` | Relation / UUID | Foreign key link to `customers.id` |
| `activityType` | Enum | Must be exact uppercase: `PURCHASE`, `BROWSE`, `CART_ABANDON` |
| `category` | Enum | Allowed categories: `ELECTRONICS`, `CLOTHING`, `FOOD` |
| `amount` | Number | Transaction amount in INR (0 for browse/abandon) |
| `activityDate` | DateTime (ISO) | Event timestamp (`YYYY-MM-DDTHH:MM:SSZ`) |
| `sourceDomain` | Text | Web/POS source domain |
| `rawPayload` | JSON | Telemetry metadata (`{"ip": "...", "user_agent": "..."}`) |

#### C. `offers` Object (`/rest/offers`)
Catalog of discount vouchers and retention promotions:
| Field Identifier | Type | Constraints / Description |
| :--- | :--- | :--- |
| `name` | Text | Offer promotion name |
| `offerType` | Enum | Exact uppercase: `DISCOUNT`, `CASHBACK`, `FREE_SHIPPING`, `BUNDLE` |
| `discountPercentage`| Number | Integer discount value (e.g. `10`, `20`, `30`) |
| `minimumOrderValue` | Number | Minimum basket size in INR (e.g. `200`, `500`) |
| `applicableCategory`| Enum | Exact uppercase: `FOOD`, `CLOTHING`, `ELECTRONICS` |
| `targetSegment` | Enum | Exact uppercase: `VIP`, `LOYAL`, `AT_RISK`, `NEW`, `DORMANT`, `ALL_CUSTOMERS` |
| `expiryDate` | DateTime (ISO) | Promotion expiration timestamp |
| `isActive` | Boolean | `true` or `false` |

#### D. `customerGroups` Object (`/rest/customerGroups`)
Stores aggregate behavioral statistics across customer segments:
| Field Identifier | Type | Constraints / Description |
| :--- | :--- | :--- |
| `name` | Text | Segment label: `VIP`, `Loyal`, `At Risk`, `New`, `Dormant` |
| `groupName` | Text | Mirror of segment name |
| `rfmSegment` | Enum | Exact uppercase: `VIP`, `LOYAL`, `AT_RISK`, `NEW`, `DORMANT` |
| `size` | Number | Number of customers assigned to this cluster |
| `avgspend` | Number | Average monetary value in INR |
| `avgpurchasefrequency`| Number | Average transaction frequency count |
| `dominantCategory` | Enum | Dominant segment preference: `FOOD`, `CLOTHING`, `ELECTRONICS` |

#### E. `customeroffers` Object (`/rest/customeroffers`)
The central recommendation join-table linking customers to their matched offers:
| Field Identifier | Type | Constraints / Description |
| :--- | :--- | :--- |
| `customersId` | Relation / UUID | Foreign key link to `customers.id` |
| `offerId` | Relation / UUID | Foreign key link to `offers.id` |
| `rfmSegment` | Enum | Customer segment at time of recommendation |
| `confidenceScore` | Number | Blended confidence score (0.0 to 1.0) |
| `recommendationReason`| Text | Audit reason (e.g. `ML Engine Match` or `Trigger A: Behavior Drift`) |
| `status` | Enum | Recommendation status (e.g. `PENDING`, `ACCEPTED`, `EXPIRED`) |
| `deliveryStatus` | Enum | Notification status (e.g. `PENDING`, `SENT`) |
| `recommendedAt` | Date (ISO) | Date of recommendation (`YYYY-MM-DD`) |

---

## ⚙️ Core Functionalities & How They Work

### 1. Feature Engineering & Telemetry (`core/feature_engineer.py`)
- **How it works:** Ingests raw customer profiles and purchase telemetry from Twenty CRM via pagination.
- **Optimization:** Groups activities by `customerId` in a single pass ($O(N + M)$ time complexity).
- **Extracted Attributes:**
  - `recency_days`: Days elapsed since the customer's last purchase (`999` if no purchases).
  - `frequency`: Total count of `PURCHASE` activities.
  - `monetary`: Total lifetime rupees spent.
  - `avg_order_value`: `monetary / frequency`.
  - `dominant_category`: Most frequent transaction category mapped to an integer index.
  - `browse_count`: Telemetry count of non-transactional store visits.
  - `cart_abandon_count`: High-intent sessions where items were added without checkout.

### 2. Customer Segmentation (`core/segmentation.py`)
- **How it works:** Implements unsupervised **K-Means Clustering** over scaled features (`StandardScaler`).
- **Dynamic Cluster Scaling:** Adjusts number of clusters based on dataset size (`k = min(5, len(df))`).
- **Composite RFM Scoring:** Each cluster is ranked using an economic scoring formula:
  $$\text{Score} = -\text{recency\_days} + (\text{frequency} \times 10) + \left(\frac{\text{monetary}}{100}\right)$$
- **Cluster to Tier Mapping:** Ranked clusters are assigned to business tiers:
  1. **VIP**: Highest spend, highest frequency, lowest recency.
  2. **Loyal**: Consistent repeat buyers with stable baskets.
  3. **At Risk**: Historical buyers who have not purchased recently.
  4. **New**: First-time or recent signups with low purchase history.
  5. **Dormant**: High recency (silent > 60 days) with low spend.

### 3. Customer Group Sync (`core/group_sync.py`)
- Aggregates cluster statistics (`size`, `avg_spend`, `avg_frequency`, `dominant_category`).
- Checks existing groups in Twenty CRM to prevent duplicate records.
- Updates existing groups (`PATCH /rest/customerGroups/{id}`) or creates new groups (`POST /rest/customerGroups`).
- Automatically links every customer record back to their assigned group via `customers.customerGroupsId`.

### 4. Neighborhood Locality Profiling (`core/locality_scorer.py`)
- **Hyperlocal Intelligence:** Evaluates the store's physical vicinity using Google Maps review data collected via the **Apify Google Maps Scraper Actor** (`nwua9Gu5YrADL7ZDj`).
- **Signal Extraction:** Evaluates review texts against 6 neighborhood personas:
  - `tourist` (homestays, trekking, hill station, monastery)
  - `local_food` (thukpa, momos, dhabas, authentic cuisine)
  - `office_worker` (IT parks, tech, corporate, coworking)
  - `family` (schools, playgrounds, residential, safe)
  - `budget` (affordable, cheap, value, pocket friendly)
  - `premium` (luxury, upscale, fine dining, expensive)
- **Caching Mechanism:** Results are cached in `locality_cache.json` with a 7-day TTL (`CACHE_DAYS = 7`) to minimize external API costs.
- **Locality Boost:** Calculates a 0.0–1.0 boost for every offer based on its category alignment.

### 5. Autonomous Environmental & Cultural AI Campaigns (`core/ai_marketer.py` & `context_fetcher.py`)
- **Environmental Signal:** Queries **Open-Meteo API** using store GPS coordinates (`lat`, `lon`) and categorizes WMO codes into events like `RAIN`, `HOT_SUMMER`, or `COLD_SNAP`.
- **Cultural Signal:** Queries **Calendarific API** for active Indian state or national festivals happening today (e.g. `HOLI`, `DIWALI`).
- **Autonomous Campaign Generation:** Feeds environmental & cultural vectors into **Google Gemini 2.5 Flash** with strict JSON schema constraints. The model designs a context-aware promotional offer (e.g., *"Monsoon Chai Fest"* or *"Summer Heatwave Chill"*).
- **Auto-Injection:** Automatically creates the generated offer in Twenty CRM (`POST /rest/offers`) so it immediately participates in the day's recommendation loop.

### 6. XGBoost Offer Recommendation Engine (`core/recommender.py`)
- **Model:** Tuned `XGBClassifier` configured with multi-class softprob output (`objective="multi:softprob"`, `n_estimators=150`, `max_depth=5`, `learning_rate=0.1`).
- **Dynamic Training:** Synthesizes training patterns reflecting Kirana retail purchase behavior across active offers.
- **Prediction & Confidence Blending:** Generates probability distributions for each customer.
  - Base ML confidence is combined with the hyper-local neighborhood boost:
    $$\text{Final Confidence} = (\text{Base ML Confidence} \times 0.6) + (\text{Locality Boost} \times 0.4)$$
- **Fallback Safeguard:** If the model's confidence is weak (< 35%), it falls back to safe generic coupons (`ALL_CUSTOMERS` or `New`).
- **Deduplication Cache:** Checks existing entries in Twenty CRM's `customeroffers` table. Duplicate recommendations for the same customer/offer pair are skipped.

### 7. Behavior Drift Detection & Win-Back Triggers (`core/offer_generator.py`)
- **Historical Comparison:** Reads previous customer state from `rfm_snapshot.json`.
- **Drift Scoring Formula:**
  - **Tier Drop:** $+2 \times (\text{Previous Tier} - \text{Current Tier})$.
  - **Recency Spike:** $+2$ points if inactivity increased by $\ge 14$ days.
  - **Spend Contraction:** $+2$ points if monetary spend dropped by $> 10\%$.
- **Trigger A Execution:** If `drift_score >= 4`, the customer is flagged for **Severe Behavior Drift**:
  - The standard ML model is **overridden**.
  - A specialized win-back offer is triggered (e.g., `VIP_to_At Risk` $\rightarrow$ *"VIP Urgent Intervention"*, 25% cashback).
  - Confidence is forced to `0.99`.
  - Recommendation reason is logged as: `"Trigger A: Severe behavior drift detected (RFM/Spend Drop)"`.
- **Daily State Snapshot:** Saves today's RFM state into `rfm_snapshot.json` at the conclusion of the run.

---

## ⚠️ Critical Notice: Webhook Dispatch Architecture

> [!WARNING]
> ### 🚨 Dual Webhook Execution Flag (Single + Group)
> Inside [core/webhook.py](file:///mnt/data/NEAI/Recommendation-system-for-kirana-stores/core/webhook.py) (invoked at the conclusion of [engine.py](file:///mnt/data/NEAI/Recommendation-system-for-kirana-stores/engine.py#L276)), the engine **concurrently fires BOTH single and group webhooks in every execution**:
>
> 1. **Single Webhook (`WEBHOOK_URL_SINGLE`)**: Fires an HTTP POST request for **every individual customer** receiving a recommendation.
> 2. **Group Webhook (`WEBHOOK_URL_GROUP`)**: In the **exact same run**, if 2 or more customers receive the same offer, a **second** HTTP POST request is fired containing the entire batch of customers.

### Potential Side Effects
If your downstream automation tool (e.g., n8n, Zapier, Twilio, Gupshup, Meta WhatsApp Cloud API) is listening to both webhooks simultaneously, **customers may receive duplicate SMS or WhatsApp messages**:
- 1 message via the single customer webhook.
- 1 message via the group broadcast webhook.

### How to Configure or Disable One
Open [core/webhook.py](file:///mnt/data/NEAI/Recommendation-system-for-kirana-stores/core/webhook.py#L68-L90):

```python
# To disable Single Webhooks and ONLY send Group Webhooks:
# Comment out lines 69-75 in core/webhook.py:
# for c in group:
#     fire_single_webhook(...)

# OR to disable Group Webhooks and ONLY send Individual Webhooks:
# Comment out lines 78-89 in core/webhook.py:
# if len(group) >= 2:
#     fire_group_webhook(...)
```

#### Webhook Payload Formats

**Single Webhook Payload (`WEBHOOK_URL_SINGLE`):**
```json
{
  "type": "single",
  "customer": {
    "name": "Akshat Jain",
    "email": "akshat@test.com",
    "phone": "+919876543210",
    "segment": "VIP",
    "confidence": 0.88
  },
  "offer": {
    "offer_name": "20% Off Electronics",
    "offer_type": "DISCOUNT",
    "discount": 20
  }
}
```

**Group Webhook Payload (`WEBHOOK_URL_GROUP`):**
```json
{
  "type": "group",
  "offer": {
    "offer_name": "Free Shipping on Food",
    "offer_type": "FREE_SHIPPING",
    "discount": 0
  },
  "group_size": 3,
  "customers": [
    {
      "name": "Akshat Jain",
      "email": "akshat@test.com",
      "phone": "+919876543210",
      "segment": "VIP",
      "confidence": 0.88
    },
    {
      "name": "Neha Sharma",
      "email": "neha@test.com",
      "phone": "+919876543211",
      "segment": "New",
      "confidence": 0.82
    }
  ]
}
```

---

## 🚀 Step-by-Step Execution Guide

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

### 3. Seed Initial CRM Data
If starting with a blank Twenty CRM database, run the seeding scripts:
```bash
# 1. Seed baseline offer catalog
python scripts/populate_offers.py

# 2. Seed test customer profiles and telemetry purchases
python scripts/populate.py
```

### 4. Run the Recommendation Pipeline
Execute the main orchestrator:
```bash
python engine.py
```

### 5. Simulate Behavior Drift (Testing Win-Backs)
To test Trigger A (sabotaging customer RFM metrics to trigger automated win-backs):
```bash
python drift_stimulator.py
python engine.py
```

---

## 📁 Repository Structure

```
├── core/
│   ├── ai_marketer.py        # Gemini 2.5 Flash autonomous campaign generator
│   ├── config.py             # Central configuration, mappings, and thresholds
│   ├── data_fetcher.py       # Twenty CRM REST API wrapper with rate-limit pacing
│   ├── feature_engineer.py   # O(N+M) customer RFM and telemetry feature builder
│   ├── group_sync.py         # Customer segment aggregation & Twenty CRM group sync
│   ├── locality_scorer.py    # Apify Google Maps reviews scraper & neighborhood profiling
│   ├── offer_generator.py    # Behavior drift scoring & recovery offer matrix
│   ├── recommender.py        # XGBoost multi-class classifier & confidence scorer
│   ├── segmentation.py       # KMeans clustering customer segmenter
│   └── webhook.py            # Dual webhook dispatcher (Single + Group)
├── scripts/
│   ├── ondc-search.js        # ONDC protocol gateway search integration
│   ├── populate.py           # Injects test customers & purchases into Twenty CRM
│   └── populate_offers.py    # Seeds initial baseline offers catalog
├── utils/
│   └── twenty_crm_schema.json# Twenty CRM schema reference
├── context_fetcher.py        # Open-Meteo weather & Calendarific holiday fetcher
├── drift_stimulator.py       # Test utility to simulate customer engagement drops
├── engine.py                 # Main application pipeline entrypoint
├── locality_cache.json       # 7-day cache for neighborhood scores
├── rfm_snapshot.json         # Daily RFM customer snapshot for drift detection
├── .env.example              # Template environment variables
├── .gitignore                # Git ignore patterns
├── requirements.txt          # Python dependency specifications
└── README.md                 # Project documentation
```
