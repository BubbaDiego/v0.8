# xcom/sound_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import platform
import os
from utils.console_logger import ConsoleLogger as log

class SoundService:
    def __init__(self, sound_file="alert.mp3"):
        self.sound_file = sound_file

    def play(self):
        try:
            system = platform.system()
            if system == "Windows":
                import winsound
                winsound.PlaySound(self.sound_file, winsound.SND_FILENAME)
            elif system == "Darwin":
                os.system(f"afplay {self.sound_file}")
            else:
                os.system(f"mpg123 {self.sound_file}")
            log.success("System sound played", source="SoundService")
        except Exception as e:
            log.error(f"Sound playback failed: {e}", source="SoundService")
