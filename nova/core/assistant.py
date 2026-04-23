import anthropic
from rich.console import Console
from nova.core.config import Config
from nova.modules.system_control import SystemControl
from nova.modules.desktop_files import DesktopFiles
from nova.modules.productivity import Productivity
from nova.modules.developer import Developer
from nova.modules.web_media import WebMedia

console = Console()

SYSTEM_PROMPT = """You are Nova, an advanced AI voice assistant. You help users control their computer, search the web, write code, manage tasks, and much more.

Your personality:
- Friendly, smart, and concise
- Responses will be spoken aloud — keep them under 3 sentences when possible
- Always use the appropriate tool when asked to perform an action
- Confirm what you did after completing a task
- If a tool fails, explain briefly and suggest an alternative

LANGUAGE RULE (most important):
- Detect the language the user is writing in and ALWAYS reply in the EXACT same language.
- Roman Urdu examples: "kya hal hai", "weather check karo", "mujhe help chahiye", "batao", "karo", "chalao" → reply in Roman Urdu
- English → reply in English
- Urdu script → reply in Urdu script
- Hindi / Roman Hindi → reply in same
- NEVER switch languages unless the user switches first.
- Roman Urdu tone should be natural and friendly, like talking to a dost (friend).

You support 100+ capabilities across system control, file management, productivity, developer tools, and web/media.
When the user greets you or asks what you can do, briefly mention a few key capabilities in their language."""


class Nova:

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.conversation_history: list[dict] = []
        self.tool_callback = None   # optional fn(tool_name) called before each tool runs

        # Initialize all modules
        self.system = SystemControl()
        self.desktop = DesktopFiles()
        self.productivity = Productivity(config)
        self.developer = Developer(config)
        self.web = WebMedia(config)

        # Build merged tool list and handler map
        self.tools = (
            self.system.get_tools()
            + self.desktop.get_tools()
            + self.productivity.get_tools()
            + self.developer.get_tools()
            + self.web.get_tools()
        )

        self._handlers: dict = {}
        for module in (self.system, self.desktop, self.productivity, self.developer, self.web):
            self._handlers.update(module.get_tool_handlers())

    # ── Public API ───────────────────────────────────────────────────────────

    def greet(self) -> str:
        import datetime
        hour = datetime.datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
        return (
            f"Good {time_of_day}! I'm Nova, your AI assistant. "
            "I can control your PC, search the web, help with code, manage tasks, play music, and much more. "
            "How can I help you?"
        )

    def process(self, user_input: str) -> str:
        """Run an agentic loop: let Claude decide which tools to call, execute them, get final response."""
        if not user_input.strip():
            return ""

        self.conversation_history.append({"role": "user", "content": user_input})

        for _ in range(8):  # max tool-use iterations
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=self.conversation_history,
            )

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self.conversation_history.append({"role": "assistant", "content": response.content})
                return text

            if response.stop_reason == "tool_use":
                self.conversation_history.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        console.print(f"[dim cyan]  → {block.name}({self._fmt_input(block.input)})[/dim cyan]")
                        if self.tool_callback:
                            self.tool_callback(block.name, block.input)
                        result = self._call_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                self.conversation_history.append({"role": "user", "content": tool_results})
                continue

            break  # unexpected stop_reason

        return "Done."

    def clear_history(self):
        self.conversation_history.clear()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _call_tool(self, name: str, inputs: dict) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f"Unknown tool: {name}"
        try:
            return str(handler(**inputs))
        except TypeError as e:
            return f"Bad arguments for {name}: {e}"
        except Exception as e:
            return f"Tool error in {name}: {e}"

    def _extract_text(self, response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def _fmt_input(self, inp: dict) -> str:
        parts = []
        for k, v in inp.items():
            val = str(v)
            parts.append(f"{k}={val[:40]!r}" if len(val) > 40 else f"{k}={v!r}")
        return ", ".join(parts)
