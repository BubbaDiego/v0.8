# xcom/xcom_core.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from xcom.xcom_config_service import XComConfigService
from xcom.email_service import EmailService
from xcom.sms_service import SMSService
from xcom.voice_service import VoiceService
from xcom.sound_service import SoundService
from utils.console_logger import ConsoleLogger as log

class XComCore:
    def __init__(self, dl_sys_data_manager):
        self.config_service = XComConfigService(dl_sys_data_manager)
        self.log = []

    def send_notification(self, level: str, subject: str, body: str, recipient: str = ""):
        email_cfg = self.config_service.get_provider("email")
        sms_cfg = self.config_service.get_provider("sms")
        voice_cfg = self.config_service.get_provider("twilio")

        results = {"email": False, "sms": False, "voice": False, "sound": False}

        if level == "HIGH":
            results["sms"] = SMSService(sms_cfg).send(recipient, body)
            results["voice"] = VoiceService(voice_cfg).call(recipient, body)
            results["sound"] = SoundService().play()
        elif level == "MEDIUM":
            results["sms"] = SMSService(sms_cfg).send(recipient, body)
        else:
            results["email"] = EmailService(email_cfg).send(recipient, subject, body)

        self.log.append({
            "level": level,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "results": results
        })

        log.info("Notification dispatched", source="XComCore", payload=results)
        return results
