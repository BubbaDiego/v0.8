# test_calc_services_totals.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.calc_services import CalcServices

def test_calculate_totals():
    svc = CalcServices()

    # 🧪 Sample synthetic positions
    test_positions = [
        {
            "size": 1000,
            "value": 1200,
            "collateral": 400,
            "leverage": 2.5,
            "travel_percent": 50,
            "heat_index": 60
        },
        {
            "size": 500,
            "value": 700,
            "collateral": 200,
            "leverage": 2.0,
            "travel_percent": 30,
            "heat_index": 30
        },
        {
            "size": 0,  # simulate edge case
            "value": 0,
            "collateral": 0,
            "leverage": 0,
            "travel_percent": 0,
            "heat_index": 0
        }
    ]

    totals = svc.calculate_totals(test_positions)

    # 🧠 Expected values
    expected = {
        "total_size": 1500,
        "total_value": 1900,
        "total_collateral": 600,
        "avg_leverage": ((2.5 * 1000) + (2.0 * 500)) / 1500,
        "avg_travel_percent": ((50 * 1000) + (30 * 500)) / 1500,
        "avg_heat_index": (60 + 30) / 2
    }

    # ✅ Assertions
    def assert_approx(actual, expected, field, tolerance=0.01):
        assert abs(actual - expected) < tolerance, f"❌ {field} mismatch: {actual} vs {expected}"
        print(f"✅ {field}: {actual:.2f} ✅")

    assert_approx(totals["total_size"], expected["total_size"], "total_size")
    assert_approx(totals["total_value"], expected["total_value"], "total_value")
    assert_approx(totals["total_collateral"], expected["total_collateral"], "total_collateral")
    assert_approx(totals["avg_leverage"], expected["avg_leverage"], "avg_leverage")
    assert_approx(totals["avg_travel_percent"], expected["avg_travel_percent"], "avg_travel_percent")
    assert_approx(totals["avg_heat_index"], expected["avg_heat_index"], "avg_heat_index")

    print("🎯 All tests passed!")

if __name__ == "__main__":
    test_calculate_totals()
