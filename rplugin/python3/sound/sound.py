
import importlib
SOUND_SUPPORTED = importlib.util.find_spec("pygame") is not None
if SOUND_SUPPORTED:
    from pygame import mixer
    mixer.init()

class SoundManager:
    def __init__(self):
        if not SOUND_SUPPORTED:
            raise RuntimeError("sound not supported: playsound module not available")
        self.sounds = {
            "shoot_bullet": mixer.Sound("data/sound/shoot_bullet.wav"),
            "explosion1": mixer.Sound("data/sound/explosion1.wav")
        }

    def play_sound(self, sound_name):
        if sound_name not in self.sounds:
            raise RuntimeError(f"sound not found: {sound_name}")
        mixer.Sound.play(self.sounds[sound_name])

