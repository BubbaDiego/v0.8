import os
import platform
import shutil
import subprocess

def play_sound():
    # 🎯 Anchor path to script location, not CWD
    script_dir = os.path.dirname(os.path.realpath(__file__))
    sound_path = os.path.join(script_dir, "static", "sounds", "death_nail.mp3")

    print(f"🔍 Looking for: {sound_path}")  # Debug path being used

    if not os.path.isfile(sound_path):
        print(f"❌ File not found: {sound_path}")
        return

    system = platform.system()

    try:
        if system == "Windows":
            import winsound
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)
        elif system == "Darwin":
            if shutil.which("afplay"):
                subprocess.call(["afplay", sound_path])
            else:
                print("❌ 'afplay' not found on macOS")
        else:
            if shutil.which("mpg123"):
                subprocess.call(["mpg123", sound_path])
            elif shutil.which("play"):
                subprocess.call(["play", sound_path])
            else:
                print("❌ No compatible audio player found (mpg123 or play)")
        print("✅ System sound played.")
    except Exception as e:
        print(f"❌ Playback failed: {e}")

if __name__ == "__main__":
    play_sound()
