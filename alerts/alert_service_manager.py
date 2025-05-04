import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alerts.alert_service import AlertService
from alerts.alert_repository import AlertRepository
from alerts.alert_enrichment_service import AlertEnrichmentService
from xcom.notification_service import NotificationService
from config.config_loader import load_config
from data.data_locker import DataLocker

from config.config_constants import ALERT_LIMITS_PATH
#config_loader = lambda: load_config() or {}
print(f"[CONFIG] ✅ Using alert config: {ALERT_LIMITS_PATH}")



# Singleton pattern for Alert Service Manager
class AlertServiceManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls._create_service()
        return cls._instance

    @classmethod
    def _create_service(cls):
        data_locker = DataLocker.get_instance()
        repo = AlertRepository(data_locker)
        enrichment = AlertEnrichmentService(data_locker)
        config_loader = lambda: load_config("alert_limits.json") or {}
        service = AlertService(repo, enrichment, config_loader)
        service.notification_service = NotificationService(config_loader)
        return service
