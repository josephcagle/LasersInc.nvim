
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
        self.music = {
            "main_menu": "data/sound/LasersIncMenu.mp3"
        }

    def play_sound(self, sound_name):
        if sound_name not in self.sounds:
            raise RuntimeError(f"sound not found: {sound_name}")
        mixer.Sound.play(self.sounds[sound_name])

    def load_music(self, music_name):
        mixer.music.load(self.music[music_name])
    def play_music(self, loop=False):
        mixer.music.play(-1 if loop else 0)
    def pause_music(self):
        mixer.music.pause()
    def unpause_music(self):
        mixer.music.unpause()
    def is_music_playing(self):
        return mixer.music.get_busy()
    def set_music_volume(self, volume_fraction):
        mixer.music.set_volume(volume_fraction)
    def fade_out_music(self, time_ms):
        mixer.music.fadeout(time_ms)  # blocking

