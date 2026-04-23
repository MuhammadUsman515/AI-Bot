import threading
import time
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from nova.utils.helpers import (
    safe_eval, load_json, save_json, TODOS_FILE, timestamp
)


_active_timers: dict[str, threading.Timer] = {}
_stopwatches: dict[str, float] = {}


class Productivity:

    def __init__(self, config):
        self.config = config

    # ── Tool Definitions ────────────────────────────────────────────────────

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression e.g. '25 * 4 + 100 / 2'"},
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "convert_units",
                "description": "Convert between units: length, weight, temperature, volume, area, speed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number", "description": "Value to convert"},
                        "from_unit": {"type": "string", "description": "Source unit (e.g. 'km', 'kg', 'celsius')"},
                        "to_unit": {"type": "string", "description": "Target unit (e.g. 'miles', 'lbs', 'fahrenheit')"},
                    },
                    "required": ["value", "from_unit", "to_unit"]
                }
            },
            {
                "name": "convert_currency",
                "description": "Convert between currencies using live exchange rates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Amount to convert"},
                        "from_currency": {"type": "string", "description": "Source currency code e.g. USD"},
                        "to_currency": {"type": "string", "description": "Target currency code e.g. EUR"},
                    },
                    "required": ["amount", "from_currency", "to_currency"]
                }
            },
            {
                "name": "translate_text",
                "description": "Translate text to any language",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to translate"},
                        "to_language": {"type": "string", "description": "Target language (e.g. 'Spanish', 'French', 'Urdu', 'Arabic')"},
                        "from_language": {"type": "string", "description": "Source language (auto-detect if not specified)"},
                    },
                    "required": ["text", "to_language"]
                }
            },
            {
                "name": "define_word",
                "description": "Get the definition, synonyms, and usage of a word",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string", "description": "Word to look up"},
                        "mode": {
                            "type": "string",
                            "enum": ["definition", "synonyms", "antonyms", "examples"],
                            "description": "What to retrieve"
                        },
                    },
                    "required": ["word"]
                }
            },
            {
                "name": "set_timer",
                "description": "Set a countdown timer that alerts when done",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "duration": {"type": "string", "description": "Duration e.g. '5 minutes', '30 seconds', '1 hour'"},
                        "label": {"type": "string", "description": "Optional timer label"},
                    },
                    "required": ["duration"]
                }
            },
            {
                "name": "manage_stopwatch",
                "description": "Start, stop, or read a stopwatch",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start", "stop", "read", "reset"],
                            "description": "Stopwatch action"
                        },
                        "name": {"type": "string", "description": "Stopwatch name (default: 'main')"},
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "manage_todos",
                "description": "Add, list, complete, or delete todo tasks",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "list", "complete", "delete", "clear"],
                            "description": "Todo action"
                        },
                        "task": {"type": "string", "description": "Task description (for 'add')"},
                        "task_id": {"type": "integer", "description": "Task ID (for 'complete' or 'delete')"},
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Task priority"
                        },
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body text"},
                        "cc": {"type": "string", "description": "CC email address (optional)"},
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "get_current_datetime",
                "description": "Get current date, time, day of week, week number",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "timezone": {"type": "string", "description": "Timezone name (optional)"},
                        "format": {"type": "string", "description": "Date format (optional)"},
                    },
                    "required": []
                }
            },
            {
                "name": "manage_pomodoro",
                "description": "Start or manage a Pomodoro focus session (25 min work + 5 min break)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start", "break", "stop", "status"],
                            "description": "Pomodoro action"
                        },
                        "work_minutes": {"type": "integer", "description": "Work session length (default 25)"},
                        "break_minutes": {"type": "integer", "description": "Break length (default 5)"},
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "text_to_speech_file",
                "description": "Convert text to a speech audio file (MP3/WAV)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert"},
                        "output_path": {"type": "string", "description": "Output file path (optional)"},
                        "language": {"type": "string", "description": "Language code e.g. 'en', 'es', 'ur'"},
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "auto_type",
                "description": "Automatically type text on the keyboard",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to type"},
                        "delay_seconds": {"type": "number", "description": "Delay before typing starts"},
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "make_invoice",
                "description": "Generate a simple text invoice",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "price": {"type": "number"}
                                }
                            },
                            "description": "List of invoice line items"
                        },
                        "currency": {"type": "string", "description": "Currency symbol (default: $)"},
                    },
                    "required": ["client_name", "items"]
                }
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "calculate": self.calculate,
            "convert_units": self.convert_units,
            "convert_currency": self.convert_currency,
            "translate_text": self.translate_text,
            "define_word": self.define_word,
            "set_timer": self.set_timer,
            "manage_stopwatch": self.manage_stopwatch,
            "manage_todos": self.manage_todos,
            "send_email": self.send_email,
            "get_current_datetime": self.get_current_datetime,
            "manage_pomodoro": self.manage_pomodoro,
            "text_to_speech_file": self.text_to_speech_file,
            "auto_type": self.auto_type,
            "make_invoice": self.make_invoice,
        }

    # ── Implementations ──────────────────────────────────────────────────────

    def calculate(self, expression: str) -> str:
        result = safe_eval(expression)
        return f"{expression} = {result}"

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> str:
        fu = from_unit.lower().strip()
        tu = to_unit.lower().strip()

        # Length
        to_meters = {"m": 1, "meter": 1, "meters": 1, "km": 1000, "kilometer": 1000, "kilometers": 1000,
                     "cm": 0.01, "mm": 0.001, "mile": 1609.34, "miles": 1609.34, "yard": 0.9144,
                     "yards": 0.9144, "foot": 0.3048, "feet": 0.3048, "inch": 0.0254, "inches": 0.0254}
        # Weight
        to_kg = {"kg": 1, "kilogram": 1, "kilograms": 1, "g": 0.001, "gram": 0.001, "grams": 0.001,
                 "lb": 0.453592, "lbs": 0.453592, "pound": 0.453592, "pounds": 0.453592,
                 "oz": 0.0283495, "ounce": 0.0283495, "ounces": 0.0283495, "t": 1000, "ton": 1000, "tons": 1000}
        # Volume
        to_liters = {"l": 1, "liter": 1, "liters": 1, "ml": 0.001, "milliliter": 0.001,
                     "gallon": 3.78541, "gallons": 3.78541, "quart": 0.946353, "cup": 0.236588,
                     "oz_fl": 0.0295735, "fl oz": 0.0295735}

        # Temperature (special case)
        temp_units = {"celsius", "c", "°c", "fahrenheit", "f", "°f", "kelvin", "k"}
        if fu in temp_units or tu in temp_units:
            return self._convert_temperature(value, fu, tu)

        # Try length
        if fu in to_meters and tu in to_meters:
            result = value * to_meters[fu] / to_meters[tu]
            return f"{value} {from_unit} = {result:.4f} {to_unit}"
        # Try weight
        if fu in to_kg and tu in to_kg:
            result = value * to_kg[fu] / to_kg[tu]
            return f"{value} {from_unit} = {result:.4f} {to_unit}"
        # Try volume
        if fu in to_liters and tu in to_liters:
            result = value * to_liters[fu] / to_liters[tu]
            return f"{value} {from_unit} = {result:.4f} {to_unit}"

        # Try pint library
        try:
            from pint import UnitRegistry
            ureg = UnitRegistry()
            q = value * ureg(fu)
            result = q.to(tu)
            return f"{value} {from_unit} = {result:.4f}"
        except Exception:
            pass

        return f"Cannot convert {from_unit} to {to_unit}"

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> str:
        fu = from_unit.lower().replace("°", "").replace("degree", "").strip()
        tu = to_unit.lower().replace("°", "").replace("degree", "").strip()
        if fu in ("c", "celsius"):
            celsius = value
        elif fu in ("f", "fahrenheit"):
            celsius = (value - 32) * 5 / 9
        elif fu in ("k", "kelvin"):
            celsius = value - 273.15
        else:
            return f"Unknown temperature unit: {from_unit}"

        if tu in ("c", "celsius"):
            result = celsius
        elif tu in ("f", "fahrenheit"):
            result = celsius * 9 / 5 + 32
        elif tu in ("k", "kelvin"):
            result = celsius + 273.15
        else:
            return f"Unknown temperature unit: {to_unit}"

        return f"{value} {from_unit} = {result:.2f} {to_unit}"

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> str:
        try:
            import requests
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            rate = data["rates"].get(to_currency.upper())
            if rate is None:
                return f"Currency not found: {to_currency}"
            result = amount * rate
            return f"{amount} {from_currency.upper()} = {result:.2f} {to_currency.upper()} (rate: {rate})"
        except Exception as e:
            return f"Currency conversion error: {e}"

    def translate_text(self, text: str, to_language: str, from_language: str = "auto") -> str:
        try:
            from deep_translator import GoogleTranslator
            lang_map = {
                "urdu": "ur", "arabic": "ar", "spanish": "es", "french": "fr",
                "german": "de", "italian": "it", "portuguese": "pt", "russian": "ru",
                "chinese": "zh-CN", "japanese": "ja", "korean": "ko", "hindi": "hi",
                "english": "en", "turkish": "tr", "persian": "fa", "dutch": "nl",
            }
            to_code = lang_map.get(to_language.lower(), to_language.lower())
            src_code = lang_map.get(from_language.lower(), from_language.lower()) if from_language != "auto" else "auto"
            translator = GoogleTranslator(source=src_code, target=to_code)
            result = translator.translate(text)
            return f"Translation ({to_language}): {result}"
        except ImportError:
            return "deep-translator not installed. Run: pip install deep-translator"
        except Exception as e:
            return f"Translation error: {e}"

    def define_word(self, word: str, mode: str = "definition") -> str:
        try:
            import requests
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return f"Word '{word}' not found in dictionary"
            data = resp.json()[0]
            meanings = data.get("meanings", [])
            if not meanings:
                return f"No meanings found for '{word}'"

            result_lines = [f"Word: {data.get('word', word)}"]
            phonetics = data.get("phonetics", [])
            if phonetics and phonetics[0].get("text"):
                result_lines.append(f"Pronunciation: {phonetics[0]['text']}")

            for meaning in meanings[:2]:
                pos = meaning.get("partOfSpeech", "")
                result_lines.append(f"\n{pos.capitalize()}:")
                if mode in ("definition", "all"):
                    defs = meaning.get("definitions", [])[:3]
                    for i, d in enumerate(defs, 1):
                        result_lines.append(f"  {i}. {d.get('definition', '')}")
                if mode in ("synonyms", "all"):
                    syns = meaning.get("synonyms", [])[:5]
                    if syns:
                        result_lines.append(f"  Synonyms: {', '.join(syns)}")
                if mode in ("antonyms", "all"):
                    ants = meaning.get("antonyms", [])[:5]
                    if ants:
                        result_lines.append(f"  Antonyms: {', '.join(ants)}")
                if mode == "examples":
                    defs = meaning.get("definitions", [])
                    for d in defs[:3]:
                        if d.get("example"):
                            result_lines.append(f"  Example: {d['example']}")
            return "\n".join(result_lines)
        except Exception as e:
            return f"Dictionary error: {e}"

    def set_timer(self, duration: str, label: str = None) -> str:
        seconds = self._parse_duration(duration)
        if seconds <= 0:
            return f"Invalid duration: {duration}"
        name = label or f"timer_{len(_active_timers)+1}"

        def _alert():
            print(f"\n⏰ TIMER '{name}' DONE! ({duration})")

        timer = threading.Timer(seconds, _alert)
        timer.daemon = True
        timer.start()
        _active_timers[name] = timer
        return f"Timer '{name}' set for {duration} ({seconds} seconds)"

    def _parse_duration(self, duration: str) -> int:
        import re
        total = 0
        patterns = [
            (r"(\d+)\s*hour", 3600),
            (r"(\d+)\s*hr", 3600),
            (r"(\d+)\s*h\b", 3600),
            (r"(\d+)\s*minute", 60),
            (r"(\d+)\s*min", 60),
            (r"(\d+)\s*m\b", 60),
            (r"(\d+)\s*second", 1),
            (r"(\d+)\s*sec", 1),
            (r"(\d+)\s*s\b", 1),
        ]
        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, duration.lower()):
                total += int(match.group(1)) * multiplier
        if total == 0:
            try:
                total = int(duration)
            except ValueError:
                pass
        return total

    def manage_stopwatch(self, action: str, name: str = "main") -> str:
        if action == "start":
            _stopwatches[name] = time.time()
            return f"Stopwatch '{name}' started"
        elif action == "stop":
            if name not in _stopwatches:
                return f"Stopwatch '{name}' not running"
            elapsed = time.time() - _stopwatches.pop(name)
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            return f"Stopwatch '{name}' stopped: {h:02d}:{m:02d}:{s:02d}"
        elif action == "read":
            if name not in _stopwatches:
                return f"Stopwatch '{name}' not running"
            elapsed = time.time() - _stopwatches[name]
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            return f"Stopwatch '{name}': {h:02d}:{m:02d}:{s:02d}"
        elif action == "reset":
            _stopwatches.pop(name, None)
            return f"Stopwatch '{name}' reset"
        return "Unknown action"

    def manage_todos(self, action: str, task: str = None, task_id: int = None, priority: str = "medium") -> str:
        todos = load_json(TODOS_FILE)
        if not isinstance(todos, list):
            todos = []

        if action == "add":
            if not task:
                return "Please provide a task description"
            todo = {
                "id": (max((t["id"] for t in todos), default=0) + 1),
                "task": task,
                "priority": priority,
                "done": False,
                "created": timestamp()
            }
            todos.append(todo)
            save_json(TODOS_FILE, todos)
            return f"Task added [ID:{todo['id']}]: {task}"

        elif action == "list":
            if not todos:
                return "No tasks in your to-do list"
            icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            lines = []
            for t in todos:
                status = "✅" if t["done"] else "⬜"
                icon = icons.get(t.get("priority", "medium"), "🟡")
                lines.append(f"{status} [{t['id']}] {icon} {t['task']}")
            return "\n".join(lines)

        elif action == "complete":
            for t in todos:
                if t["id"] == task_id:
                    t["done"] = True
                    t["completed"] = timestamp()
                    save_json(TODOS_FILE, todos)
                    return f"Task {task_id} marked as done: {t['task']}"
            return f"Task {task_id} not found"

        elif action == "delete":
            before = len(todos)
            todos = [t for t in todos if t["id"] != task_id]
            save_json(TODOS_FILE, todos)
            return f"Task {task_id} deleted" if len(todos) < before else f"Task {task_id} not found"

        elif action == "clear":
            save_json(TODOS_FILE, [])
            return "All tasks cleared"

        return "Unknown action"

    def send_email(self, to: str, subject: str, body: str, cc: str = None) -> str:
        if not self.config.email_address or not self.config.email_password:
            return "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email_address
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_address, self.config.email_password)
                recipients = [to] + ([cc] if cc else [])
                server.sendmail(self.config.email_address, recipients, msg.as_string())
            return f"Email sent to {to}"
        except Exception as e:
            return f"Email error: {e}"

    def get_current_datetime(self, timezone: str = None, format: str = None) -> str:
        try:
            if timezone:
                from datetime import timezone as tz_module
                import zoneinfo
                now = datetime.now(zoneinfo.ZoneInfo(timezone))
            else:
                now = datetime.now()
            fmt = format or "%A, %B %d %Y - %I:%M:%S %p"
            return now.strftime(fmt) + f"\nWeek: {now.isocalendar()[1]}, Day of year: {now.timetuple().tm_yday}"
        except Exception as e:
            return f"DateTime error: {e}\nFallback: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def manage_pomodoro(self, action: str, work_minutes: int = 25, break_minutes: int = 5) -> str:
        name = "pomodoro"
        if action == "start":
            seconds = work_minutes * 60

            def _work_done():
                print(f"\n🍅 POMODORO: {work_minutes}-minute work session done! Take a {break_minutes}-min break.")

            timer = threading.Timer(seconds, _work_done)
            timer.daemon = True
            timer.start()
            _active_timers[name] = timer
            _stopwatches[name] = time.time()
            return f"Pomodoro started! Work for {work_minutes} minutes. Focus!"

        elif action == "break":
            seconds = break_minutes * 60

            def _break_done():
                print(f"\n☕ BREAK DONE! Time to get back to work.")

            timer = threading.Timer(seconds, _break_done)
            timer.daemon = True
            timer.start()
            _active_timers[f"{name}_break"] = timer
            return f"Break timer started for {break_minutes} minutes. Relax!"

        elif action == "stop":
            for k in [name, f"{name}_break"]:
                t = _active_timers.pop(k, None)
                if t:
                    t.cancel()
            elapsed = _stopwatches.pop(name, None)
            if elapsed:
                mins = int((time.time() - elapsed) / 60)
                return f"Pomodoro stopped after {mins} minutes"
            return "No active Pomodoro"

        elif action == "status":
            if name in _stopwatches:
                elapsed = int((time.time() - _stopwatches[name]) / 60)
                remaining = max(0, work_minutes - elapsed)
                return f"Pomodoro active: {elapsed} min elapsed, {remaining} min remaining"
            return "No active Pomodoro"

    def text_to_speech_file(self, text: str, output_path: str = None, language: str = "en") -> str:
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(Path.home() / f"nova_tts_{ts}.mp3")
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language)
            tts.save(output_path)
            return f"Audio saved to: {output_path}"
        except ImportError:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.save_to_file(text, output_path.replace(".mp3", ".wav"))
                engine.runAndWait()
                return f"Audio saved to: {output_path.replace('.mp3', '.wav')}"
            except Exception as e2:
                return f"TTS file error: {e2}"
        except Exception as e:
            return f"TTS error: {e}"

    def auto_type(self, text: str, delay_seconds: float = 3.0) -> str:
        def _type():
            time.sleep(delay_seconds)
            try:
                import pyautogui
                pyautogui.typewrite(text, interval=0.03)
            except Exception as e:
                print(f"Auto-type error: {e}")
        t = threading.Thread(target=_type, daemon=True)
        t.start()
        return f"Will type '{text[:30]}...' in {delay_seconds} seconds"

    def make_invoice(self, client_name: str, items: list[dict], currency: str = "$") -> str:
        now = datetime.now()
        lines = [
            "=" * 50,
            f"INVOICE #{now.strftime('%Y%m%d%H%M')}",
            f"Date: {now.strftime('%B %d, %Y')}",
            f"To: {client_name}",
            "=" * 50,
            f"{'Item':<30} {'Qty':>5} {'Price':>8} {'Total':>10}",
            "-" * 55,
        ]
        grand_total = 0
        for item in items:
            desc = item.get("description", "Item")[:28]
            qty = item.get("quantity", 1)
            price = item.get("price", 0)
            total = qty * price
            grand_total += total
            lines.append(f"{desc:<30} {qty:>5} {currency}{price:>7.2f} {currency}{total:>9.2f}")
        lines.extend([
            "-" * 55,
            f"{'TOTAL':<44} {currency}{grand_total:>9.2f}",
            "=" * 50,
            "Thank you for your business!",
        ])
        invoice_text = "\n".join(lines)
        path = Path.home() / f"invoice_{client_name.replace(' ', '_')}_{now.strftime('%Y%m%d')}.txt"
        path.write_text(invoice_text)
        return f"Invoice created:\n{invoice_text}\n\nSaved to: {path}"
