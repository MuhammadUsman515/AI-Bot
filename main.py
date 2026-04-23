#!/usr/bin/env python3
"""
Nova — Advanced Voice AI Assistant
Run: python main.py [--text]
  --text   : skip microphone, use keyboard input only
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nova.core.config import Config
from nova.core.assistant import Nova
from nova.core.voice import VoiceEngine

console = Console()

BANNER = """
 ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗
 ████╗  ██║██╔═══██╗██║   ██║██╔══██╗
 ██╔██╗ ██║██║   ██║██║   ██║███████║
 ██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║
 ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║
 ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝
   Advanced Voice AI Assistant v1.0
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Nova Voice AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no microphone)")
    parser.add_argument("--no-tts", action="store_true", help="Disable text-to-speech output")
    return parser.parse_args()


def main():
    args = parse_args()

    console.print(Panel(Text(BANNER, style="bold cyan"), border_style="cyan"))

    # Load and validate config
    config = Config()
    errors = config.validate()
    if errors:
        for err in errors:
            console.print(f"[bold red]✗ {err}[/bold red]")
        console.print("\n[yellow]Copy .env.example to .env and add your API keys.[/yellow]")
        sys.exit(1)

    console.print("[bold green]✓ Config loaded[/bold green]")

    # Initialize assistant
    nova = Nova(config)
    console.print("[bold green]✓ Nova assistant ready[/bold green]")

    # Initialize voice engine
    voice = VoiceEngine(config)

    # Greet user
    greeting = nova.greet()
    voice.speak(greeting)

    # Auto-detect voice availability
    use_voice = not args.text and voice.has_voice_input
    use_tts = not args.no_tts and voice.has_voice_output

    if not args.text and not voice.has_voice_input:
        console.print("[yellow]⚠ No mic detected — switching to text mode automatically.[/yellow]")
        console.print("[dim]  To enable voice: pip install pyaudio  or  pip install sounddevice[/dim]\n")

    # Print mode info
    mode_parts = []
    mode_parts.append("🎤 Voice input" if use_voice else "⌨️  Text input")
    mode_parts.append("🔊 Voice output" if use_tts else "💬 Text output only")
    console.print(f"\n[dim]{' | '.join(mode_parts)}[/dim]")

    if use_voice:
        console.print(f"[dim]Say '[bold]{config.wake_word}[/bold]' to wake me up. Ctrl+C to quit.[/dim]\n")
    else:
        console.print("[dim]Type your command and press Enter. 'quit' = exit | 'clear' = reset memory.[/dim]\n")

    # Main loop
    while True:
        try:
            user_input = _get_input(voice, use_voice, config.wake_word)

            if user_input is None:
                continue

            user_input = user_input.strip()

            if not user_input:
                continue

            # Built-in commands
            if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
                farewell = "Goodbye! Have a great day!"
                voice.speak(farewell)
                break

            if user_input.lower() in ("clear", "reset", "forget"):
                nova.clear_history()
                msg = "Memory cleared. Starting fresh!"
                voice.speak(msg)
                continue

            if user_input.lower() in ("help", "what can you do", "commands"):
                _show_help(voice)
                continue

            # Process with Nova
            console.print()
            response = nova.process(user_input)

            if response:
                if use_tts:
                    voice.speak(response)
                else:
                    console.print(f"[bold blue]Nova:[/bold blue] {response}")
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Say 'quit' or press Ctrl+C again to exit.[/yellow]")
            try:
                again = _get_input(voice, use_voice, config.wake_word)
                if again and again.lower() in ("quit", "exit"):
                    break
            except KeyboardInterrupt:
                break

    console.print("\n[cyan]Nova session ended. Goodbye![/cyan]")


def _get_input(voice: VoiceEngine, use_voice: bool, wake_word: str) -> str | None:
    if use_voice:
        # Check for wake word first
        console.print(f"[dim]Listening for '{wake_word}'...[/dim]", end="\r")
        detected = voice.listen_for_wake_word(wake_word)
        if detected:
            voice.speak("Yes?")
            console.print("[bold green]Activated! Listening...[/bold green]")
            return voice.listen(timeout=8, phrase_limit=20)
        return None
    else:
        try:
            return input("You: ")
        except EOFError:
            return "quit"


def _show_help(voice: VoiceEngine):
    help_text = """
[bold cyan]Nova Capabilities:[/bold cyan]

[bold]System Control[/bold]
  • "What's my CPU usage?" / "Check system info"
  • "Take a screenshot" / "Lock my screen"
  • "Turn volume up" / "Set brightness to 70%"
  • "Open Chrome" / "Kill process firefox"
  • "Check WiFi networks" / "Connect to MyWifi"
  • "Empty trash" / "Clean my disk"

[bold]Files & Desktop[/bold]
  • "Find all PDF files in Documents"
  • "Create a folder called Projects"
  • "Zip these files: file1.txt, file2.txt"
  • "Read the file notes.txt"
  • "Add a note: buy groceries"
  • "What's in my clipboard?"

[bold]Productivity[/bold]
  • "Calculate 25 * 4 + 100"
  • "Convert 100 USD to EUR"
  • "Translate 'Hello' to Spanish"
  • "Set a timer for 5 minutes"
  • "Add todo: finish the report"
  • "List my tasks"
  • "Send email to john@example.com"

[bold]Developer Tools[/bold]
  • "Run this Python code: print('Hello')"
  • "Git status" / "Git commit: fix bug"
  • "Test API GET https://api.example.com"
  • "Create a Flask project called myapp"
  • "Search for 'def login' in my code"
  • "Run command: ls -la"

[bold]Web & Media[/bold]
  • "Search for Python tutorials"
  • "What's the weather in London?"
  • "Get me the latest tech news"
  • "Play lofi music on YouTube"
  • "Bitcoin price" / "Tesla stock"
  • "Tell me a joke" / "Give me a quote"
  • "Find recipe for pasta carbonara"
  • "Get directions to Times Square"

[dim]Type 'clear' to reset memory | 'quit' to exit[/dim]
"""
    console.print(help_text)
    voice.speak("Here are some things I can do. Check the console for the full list.")


if __name__ == "__main__":
    main()
