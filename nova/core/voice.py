import sys
import threading
import numpy as np
from rich.console import Console

console = Console()


class VoiceEngine:
    def __init__(self, config):
        self.config = config
        self.recognizer = None
        self.tts_engine = None
        self.microphone = None
        self._tts_lock = threading.Lock()
        self._stt_backend = None   # "pyaudio" | "sounddevice" | None
        self._tts_backend = None   # "pyttsx3" | "espeak" | None
        self._init_stt()
        self._init_tts()

    # ── STT init ────────────────────────────────────────────────────────────

    def _init_stt(self):
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3500
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Try pyaudio first
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            # Quick test open/close
            with self.microphone:
                pass
            self._stt_backend = "pyaudio"
            console.print("[green]✓ Microphone ready (pyaudio)[/green]")
            return
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: sounddevice
        try:
            import sounddevice  # noqa: F401
            self._stt_backend = "sounddevice"
            console.print("[green]✓ Microphone ready (sounddevice)[/green]")
            return
        except ImportError:
            pass
        except Exception:
            pass

        console.print(
            "[yellow]⚠ No microphone backend found.\n"
            "  Fix: pip install pyaudio   OR   pip install sounddevice\n"
            "  Running in text-only mode.[/yellow]"
        )

    # ── TTS init ────────────────────────────────────────────────────────────

    def _init_tts(self):
        # Try pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.config.voice_rate)
            engine.setProperty("volume", self.config.voice_volume)
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)
            self.tts_engine = engine
            self._tts_backend = "pyttsx3"
            console.print("[green]✓ Text-to-speech ready (pyttsx3)[/green]")
            return
        except ImportError:
            pass
        except Exception as e:
            console.print(f"[dim]pyttsx3 init warning: {e}[/dim]")

        # Fallback: espeak system command
        try:
            import subprocess
            result = subprocess.run(["espeak", "--version"], capture_output=True)
            if result.returncode == 0:
                self._tts_backend = "espeak"
                console.print("[green]✓ Text-to-speech ready (espeak)[/green]")
                return
        except FileNotFoundError:
            pass

        console.print(
            "[yellow]⚠ No TTS engine found. Nova will show text only.\n"
            "  Fix: pip install pyttsx3   or   sudo apt install espeak[/yellow]"
        )

    # ── speak ────────────────────────────────────────────────────────────────

    def speak(self, text: str):
        console.print(f"[bold blue]Nova:[/bold blue] {text}")

        if self._tts_backend == "pyttsx3" and self.tts_engine:
            with self._tts_lock:
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    console.print(f"[dim]TTS warn: {e}[/dim]")

        elif self._tts_backend == "espeak":
            import subprocess
            try:
                subprocess.run(
                    ["espeak", "-s", str(self.config.voice_rate), text],
                    capture_output=True
                )
            except Exception as e:
                console.print(f"[dim]espeak warn: {e}[/dim]")

    # ── listen ───────────────────────────────────────────────────────────────

    def listen(self, timeout: int = 5, phrase_limit: int = 15) -> str | None:
        if self._stt_backend == "pyaudio":
            return self._listen_pyaudio(timeout, phrase_limit)
        elif self._stt_backend == "sounddevice":
            return self._listen_sounddevice(phrase_limit)
        return None

    def _listen_pyaudio(self, timeout: int, phrase_limit: int) -> str | None:
        import speech_recognition as sr
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                console.print("[dim]🎤 Listening...[/dim]")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            text = self.recognizer.recognize_google(
                audio, language=self.config.language
            )
            console.print(f"[bold green]You:[/bold green] {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            console.print(f"[yellow]⚠ Speech API error: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]⚠ Listen error: {e}[/yellow]")
            return None

    def _listen_sounddevice(self, phrase_limit: int) -> str | None:
        import sounddevice as sd
        import speech_recognition as sr
        try:
            samplerate = 16000
            duration = min(phrase_limit, 10)
            console.print("[dim]🎤 Listening...[/dim]")
            recording = sd.rec(
                int(duration * samplerate),
                samplerate=samplerate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            raw = recording.tobytes()
            audio = sr.AudioData(raw, samplerate, 2)
            text = self.recognizer.recognize_google(
                audio, language=self.config.language
            )
            console.print(f"[bold green]You:[/bold green] {text}")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            console.print(f"[yellow]⚠ Speech API error: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]⚠ Listen error: {e}[/yellow]")
            return None

    def listen_for_wake_word(self, wake_word: str) -> bool:
        result = self.listen(timeout=3, phrase_limit=3)
        return bool(result and wake_word.lower() in result.lower())

    def text_input(self) -> str:
        try:
            return input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            return ""

    @property
    def has_voice_input(self) -> bool:
        return self._stt_backend is not None

    @property
    def has_voice_output(self) -> bool:
        return self._tts_backend is not None
