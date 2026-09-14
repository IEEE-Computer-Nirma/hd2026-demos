"""ML training lab — train, compare, and forecast with multiple algorithms."""

import numpy as np
import pandas as pd
import streamlit as st

from utils.db import cortex_complete, load_macro_history

st.title("ML training lab")
st.caption("Train and compare forecasting models on macroeconomic indicators")

with st.spinner("Loading macro history..."):
    raw = load_macro_history()

if raw.empty:
    st.warning("No historical data available.", icon=":material/warning:")
    st.stop()

raw["DATE"] = pd.to_datetime(raw["DATE"])
raw = raw.sort_values("DATE").set_index("DATE")

TARGETS = {
    "Unemployment rate (%)": "UNEMPLOYMENT_RATE",
    "CPI index": "CPI_INDEX",
    "Home price index": "HPI_INDEX",
}


# ----- Configuration -----

st.subheader("1. Configure training", anchor=False)

c1, c2 = st.columns(2)
with c1:
    target_label = st.selectbox("Target indicator", list(TARGETS.keys()))
    compare_mode = st.toggle("Compare all algorithms", value=True)
    if not compare_mode:
        model_name = st.selectbox(
            "Algorithm",
            ["Linear Regression", "Ridge Regression", "Random Forest", "Gradient Boosting"],
        )
with c2:
    n_lags = st.slider("Lag features (months)", 1, 12, 6)
    rolling_window = st.slider("Rolling mean window", 2, 12, 3)
    test_pct = st.slider("Test set %", 10, 40, 20)

forecast_months = st.slider("Forecast horizon (months ahead)", 1, 24, 6)
use_cv = st.toggle("Use cross-validation (5-fold)", value=False)

target_col = TARGETS[target_label]
series = raw[[target_col]].dropna().copy()

if len(series) < n_lags + rolling_window + 24:
    st.error("Not enough data points. Try reducing lags or rolling window.", icon=":material/error:")
    st.stop()


def build_features(df: pd.DataFrame, col: str, n_lags: int, rolling: int) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for lag in range(1, n_lags + 1):
        out[f"lag_{lag}"] = df[col].shift(lag)
    out[f"rolling_mean_{rolling}"] = df[col].rolling(rolling).mean().shift(1)
    out[f"rolling_std_{rolling}"] = df[col].rolling(rolling).std().shift(1)
    out["month"] = df.index.month
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    out["target"] = df[col]
    return out.dropna()


feat_df = build_features(series, target_col, n_lags, rolling_window)

st.caption(f"{len(series)} monthly observations, {feat_df.shape[1] - 1} engineered features")

split_idx = int(len(feat_df) * (1 - test_pct / 100))
train_df = feat_df.iloc[:split_idx]
test_df = feat_df.iloc[split_idx:]

X_train = train_df.drop(columns=["target"])
y_train = train_df["target"]
X_test = test_df.drop(columns=["target"])
y_test = test_df["target"]

st.caption(f"Train: {len(train_df)} rows | Test: {len(test_df)} rows")


# ----- Training -----

