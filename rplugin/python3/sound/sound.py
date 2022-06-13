
import importlib
SOUND_SUPPORTED = importlib.util.find_spec("playsound") is not None
if SOUND_SUPPORTED:
    import playsound

class SoundManager:
    def __init__(self):
        if not SOUND_SUPPORTED:
            raise RuntimeError("sound not supported: playsound module not available")
        self.sounds = {
            "shoot_bullet": "data/sound/shoot_bullet.wav"
        }

    def play_sound(self, sound_name):
        if sound_name not in self.sounds:
            raise RuntimeError(f"sound not found: {sound_name}")
        playsound.playsound(self.sounds[sound_name], False)

