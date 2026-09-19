"""
Train a flood damage cause classifier on FEMA NFIP claim data.

Dataset: SNOWFLAKE_PUBLIC_DATA_FREE → FEMA National Flood Insurance Program Claims
         (~2.6M claims, 4 target classes of flood cause)

Task:    Predict DAMAGE_CAUSE from property/claim features.
Model:   Random Forest (scikit-learn)

Run:     Execute sql/setup.sql first, then run this script in a Snowflake
         workspace or locally with snowflake-connector-python.
"""

import json
import warnings

import numpy as np
import pandas as pd
from snowflake.snowpark.context import get_active_session

warnings.filterwarnings("ignore")

# ── 1. Load data from Snowflake ──────────────────────────────────────────────

print("Connecting to Snowflake...")
session = get_active_session()

print("Loading FEMA flood claim features (sampled to 200K for speed)...")
df = session.sql("""
    SELECT *
    FROM LLM_CHAT_LAB_DB.ML.FLOOD_CLAIM_FEATURES
    SAMPLE (200000 ROWS)
""").to_pandas()

print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")
print(f"\nTarget distribution:\n{df['DAMAGE_CAUSE'].value_counts()}\n")

# ── 2. Feature engineering ───────────────────────────────────────────────────

from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

TARGET = "DAMAGE_CAUSE"

NUMERIC_COLS = [
    "WATER_DEPTH_FT", "WATER_DURATION_HRS", "PROPERTY_VALUE",
    "DAMAGE_AMOUNT", "CONTENTS_VALUE", "CONTENTS_DAMAGE",
    "INSURANCE_COVERAGE", "CONTENTS_COVERAGE", "DEDUCTIBLE",
    "ELEVATION_DIFF", "DAMAGE_RATIO", "COVERAGE_RATIO",
    "LAT", "LON", "LOSS_MONTH", "LOSS_YEAR", "BUILDING_AGE_YRS",
]

CATEGORICAL_COLS = [
    "OCCUPANCY_TYPE", "NUMBER_OF_FLOORS", "BUILDING_TYPE",
    "REPLACEMENT_COST_BASIS", "CURRENT_FLOOD_ZONE", "BASEMENT_TYPE",
    "STATE_GEO",
]

# Fill NaN in numerics
for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Encode categoricals with OrdinalEncoder (handles unseen gracefully)
cat_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
for col in CATEGORICAL_COLS:
    df[col] = df[col].fillna("Unknown").astype(str)

df[CATEGORICAL_COLS] = cat_encoder.fit_transform(df[CATEGORICAL_COLS])

# Encode target
label_enc = LabelEncoder()
df["target"] = label_enc.fit_transform(df[TARGET])

FEATURE_COLS = NUMERIC_COLS + CATEGORICAL_COLS
X = df[FEATURE_COLS].values
y = df["target"].values

print(f"Features: {len(FEATURE_COLS)}")
print(f"Classes:  {list(label_enc.classes_)}")

# ── 3. Train/test split ─────────────────────────────────────────────────────

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── 4. Train Random Forest ──────────────────────────────────────────────────

from sklearn.ensemble import RandomForestClassifier

print("\nTraining Random Forest (200 trees, max_depth=20)...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    min_samples_leaf=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)
print("Training complete.")

# ── 5. Evaluate ──────────────────────────────────────────────────────────────

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n{'='*60}")
print(f"  TEST ACCURACY: {accuracy:.4f} ({accuracy*100:.1f}%)")
print(f"{'='*60}")

print("\nClassification Report:")
print(classification_report(
    y_test, y_pred,
    target_names=label_enc.classes_,
    digits=3,
))

print("Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
cm_df = pd.DataFrame(
    cm,
    index=[f"True: {c}" for c in label_enc.classes_],
    columns=[f"Pred: {c}" for c in label_enc.classes_],
)
print(cm_df.to_string())

# ── 6. Feature importance ───────────────────────────────────────────────────

importances = model.feature_importances_
feat_imp = pd.DataFrame({
    "feature": FEATURE_COLS,
    "importance": importances,
}).sort_values("importance", ascending=False)

print(f"\nTop 10 Feature Importances:")
print(feat_imp.head(10).to_string(index=False))

# ── 7. Save model artifacts ─────────────────────────────────────────────────

import pickle

artifacts = {
    "model": model,
    "label_encoder": label_enc,
    "cat_encoder": cat_encoder,
    "feature_cols": FEATURE_COLS,
    "numeric_cols": NUMERIC_COLS,
    "categorical_cols": CATEGORICAL_COLS,
    "accuracy": accuracy,
    "class_names": list(label_enc.classes_),
    "feature_importances": feat_imp.to_dict(orient="records"),
}

model_path = "/tmp/flood_claim_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(artifacts, f)

print(f"\nModel saved to {model_path}")
print(f"Artifact size: {round(len(open(model_path, 'rb').read()) / 1024 / 1024, 1)} MB")

# ── 8. Quick prediction demo ────────────────────────────────────────────────

print(f"\n{'='*60}")
print("  DEMO: Predict damage cause for a sample claim")
print(f"{'='*60}")

sample = X_test[0:1]
pred_class = label_enc.inverse_transform(model.predict(sample))[0]
pred_proba = model.predict_proba(sample)[0]

print(f"Predicted cause: {pred_class}")
print(f"Probabilities:")
for cls, prob in zip(label_enc.classes_, pred_proba):
    bar = "#" * int(prob * 40)
    print(f"  {cls:45s} {prob:.3f} {bar}")

print("\nDone. Model is ready for integration with the chat app.")
