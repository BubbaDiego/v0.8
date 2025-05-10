import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional, List
from core.logging import log
from datetime import datetime

import sqlite3


class CalcServices:
    def __init__(self):
        self.color_ranges = {
            "travel_percent": [(0, 25, "green"), (25, 50, "yellow"), (50, 75, "orange"), (75, 100, "red")],
            "heat_index": [(0, 20, "blue"), (20, 40, "green"), (40, 60, "yellow"), (60, 80, "orange"), (80, 100, "red")],
            "collateral": [(0, 500, "lightgreen"), (500, 1000, "yellow"), (1000, 2000, "orange"), (2000, 10000, "red")]
        }

    def update_calcs_for_cyclone(self, data_locker) -> (list, dict):
        log.banner("Cyclone Calculation Update Started")
        log.start_timer("update_calcs_for_cyclone")

        positions = data_locker.read_positions()
        log.info("Loaded positions", "update_calcs_for_cyclone", {"count": len(positions)})

        updated_positions = self.aggregator_positions(positions, data_locker.db_path)
        totals = self.calculate_totals(updated_positions)

        confirmed_positions = data_locker.read_positions()
        log.success("Cyclone update completed", "update_calcs_for_cyclone", totals)
        log.end_timer("update_calcs_for_cyclone", "update_calcs_for_cyclone")
        return confirmed_positions, totals

    def aggregator_positions(self, positions: List[dict], db_path: str) -> List[dict]:
        log.start_timer("aggregator_positions")
        log.info("Starting aggregation on positions", "aggregator_positions", {"count": len(positions)})

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for pos in positions:
            pos_id = pos.get("id", "UNKNOWN")
            try:
                log.debug(f"Aggregating position {pos_id}", "aggregator_positions", pos)

                position_type = (pos.get("position_type") or "LONG").upper()
                entry_price = float(pos.get("entry_price", 0.0))
                current_price = float(pos.get("current_price", 0.0))
                liquidation_price = float(pos.get("liquidation_price", 0.0))
                collateral = float(pos.get("collateral", 0.0))
                size = float(pos.get("size", 0.0))

                pos["travel_percent"] = self.calculate_travel_percent(position_type, entry_price, current_price, liquidation_price)
                pos["liquidation_distance"] = self.calculate_liquid_distance(current_price, liquidation_price)

                for field, val in [
                    ("travel_percent", pos["travel_percent"]),
                    ("liquidation_distance", pos["liquidation_distance"]),
                    ("current_price", current_price)
                ]:
                    cursor.execute(f"UPDATE positions SET {field} = ? WHERE id = ?", (val, pos_id))

                if entry_price > 0:
                    token_count = size / entry_price
                    pnl = (current_price - entry_price) * token_count if position_type == "LONG" else (entry_price - current_price) * token_count
                else:
                    pnl = 0.0

                pos["value"] = round(collateral + pnl, 2)
                pos["leverage"] = round(size / collateral, 2) if collateral > 0 else 0.0
                heat_index = self.calculate_heat_index(pos) or 0.0
                pos["heat_index"] = pos["current_heat_index"] = heat_index

                cursor.execute("UPDATE positions SET heat_index = ?, current_heat_index = ? WHERE id = ?", (heat_index, heat_index, pos_id))
                cursor.execute("SELECT heat_index, current_heat_index, current_price FROM positions WHERE id = ?", (pos_id,))
                updated_row = cursor.fetchone()

                log.success("Updated DB for position", "aggregator_positions", {
                    "id": pos_id,
                    "heat_index": updated_row[0] if updated_row else None,
                    "current_price": updated_row[2] if updated_row else None
                })

            except Exception as e:
                log.error(f"Error processing position {pos_id}: {e}", "aggregator_positions")

        conn.commit()
        conn.close()
        log.end_timer("aggregator_positions", "aggregator_positions")
        return positions

    def calculate_composite_risk_index(self, position: dict) -> Optional[float]:
        try:
            entry_price = float(position.get("entry_price", 0.0))
            current_price = float(position.get("current_price", 0.0))
            liquidation_price = float(position.get("liquidation_price", 0.0))
            collateral = float(position.get("collateral", 0.0))
            size = float(position.get("size", 0.0))
            leverage = float(position.get("leverage", 0.0))
            position_type = (position.get("position_type") or "LONG").upper()

            if entry_price <= 0 or liquidation_price <= 0 or collateral <= 0 or size <= 0:
                return None

            if abs(entry_price - liquidation_price) < 1e-6:
                return None

            if position_type == "LONG":
                ndl = (current_price - liquidation_price) / (entry_price - liquidation_price)
            else:
                ndl = (liquidation_price - current_price) / (liquidation_price - entry_price)
            ndl = max(0.0, min(ndl, 1.0))

            distance_factor = 1.0 - ndl
            normalized_leverage = leverage / 100.0
            collateral_ratio = min(collateral / size, 1.0)
            risk_collateral_factor = 1.0 - collateral_ratio

            risk_index = (distance_factor ** 0.45) * (normalized_leverage ** 0.35) * (risk_collateral_factor ** 0.20) * 100.0
            risk_index = self.apply_minimum_risk_floor(risk_index, 5.0)

            log.debug("Calculated composite risk index", "calculate_composite_risk_index", {
                "position_id": position.get("id"),
                "risk_index": risk_index
            })

            return round(risk_index, 2)
        except Exception as e:
            log.error(f"Risk index calculation failed: {e}", "calculate_composite_risk_index", position)
            return None

    def calculate_value(self, position):

        value = round(float(position.get("size") or 0.0), 2)
        log.debug("Calculated value", "calculate_value", {"value": value})
        return value

    def calculate_leverage(self, size: float, collateral: float) -> float:
        leverage = round(size / collateral, 2) if size > 0 and collateral > 0 else 0.0
        log.debug("Calculated leverage", "calculate_leverage", {"leverage": leverage})
        return leverage

    def calculate_travel_percent(self, position_type: str, entry_price: float, current_price: float, liquidation_price: float) -> float:
        if entry_price <= 0 or liquidation_price <= 0 or entry_price == liquidation_price:
            log.warning("Invalid price parameters in travel percent", "calculate_travel_percent")
            return 0.0

        ptype = position_type.strip().upper()
        result = 0.0

        try:
            if ptype == "LONG":
                if current_price <= entry_price:
                    denom = entry_price - liquidation_price
                    numer = current_price - entry_price
                    result = (numer / denom) * 100
                else:
                    profit_target = entry_price + (entry_price - liquidation_price)
                    result = ((current_price - entry_price) / (profit_target - entry_price)) * 100
            elif ptype == "SHORT":
                if current_price >= entry_price:
                    result = -((current_price - entry_price) / (liquidation_price - entry_price)) * 100
                else:
                    profit_target = entry_price - (liquidation_price - entry_price)
                    result = ((entry_price - current_price) / (entry_price - profit_target)) * 100
            else:
                log.warning(f"Unknown position type {position_type}", "calculate_travel_percent")
        except Exception as e:
            log.error(f"Failed to calculate travel percent: {e}", "calculate_travel_percent")

        log.debug("Travel percent calculated", "calculate_travel_percent", {"result": result})
        return result

    def calculate_liquid_distance(self, current_price: float, liquidation_price: float) -> float:
        distance = round(abs(liquidation_price - current_price), 2)
        log.debug("Calculated liquidation distance", "calculate_liquid_distance", {"distance": distance})
        return distance

    def calculate_heat_index(self, position: dict) -> Optional[float]:
        try:
            size = float(position.get("size", 0.0))
            leverage = float(position.get("leverage", 0.0))
            collateral = float(position.get("collateral", 0.0))
            if collateral <= 0:
                return None
            hi = (size * leverage) / collateral
            log.debug("Heat index calculated", "calculate_heat_index", {"heat_index": hi})
            return round(hi, 2)
        except Exception as e:
            log.error(f"Failed to calculate heat index: {e}", "calculate_heat_index", position)
            return None

    def calculate_totals(self, positions: List[dict]) -> dict:
        log.info("Calculating totals from positions", "calculate_totals")
        total_size = total_value = total_collateral = total_heat_index = 0.0
        heat_index_count = 0
        weighted_leverage_sum = weighted_travel_percent_sum = 0.0

        for pos in positions:
            size = float(pos.get("size") or 0.0)
            value = float(pos.get("value") or 0.0)
            collateral = float(pos.get("collateral") or 0.0)
            leverage = float(pos.get("leverage") or 0.0)
            travel_percent = float(pos.get("travel_percent") or 0.0)
            heat_index = float(pos.get("heat_index") or 0.0)

            total_size += size
            total_value += value
            total_collateral += collateral
            weighted_leverage_sum += leverage * size
            weighted_travel_percent_sum += travel_percent * size
            if heat_index:
                total_heat_index += heat_index
                heat_index_count += 1

        avg_leverage = weighted_leverage_sum / total_size if total_size > 0 else 0.0
        avg_travel_percent = weighted_travel_percent_sum / total_size if total_size > 0 else 0.0
        avg_heat_index = total_heat_index / heat_index_count if heat_index_count > 0 else 0.0

        totals = {
            "total_size": total_size,
            "total_value": total_value,
            "total_collateral": total_collateral,
            "avg_leverage": avg_leverage,
            "avg_travel_percent": avg_travel_percent,
            "avg_heat_index": avg_heat_index
        }

        log.success("Totals calculated", "calculate_totals", totals)
        return totals

    def apply_minimum_risk_floor(self, risk_index: float, floor: float = 5.0) -> float:
        return max(risk_index, floor)

    def get_color(self, value: float, metric: str) -> str:
        if metric not in self.color_ranges:
            return "white"
        for (lower, upper, color) in self.color_ranges[metric]:
            if lower <= value < upper:
                return color
        return "red"
