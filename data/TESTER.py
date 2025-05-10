import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.calc_services import calculate_travel_percent

def run_travel_percent_tests():
    print("\n🚀 Travel Percent Test Suite\n")

    test_cases = [
        # 💥 LONG - liquidation zone
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 75,  "expected": -50.0},
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 50,  "expected": -100.0},

        # 🚀 LONG - profit range
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 125, "expected": 50.0},
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 150, "expected": 100.0},
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 200, "expected": 200.0},
        {"pos": "LONG", "ep": 100, "lp": 50,  "cp": 500, "expected": 800.0},

        # 💥 SHORT - liquidation zone
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 125, "expected": -50.0},
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 150, "expected": -100.0},

        # 🚀 SHORT - profit range
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 75,  "expected": 50.0},
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 50,  "expected": 100.0},
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 25,  "expected": 150.0},
        {"pos": "SHORT", "ep": 100, "lp": 150, "cp": 0,   "expected": 200.0},
    ]

    for i, case in enumerate(test_cases, 1):
        actual = calculate_travel_percent(
            entry_price=case["ep"],
            current_price=case["cp"],
            liquidation_price=case["lp"],
            position_type=case["pos"]
        )

        status = "✅ PASS" if round(actual, 2) == case["expected"] else "❌ FAIL"
        print(f"{status} | Test {i}: {case['pos']} | EP={case['ep']} CP={case['cp']} LP={case['lp']} → TP={actual:.2f}% (expected {case['expected']}%)")

if __name__ == "__main__":
    run_travel_percent_tests()
