import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.calc_services import CalcServices
from core.logging import log
from core.constants import DB_PATH
#from core.locker_factory import get_locker
from data.data_locker import DataLocker
from utils.fuzzy_wuzzy import fuzzy_match_key

#dl = DataLocker(str(DB_PATH))

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
                'value': 0.0
            }
            for k, v in defaults.items():
                position.setdefault(k, v)

            if not position.get("wallet_name"):
                position["wallet_name"] = "Unknown"
                log.warning(f"⚠️ No wallet_name for [{pos_id}] — defaulted", source="Enrichment")

            raw_type = str(position.get("position_type", "")).strip().lower()
            match = fuzzy_match_key(raw_type, {"LONG": None, "SHORT": None}, threshold=60.0)
            position["position_type"] = match.upper() if match else "UNKNOWN"

            # Step 2: Coercion
            position['entry_price'] = float(position['entry_price'])
            position['current_price'] = float(position['current_price'])
            position['liquidation_price'] = float(position['liquidation_price'])
            position['collateral'] = float(position['collateral'])
            position['size'] = float(position['size'])

            # Step 3: Derived fields
            position['profit'] = calc.calculate_value(position)
            position['leverage'] = calc.calculate_leverage(position['size'], position['collateral']) if position[
                                                                                                            'collateral'] > 0 else None
            position['travel_percent'] = calc.calculate_travel_percent(
                position.get('position_type', ''),
                position['entry_price'], position['current_price'], position['liquidation_price']
            )
            position['liquidation_distance'] = calc.calculate_liquid_distance(
                position['current_price'], position['liquidation_price']
            )
            risk = calc.calculate_composite_risk_index(position)
            position['heat_index'] = risk
            position['current_heat_index'] = risk

            # Step 4: Market enrichment
            latest = self.dl.get_latest_price(asset)
            if latest and 'current_price' in latest:
                position['current_price'] = float(latest['current_price'])
                log.info(f"🌐 Market price injected for {asset}: {position['current_price']}", source="Enrichment")

            log.success(f"✅ Enriched [{pos_id}] complete", source="Enrichment")
            return position

        except Exception as e:
            log.error(f"🔥 Enrichment FAILED for [{pos_id}]: {e}", source="Enrichment")
            return position
