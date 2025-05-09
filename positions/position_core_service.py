import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.calc_services import CalcServices
from core.logging import log

class PositionCoreService:
    def __init__(self, data_locker):
        self.dl = data_locker

    def get_all_positions(self):
        log.debug("🔍 Starting get_all_positions()", source="PositionCoreService")
        try:
            raw_positions = self.dl.read_positions()
            log.info(f"📦 Pulled {len(raw_positions)} raw positions from DB", source="PositionCoreService")
            positions = []

            for i, pos in enumerate(raw_positions):
                try:
                    pos_dict = {key: pos[key] for key in pos.keys()}
                    log.debug(f"🔄 Enriching pos: {pos_dict.get('id')}...", source="PositionCoreService")
                    enriched = self.enrich_position(pos_dict)

                    wallet_name = enriched.get("wallet_name")
                    wallet = self.dl.wallets.get_wallet_by_name(wallet_name) if wallet_name else None
                    if not wallet:
                        log.warning(f"❓ No wallet found for name: {wallet_name}", source="PositionCoreService")
                    enriched["wallet"] = wallet

                    positions.append(enriched)
                    log.success(f"✅ Enriched: {enriched.get('id')}", source="PositionCoreService")
                except Exception as e:
                    log.error(f"❌ Failed to enrich pos {pos.get('id')} — {e}", source="PositionCoreService")
                    continue

            log.success(f"🎯 Returning {len(positions)} positions to viewer", source="PositionCoreService")
            return positions
        except Exception as e:
            log.error(f"❌ Fatal error in get_all_positions(): {e}", source="PositionCoreService")
            return []

    def enrich_position(self, position):
        calc = CalcServices()
        fields = ['entry_price', 'current_price', 'liquidation_price', 'collateral', 'size']
        for f in fields:
            if position.get(f) is None:
                position[f] = position.get('entry_price', 0.0) if f == 'current_price' else 0.0

        try:
            position['entry_price'] = float(position['entry_price'])
            position['current_price'] = float(position['current_price'])
            position['liquidation_price'] = float(position['liquidation_price'])
            position['collateral'] = float(position['collateral'])
            position['size'] = float(position['size'])
        except Exception as e:
            log.warning(f"⚠️ Failed to convert numeric fields: {e}", source="PositionCoreService")

        try:
            position['profit'] = calc.calculate_value(position)
            position['leverage'] = calc.calculate_leverage(position['size'], position['collateral']) if position['collateral'] > 0 else None
            position['travel_percent'] = calc.calculate_travel_percent(
                position.get('position_type', ''), position['entry_price'], position['current_price'], position['liquidation_price']
            )
            position['liquidation_distance'] = calc.calculate_liquid_distance(
                position['current_price'], position['liquidation_price']
            )
            composite_risk = calc.calculate_composite_risk_index(position)
            position['heat_index'] = composite_risk
            position['current_heat_index'] = composite_risk
        except Exception as e:
            log.error(f"❌ Error enriching position {position.get('id')}: {e}", source="PositionCoreService")

        return position

    def clear_positions(self):
        try:
            cursor = self.dl.db.get_cursor()
            cursor.execute("DELETE FROM positions")
            self.dl.db.commit()
            cursor.close()
            log.success("🧹 Positions table cleared", source="PositionCoreService")
        except Exception as e:
            log.error(f"❌ Clear positions failed: {e}", source="PositionCoreService")

    def fill_positions_with_latest_price(self, positions):
        for pos in positions:
            asset = pos.get('asset_type')
            if asset:
                latest = self.dl.get_latest_price(asset)
                if latest and 'current_price' in latest:
                    try:
                        pos['current_price'] = float(latest['current_price'])
                    except Exception as e:
                        log.warning(f"⚠️ Couldn't parse latest price for {asset}: {e}", source="PositionCoreService")
        return positions

    def update_position_and_alert(self, pos):
        try:
            self.dl.positions.create_position(pos)
            from alerts.alert_evaluator import AlertEvaluator
            evaluator = AlertEvaluator({}, self.dl)
            evaluator.update_alert_for_position(pos)
            log.success(f"✅ Updated position & alert: {pos.get('id')}", source="PositionCoreService")
        except Exception as e:
            log.error(f"❌ update_position_and_alert failed: {e}", source="PositionCoreService")

    def delete_position_and_cleanup(self, position_id: str):
        try:
            from alerts.alert_controller import AlertController
            alert_ctrl = AlertController()

            alerts = self.dl.get_alerts()
            alerts_deleted = 0
            for alert in alerts:
                if alert.get("position_reference_id") == position_id:
                    if alert_ctrl.delete_alert(alert["id"]):
                        alerts_deleted += 1
            log.success(f"🗑 Deleted {alerts_deleted} alerts for position {position_id}", source="PositionCoreService")

            cursor = self.dl.db.get_cursor()
            cursor.execute("UPDATE positions SET hedge_buddy_id = NULL WHERE hedge_buddy_id = ?", (position_id,))
            self.dl.db.commit()
            cursor.close()
            log.success(f"💣 Cleared hedge_buddy_id for {position_id}", source="PositionCoreService")

            self.dl.delete_position(position_id)
            log.success(f"✅ Deleted position {position_id}", source="PositionCoreService")

        except Exception as ex:
            log.error(f"❌ Error during delete_position_and_cleanup: {ex}", source="PositionCoreService")

    def record_positions_snapshot(self):
        try:
            positions = self.dl.read_positions()
            calc = CalcServices()
            totals = calc.calculate_totals(positions)
            self.dl.record_positions_totals_snapshot(totals)
            log.success(f"📋 Snapshot of {len(positions)} positions recorded.", source="PositionCoreService")
        except Exception as e:
            log.error(f"❌ record_positions_snapshot failed: {e}", source="PositionCoreService")
