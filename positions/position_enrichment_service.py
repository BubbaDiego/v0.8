import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.calc_services import CalcServices
from core.logging import log
from core.constants import DB_PATH
from data.data_locker import DataLocker
from utils.fuzzy_wuzzy import fuzzy_match_key

class PositionEnrichmentService:
    def __init__(self, data_locker=None):
        self.dl = data_locker


    def enrich(self, position):
        from utils.calc_services import CalcServices
        from core.logging import log
        from utils.fuzzy_wuzzy import fuzzy_match_key

        calc = CalcServices()
        pos_id = position.get('id', 'UNKNOWN')
        asset = position.get('asset_type', '??')

        log.info(f"\n📥 Enriching position [{pos_id}] — Asset: {asset}", source="Enrichment")

        try:
            # Step 1: Field defaults
            defaults = {
                'entry_price': 0.0,
                'current_price': position.get('entry_price', 0.0),
                'liquidation_price': 0.0,
                'collateral': 0.0,
                'size': 0.0,
                'leverage': None,
                'value': 0.0,
                'pnl_after_fees_usd': 0.0,
                'travel_percent': 0.0,
                'liquidation_distance': 0.0,
                'current_heat_index': 0.0
            }
            for k, v in defaults.items():
                position.setdefault(k, v)

            if not position.get("wallet_name"):
                position["wallet_name"] = "Unknown"
                log.warning(f"⚠️ No wallet_name for [{pos_id}] — defaulted", source="Enrichment")

            raw_type = str(position.get("position_type", "")).strip().lower()
            match = fuzzy_match_key(raw_type, {"LONG": None, "SHORT": None}, threshold=60.0)
            position["position_type"] = match.upper() if match else "UNKNOWN"
            if position["position_type"] == "UNKNOWN":
                log.warning(f"⚠️ Cannot reliably enrich UNKNOWN position type for [{pos_id}]", source="Enrichment")

            # Step 2: Validation before coercion
            required_fields = ['entry_price', 'current_price', 'liquidation_price', 'collateral', 'size']
            missing = [k for k in required_fields if position.get(k) is None]
            if missing:
                log.warning(f"⚠️ Missing numeric fields for [{pos_id}]: {missing}", source="Enrichment")

            # Step 3: Safe coercion
            for field in required_fields:
                try:
                    position[field] = float(position.get(field) or 0.0)
                except Exception as e:
                    log.error(f"❌ Failed to coerce field [{field}] for [{pos_id}]: {e}", source="Enrichment")
                    position[field] = 0.0

            # Step 4: Derived field enrichment
            position['value'] = position['size'] * position['current_price']
            position['leverage'] = calc.calculate_leverage(position['size'], position['collateral']) if position['collateral'] > 0 else 0.0
            position['travel_percent'] = calc.calculate_travel_percent(
                position['position_type'],
                position['entry_price'], position['current_price'], position['liquidation_price']
            )
            position['liquidation_distance'] = calc.calculate_liquid_distance(
                position['current_price'], position['liquidation_price']
            )

            try:
                risk = calc.calculate_composite_risk_index(position)
            except Exception as e:
                log.error(f"❌ Risk index calculation failed: {e}", source="calculate_composite_risk_index", payload=position)
                risk = 0.0

            position['heat_index'] = risk
            position['current_heat_index'] = risk

            # Step 5: Market price injection
            latest = self.dl.get_latest_price(asset)
            if latest and 'current_price' in latest:
                position['current_price'] = float(latest['current_price'])
                log.info(f"🌐 Market price injected for {asset}: {position['current_price']}", source="Enrichment")

            log.success(f"✅ Enriched [{pos_id}] complete", source="Enrichment")
            return position

        except Exception as e:
            log.error(f"🔥 Enrichment FAILED for [{pos_id}]: {e}", source="Enrichment")
            return position
