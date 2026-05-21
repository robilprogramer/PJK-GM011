"""
tests/test_ml.py — Unit Test SiagaAI ML Pipeline
=================================================
pytest tests/test_ml.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
from app.services.ml.flood_predictor import (
    flood_predictor, FEATURE_NAMES, CLASS_ORDER,
    SOIL_TYPE_ENCODING, CITY_DEFAULTS
)

# ─── Fixture ──────────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def load_model():
    flood_predictor.ensure_loaded()
    assert flood_predictor._loaded, "Model harus ter-load sebelum test"


# ─── 1. Model Loading ─────────────────────────────────────────
class TestModelLoading:
    def test_model_loaded(self):
        assert flood_predictor._model is not None

    def test_scaler_loaded(self):
        assert flood_predictor._scaler is not None

    def test_encoder_loaded(self):
        assert flood_predictor._le is not None

    def test_metadata_has_keys(self):
        meta = flood_predictor._metadata
        for key in ["model_version", "accuracy", "f1_score_weighted", "feature_names"]:
            assert key in meta, f"Key '{key}' tidak ada di metadata"

    def test_accuracy_acceptable(self):
        acc = flood_predictor._metadata.get("accuracy", 0)
        assert acc >= 0.80, f"Accuracy {acc:.4f} di bawah threshold 0.80"

    def test_f1_acceptable(self):
        f1 = flood_predictor._metadata.get("f1_score_weighted", 0)
        assert f1 >= 0.78, f"F1 {f1:.4f} di bawah threshold 0.78"

    def test_correct_n_features(self):
        assert len(FEATURE_NAMES) == 17
        n = len(flood_predictor._model.feature_importances_)
        assert n == 17, f"Model punya {n} fitur, expected 17"

    def test_class_order(self):
        classes = set(flood_predictor._le.classes_.tolist())
        expected = {"aman", "waspada", "siaga", "awas"}
        assert classes == expected, f"Kelas tidak sesuai: {classes}"


# ─── 2. Feature Engineering ───────────────────────────────────
class TestFeatureEngineering:
    def test_build_features_shape(self):
        X = flood_predictor._build_features(
            10, 25, 60, 80, 27, 3, 1, 50, 3, 0, 0.7
        )
        assert X.shape == (1, 17), f"Shape tidak sesuai: {X.shape}"

    def test_build_features_no_nan(self):
        X = flood_predictor._build_features(
            0, 0, 0, 45, 35, 0, 8, 800, 10, 3, 0.3
        )
        assert not np.isnan(X).any(), "Ada NaN di feature vector"

    def test_rain_intensity_no_rain(self):
        X = flood_predictor._build_features(
            0, 0, 0, 60, 30, 2, 7, 100, 5, 2, 0.5
        )
        # index 11 = rain_intensity
        assert X[0, 11] == 0, "rain_intensity harus 0 jika tidak hujan"

    def test_rain_intensity_extreme(self):
        X = flood_predictor._build_features(
            80, 200, 400, 95, 25, 10, 1, 5, 1, 0, 0.9
        )
        assert X[0, 11] == 4, "rain_intensity harus 4 untuk hujan sangat lebat"

    def test_is_rainy_season_january(self):
        X = flood_predictor._build_features(
            5, 12, 30, 75, 28, 3, 1, 100, 4, 0, 0.6
        )
        # index 7 = is_rainy_season
        assert X[0, 7] == 1, "Januari harus is_rainy_season=1"

    def test_is_rainy_season_july(self):
        X = flood_predictor._build_features(
            1, 2, 5, 55, 32, 2, 7, 200, 6, 2, 0.4
        )
        assert X[0, 7] == 0, "Juli harus is_rainy_season=0"

    def test_drainage_score_range(self):
        X = flood_predictor._build_features(
            10, 25, 60, 80, 27, 3, 5, 100, 3, 0, 0.6
        )
        drainage = X[0, 14]  # index 14 = drainage_score (setelah saturation_index)
        assert 0 <= drainage <= 1, f"drainage_score harus 0-1, dapat {drainage}"


# ─── 3. City Lookup ───────────────────────────────────────────
class TestCityLookup:
    def test_jakarta_found(self):
        r = flood_predictor._get_city_defaults("Jakarta Utara")
        assert r["soil_type_encoded"] == 0   # aluvial
        assert r["elevation_m"] <= 15
        assert r["flood_prone_score"] >= 0.85

    def test_bandung_found(self):
        r = flood_predictor._get_city_defaults("Bandung")
        assert r["elevation_m"] >= 700       # dataran tinggi
        assert r["flood_prone_score"] < 0.55  # tidak terlalu rawan

    def test_unknown_city_fallback(self):
        r = flood_predictor._get_city_defaults("Kota XYZ Tidak Ada")
        assert "elevation_m" in r
        assert "flood_prone_score" in r

    def test_case_insensitive(self):
        r1 = flood_predictor._get_city_defaults("SURABAYA")
        r2 = flood_predictor._get_city_defaults("surabaya")
        assert r1["elevation_m"] == r2["elevation_m"]


# ─── 4. Prediction Correctness ────────────────────────────────
class TestPredictions:
    """Uji prediksi untuk skenario nyata bencana Indonesia."""

    def test_returns_valid_risk_level(self):
        result = flood_predictor.predict(10, 25, 60, 80, 27, 3)
        assert result.risk_level in CLASS_ORDER

    def test_probability_sums_to_one(self):
        result = flood_predictor.predict(20, 50, 100, 85, 26, 5)
        total = sum(result.probabilities.values())
        assert abs(total - 1.0) < 0.001, f"Sum proba = {total}, harus 1.0"

    def test_risk_score_range(self):
        result = flood_predictor.predict(30, 80, 150, 90, 27, 7)
        assert 0.0 <= result.risk_score <= 1.0

    def test_confidence_valid(self):
        result = flood_predictor.predict(5, 10, 25, 70, 28, 2)
        assert result.confidence in ["high", "medium", "low"]

    def test_top_features_count(self):
        result = flood_predictor.predict(40, 100, 200, 92, 26, 8)
        assert 1 <= len(result.top_features) <= 7

    def test_inference_time_fast(self):
        """Inference harus < 500ms"""
        result = flood_predictor.predict(15, 40, 80, 82, 27, 4)
        assert result.inference_ms < 500, f"Inference {result.inference_ms}ms terlalu lambat"

    def test_no_rain_dry_season_aman(self):
        """Kemarau, tidak hujan → harus aman atau waspada"""
        result = flood_predictor.predict(
            rainfall_1h=0, rainfall_3h=0, rainfall_24h=2,
            humidity=55, temperature=34, wind_speed=1.5,
            month=8, city_name="Bandung"
        )
        assert result.risk_level in ["aman", "waspada"], \
            f"Kemarau tanpa hujan tidak boleh {result.risk_level}"

    def test_extreme_rain_high_risk(self):
        """Hujan sangat lebat → harus siaga atau awas"""
        result = flood_predictor.predict(
            rainfall_1h=80, rainfall_3h=200, rainfall_24h=400,
            humidity=97, temperature=25, wind_speed=12,
            month=1, city_name="Jakarta Utara"
        )
        assert result.risk_level in ["siaga", "awas"], \
            f"Hujan ekstrem harus siaga/awas, bukan {result.risk_level}"

    def test_high_elevation_reduces_risk(self):
        """Elevasi sangat tinggi harusnya lebih rendah risikonya"""
        low  = flood_predictor.predict(20, 50, 100, 85, 27, 5, 1, elevation_m=5,   distance_to_river_km=0.5, soil_type_encoded=0)
        high = flood_predictor.predict(20, 50, 100, 85, 27, 5, 1, elevation_m=800, distance_to_river_km=8.0, soil_type_encoded=3)
        # risk_score rendah lebih baik
        assert high.risk_score <= low.risk_score, \
            f"Elevasi tinggi ({high.risk_score}) harusnya <= elevasi rendah ({low.risk_score})"

    def test_gambut_soil_riskier_than_andosol(self):
        """Tanah gambut (1) lebih rawan dari andosol (3)"""
        gambut  = flood_predictor.predict(20, 50, 100, 85, 27, 5, 1, soil_type_encoded=1)
        andosol = flood_predictor.predict(20, 50, 100, 85, 27, 5, 1, soil_type_encoded=3)
        assert gambut.risk_score >= andosol.risk_score, \
            f"Gambut ({gambut.risk_score}) harusnya >= andosol ({andosol.risk_score})"

    def test_actions_not_empty(self):
        result = flood_predictor.predict(50, 130, 250, 94, 25, 9, 1, "Jakarta")
        assert len(result.actions) > 0, "Actions tidak boleh kosong"

    def test_message_not_empty(self):
        result = flood_predictor.predict(5, 12, 30, 72, 29, 2, 9)
        assert len(result.message) > 0

    def test_model_version_in_result(self):
        result = flood_predictor.predict(10, 25, 60, 80, 27, 3)
        assert result.model_version != "unknown"


# ─── 5. Predict from Weather dict ─────────────────────────────
class TestPredictFromWeather:
    def test_basic_weather_dict(self):
        weather = {
            "temperature": 27, "humidity": 85,
            "rainfall_1h": 15, "wind_speed": 4,
        }
        result = flood_predictor.predict_from_weather(weather, city_name="Semarang")
        assert result.risk_level in CLASS_ORDER

    def test_zero_rain_weather(self):
        weather = {
            "temperature": 33, "humidity": 58,
            "rainfall_1h": 0, "wind_speed": 2,
        }
        result = flood_predictor.predict_from_weather(weather, city_name="Surabaya")
        assert result.risk_level in ["aman", "waspada"]


# ─── 6. Model Info ────────────────────────────────────────────
class TestModelInfo:
    def test_get_model_info_returns_dict(self):
        info = flood_predictor.get_model_info()
        assert isinstance(info, dict)

    def test_model_info_has_required_keys(self):
        info = flood_predictor.get_model_info()
        required = [
            "model_type", "model_version", "accuracy",
            "f1_score_weighted", "feature_names", "class_names", "is_loaded"
        ]
        for k in required:
            assert k in info, f"Key '{k}' tidak ada di model_info"

    def test_model_info_is_loaded_true(self):
        info = flood_predictor.get_model_info()
        assert info["is_loaded"] is True

    def test_feature_names_match(self):
        info = flood_predictor.get_model_info()
        assert info["feature_names"] == FEATURE_NAMES


# ─── 7. Input Validation (boundary) ──────────────────────────
class TestInputValidation:
    def test_zero_rainfall(self):
        """Semua rainfall = 0 tidak boleh crash"""
        result = flood_predictor.predict(0, 0, 0, 50, 32, 1)
        assert result is not None

    def test_max_rainfall_capped(self):
        """Rainfall sangat besar harus di-cap, tidak error"""
        result = flood_predictor.predict(9999, 9999, 9999, 100, 20, 30)
        assert result.risk_level == "awas"

    def test_month_default_not_none(self):
        """month=None harus pakai bulan saat ini"""
        result = flood_predictor.predict(10, 25, 60, 80, 27, 3, month=None)
        assert result is not None

    def test_city_name_empty_string(self):
        """city_name kosong tidak boleh crash"""
        result = flood_predictor.predict(10, 25, 60, 80, 27, 3, city_name="")
        assert result is not None


if __name__ == "__main__":
    import subprocess
    subprocess.run(["pytest", __file__, "-v", "--tb=short"])
