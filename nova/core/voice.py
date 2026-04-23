import sys
import threading
from rich.console import Console

console = Console()


class VoiceEngine:
    def __init__(self, config):
        self.config = config
        self.recognizer = None
        self.tts_engine = None
        self.microphone = None
        self._tts_lock = threading.Lock()
        self._init_stt()
        self._init_tts()

    def _init_stt(self):
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            console.print("[green]✓ Microphone initialized[/green]")
        except ImportError:
            console.print("[yellow]⚠ SpeechRecognition not installed - voice input disabled[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠ Microphone error: {e} - voice input disabled[/yellow]")

    def _init_tts(self):
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", self.config.voice_rate)
            self.tts_engine.setProperty("volume", self.config.voice_volume)
            voices = self.tts_engine.getProperty("voices")
            if voices:
                self.tts_engine.setProperty("voice", voices[0].id)
            console.print("[green]✓ Text-to-speech initialized[/green]")
        except ImportError:
            console.print("[yellow]⚠ pyttsx3 not installed - TTS disabled[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠ TTS error: {e} - TTS disabled[/yellow]")

    def speak(self, text: str):
        console.print(f"[bold blue]Nova:[/bold blue] {text}")
        if not self.tts_engine:
            return
        with self._tts_lock:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                console.print(f"[yellow]⚠ TTS error: {e}[/yellow]")

    def listen(self, timeout: int = 5, phrase_limit: int = 15) -> str | None:
        if not self.recognizer or not self.microphone:
            return None
        import speech_recognition as sr
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                console.print("[dim]Listening...[/dim]")
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
            console.print(f"[yellow]⚠ Speech service error: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]⚠ Listen error: {e}[/yellow]")
            return None

    def listen_for_wake_word(self, wake_word: str) -> bool:
        result = self.listen(timeout=3, phrase_limit=3)
        if result and wake_word.lower() in result.lower():
            return True
        return False

    def text_input(self) -> str:
        try:
            return input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            return ""
