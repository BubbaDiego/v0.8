# xcom/voice_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from twilio.rest import Client
from utils.console_logger import ConsoleLogger as log

class VoiceService:
    def __init__(self, config: dict):
        self.config = config

    def call(self, to: str, message: str):
       # if not self.config.get("enabled"):
     #       log.warning("Voice provider disabled", source="VoiceService")
    #        return False

        sid, token, flow = map(self.config.get, ["account_sid", "auth_token", "flow_sid"])
        from_num = self.config.get("default_from_phone")
        to = to or self.config.get("default_to_phone")

        if not all([sid, token, flow, to, from_num]):
            log.error("Missing voice config", source="VoiceService")
            return False

        try:
            client = Client(sid, token)
            execution = client.studio.v2.flows(flow).executions.create(
                to=to, from_=from_num, parameters={"custom_message": message}
            )
            log.success("Voice call initiated", source="VoiceService", payload={"sid": execution.sid})
            return execution.sid
        except Exception as e:
            log.error(f"Voice call failed: {e}", source="VoiceService")
            return False