if st.button("Train model" + ("s" if compare_mode else ""), type="primary", icon=":material/model_training:"):
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    ALL_MODELS = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42),
    }

    if compare_mode:
        models_to_train = ALL_MODELS
    else:
        models_to_train = {model_name: ALL_MODELS[model_name]}

    results = {}
    predictions = {}

    with st.spinner("Training models..."):
        for name, model in models_to_train.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)

            cv_score = None
            if use_cv:
                from sklearn.model_selection import cross_val_score
                cv_scores = cross_val_score(
                    model.__class__(**model.get_params()),
                    feat_df.drop(columns=["target"]),
                    feat_df["target"],
                    cv=5,
                    scoring="neg_mean_absolute_error",
                )
                cv_score = -cv_scores.mean()

            results[name] = {"MAE": mae, "RMSE": rmse, "R²": r2, "CV MAE": cv_score, "model": model}
            predictions[name] = y_pred


    # ----- Model comparison table -----

    st.subheader("2. Model comparison", anchor=False)

    comparison_rows = []
    for name, metrics in results.items():
        row = {"Algorithm": name, "MAE": f"{metrics['MAE']:.4f}", "RMSE": f"{metrics['RMSE']:.4f}", "R²": f"{metrics['R²']:.4f}"}
        if use_cv:
            row["CV MAE (5-fold)"] = f"{metrics['CV MAE']:.4f}" if metrics["CV MAE"] else "N/A"
        comparison_rows.append(row)

    comparison_df = pd.DataFrame(comparison_rows)
    st.dataframe(comparison_df, hide_index=True, use_container_width=True)

    # Pick best model by R²
    best_name = max(results, key=lambda k: results[k]["R²"])
    best_model = results[best_name]["model"]
    best_pred = predictions[best_name]

    if compare_mode:
        st.caption(f"Best model by R²: **{best_name}**")


    # ----- Actual vs Predicted -----

    st.subheader("3. Actual vs predicted (test set)", anchor=False)

    if compare_mode:
        compare_chart = pd.DataFrame({"Actual": y_test.values}, index=y_test.index)
        for name, pred in predictions.items():
            compare_chart[name] = pred
        st.line_chart(compare_chart, use_container_width=True)
    else:
        compare_chart = pd.DataFrame(
            {"Actual": y_test.values, "Predicted": best_pred},
            index=y_test.index,
        )
        st.line_chart(compare_chart, use_container_width=True)


    # ----- Residual analysis -----

    st.subheader("4. Residual analysis", anchor=False)
    st.caption(f"Residuals for {best_name}")

    residuals = y_test.values - best_pred
    residual_df = pd.DataFrame({
        "Predicted": best_pred,
        "Residual": residuals,
    }, index=y_test.index)

    rc1, rc2 = st.columns(2)
    with rc1:
        with st.container(border=True):
            st.markdown("**Residuals over time**")
            st.bar_chart(pd.DataFrame({"Residual": residuals}, index=y_test.index), use_container_width=True)
    with rc2:
        with st.container(border=True):
            st.markdown("**Residual statistics**")
            st.metric("Mean residual", f"{residuals.mean():.4f}", border=True)
            st.metric("Std residual", f"{residuals.std():.4f}", border=True)
            st.metric("Max |residual|", f"{np.abs(residuals).max():.4f}", border=True)


    # ----- Feature importance -----

    if hasattr(best_model, "feature_importances_"):
        st.subheader("5. Feature importance", anchor=False)
        fi = pd.Series(best_model.feature_importances_, index=X_train.columns).sort_values(ascending=True)
        st.bar_chart(fi.tail(10), use_container_width=True, horizontal=True)


    # ----- Forecast with confidence intervals -----

    st.subheader("6. Forecast with confidence bands", anchor=False)

    full_series = series[target_col].copy()
    forecast_dates = pd.date_range(
        start=full_series.index[-1] + pd.DateOffset(months=1),
        periods=forecast_months,
        freq="MS",
    )

    # Bootstrap confidence intervals (if tree-based model)
    n_bootstrap = 50 if hasattr(best_model, "feature_importances_") else 0

    if n_bootstrap > 0:
        all_forecasts = []
        for b in range(n_bootstrap):
            boot_idx = np.random.choice(len(X_train), size=len(X_train), replace=True)
            X_boot = X_train.iloc[boot_idx]
            y_boot = y_train.iloc[boot_idx]
            boot_model = best_model.__class__(**best_model.get_params())
            boot_model.fit(X_boot, y_boot)

            fc_vals = []
            extended = full_series.copy()
            for fdate in forecast_dates:
                row = {}
                ext = pd.concat([extended, pd.Series(fc_vals, index=forecast_dates[: len(fc_vals)])])
                for lag in range(1, n_lags + 1):
                    row[f"lag_{lag}"] = ext.iloc[-lag]
                recent = ext.iloc[-rolling_window:]
                row[f"rolling_mean_{rolling_window}"] = recent.mean()
                row[f"rolling_std_{rolling_window}"] = recent.std()
                row["month"] = fdate.month
                row["month_sin"] = np.sin(2 * np.pi * fdate.month / 12)
                row["month_cos"] = np.cos(2 * np.pi * fdate.month / 12)
                pred = boot_model.predict(pd.DataFrame([row]))[0]
                fc_vals.append(pred)
            all_forecasts.append(fc_vals)

        all_forecasts = np.array(all_forecasts)
        fc_mean = all_forecasts.mean(axis=0)
        fc_lower = np.percentile(all_forecasts, 10, axis=0)
        fc_upper = np.percentile(all_forecasts, 90, axis=0)
    else:
        fc_vals = []
        for fdate in forecast_dates:
            row = {}
            extended = pd.concat([full_series, pd.Series(fc_vals, index=forecast_dates[: len(fc_vals)])])
            for lag in range(1, n_lags + 1):
                row[f"lag_{lag}"] = extended.iloc[-lag]
            recent = extended.iloc[-rolling_window:]
            row[f"rolling_mean_{rolling_window}"] = recent.mean()
            row[f"rolling_std_{rolling_window}"] = recent.std()
            row["month"] = fdate.month
            row["month_sin"] = np.sin(2 * np.pi * fdate.month / 12)
            row["month_cos"] = np.cos(2 * np.pi * fdate.month / 12)
            pred = best_model.predict(pd.DataFrame([row]))[0]
            fc_vals.append(pred)
        fc_mean = np.array(fc_vals)
        # Use residual std for simple CI
        res_std = residuals.std()
        fc_lower = fc_mean - 1.645 * res_std
        fc_upper = fc_mean + 1.645 * res_std

    hist_tail = full_series.tail(24).rename("Historical")
    forecast_chart = pd.DataFrame({
        "Historical": hist_tail,
    }).join(pd.DataFrame({
        "Forecast": pd.Series(fc_mean, index=forecast_dates),
        "Lower bound (90%)": pd.Series(fc_lower, index=forecast_dates),
        "Upper bound (90%)": pd.Series(fc_upper, index=forecast_dates),
    }), how="outer")
    st.line_chart(forecast_chart, use_container_width=True)
    st.caption(
        f"Forecast extends {forecast_months} months beyond {full_series.index[-1].strftime('%Y-%m')}. "
        f"Confidence bands show 80% prediction interval."
    )


    # ----- AI interpretation -----

    st.subheader("7. AI interpretation", anchor=False)

    with st.spinner("Generating analysis..."):
        direction = "rising" if fc_mean[-1] > fc_mean[0] else "falling"
        best_metrics = results[best_name]
        prompt = (
            f"You are an economist. A {best_name} model was trained to forecast the US "
            f"{target_label}. Test metrics: MAE={best_metrics['MAE']:.4f}, "
            f"RMSE={best_metrics['RMSE']:.4f}, R²={best_metrics['R²']:.4f}. "
            f"The {forecast_months}-month forecast shows a {direction} trend from "
            f"{fc_mean[0]:.2f} to {fc_mean[-1]:.2f}. "
            f"The 80% confidence band at the end spans {fc_lower[-1]:.2f} to {fc_upper[-1]:.2f}. "
        )
        if compare_mode:
            prompt += f"Among 4 algorithms compared, {best_name} had the best R². "
        prompt += (
            "In 3-4 sentences, interpret the model quality, forecast direction, and uncertainty. "
            "Mention caveats about using ML for macro forecasting."
        )
        try:
            interpretation = cortex_complete(prompt)
            with st.container(border=True):
                st.markdown(interpretation)
        except Exception:
            st.caption("AI interpretation unavailable.")


    # ----- Raw data -----

    with st.expander("View feature matrix", icon=":material/table_chart:"):
        st.dataframe(feat_df.sort_index(ascending=False), use_container_width=True)
