"""Nova Web Portal — Flask + SocketIO server"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from nova.core.config import Config
from nova.core.assistant import Nova

app = Flask(__name__)
app.config["SECRET_KEY"] = "nova-secret-key-2024"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Init Nova ─────────────────────────────────────────────────────────────────

config = Config()
errors = config.validate()
if errors:
    print("❌ Config error:", errors[0])
    print("   Create a .env file with ANTHROPIC_API_KEY=your_key")
    sys.exit(1)

nova = Nova(config)
print("✓ Nova assistant ready")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": config.model})


# ── SocketIO events ───────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    greeting = nova.greet()
    emit("nova_message", {
        "text": greeting,
        "type": "greeting"
    })

@socketio.on("user_message")
def on_user_message(data):
    user_text = data.get("message", "").strip()
    if not user_text:
        return

    # Tool callback → sends live tool updates to the browser
    def tool_notify(tool_name, tool_input):
        tool_labels = {
            "get_system_info":    "System info check kar raha hoon...",
            "get_weather":        "Weather dekh raha hoon...",
            "get_news":           "News fetch kar raha hoon...",
            "web_search":         "Web search kar raha hoon...",
            "get_crypto_price":   "Crypto price dekh raha hoon...",
            "get_stock_price":    "Stock price dekh raha hoon...",
            "calculate":          "Calculate kar raha hoon...",
            "translate_text":     "Translate kar raha hoon...",
            "manage_todos":       "To-do list update kar raha hoon...",
            "set_timer":          "Timer set kar raha hoon...",
            "take_screenshot":    "Screenshot le raha hoon...",
            "run_code":           "Code run kar raha hoon...",
            "git_operation":      "Git operation...",
            "find_recipe":        "Recipe dhundh raha hoon...",
            "get_movie_info":     "Movie info la raha hoon...",
            "get_wikipedia":      "Wikipedia search kar raha hoon...",
            "send_email":         "Email bhej raha hoon...",
            "control_volume":     "Volume adjust kar raha hoon...",
            "control_brightness": "Brightness adjust kar raha hoon...",
            "launch_application": "App khol raha hoon...",
            "play_media":         "Media play kar raha hoon...",
            "get_joke":           "Joke dhundh raha hoon... 😄",
            "get_quote":          "Quote la raha hoon...",
        }
        label = tool_labels.get(tool_name, f"{tool_name} chal raha hai...")
        socketio.emit("tool_activity", {"tool": tool_name, "label": label})

    nova.tool_callback = tool_notify

    try:
        response = nova.process(user_text)
        emit("nova_message", {"text": response, "type": "response"})
    except Exception as e:
        emit("nova_message", {
            "text": f"Kuch masla aaya: {str(e)}",
            "type": "error"
        })
    finally:
        nova.tool_callback = None

@socketio.on("clear_history")
def on_clear():
    nova.clear_history()
    emit("nova_message", {
        "text": "Memory clear ho gayi! Fresh start karte hain. 🧹",
        "type": "system"
    })

@socketio.on("get_capabilities")
def on_capabilities():
    caps = [
        {"icon": "🖥️", "label": "System Info", "cmd": "system info dikhao"},
        {"icon": "🌤️", "label": "Weather",     "cmd": "Lahore ka weather batao"},
        {"icon": "📰", "label": "News",         "cmd": "latest tech news dikhao"},
        {"icon": "🧮", "label": "Calculator",   "cmd": "25 * 4 + 100 calculate karo"},
        {"icon": "⏱️", "label": "Timer",        "cmd": "5 minute ka timer lagao"},
        {"icon": "✅", "label": "Todo",          "cmd": "todos dikhao"},
        {"icon": "💱", "label": "Currency",     "cmd": "100 USD to PKR convert karo"},
        {"icon": "🌐", "label": "Translate",    "cmd": "Hello ko Urdu mein translate karo"},
        {"icon": "😄", "label": "Joke",         "cmd": "ek joke sunao"},
        {"icon": "💬", "label": "Quote",        "cmd": "ek motivational quote do"},
        {"icon": "₿",  "label": "Crypto",       "cmd": "Bitcoin ka price batao"},
        {"icon": "📈", "label": "Stocks",       "cmd": "AAPL stock price dikhao"},
        {"icon": "🎬", "label": "Movies",       "cmd": "Inception movie ki info do"},
        {"icon": "🍳", "label": "Recipe",       "cmd": "biryani ki recipe batao"},
        {"icon": "🗒️", "label": "Notes",        "cmd": "mera note dikhao"},
        {"icon": "📸", "label": "Screenshot",   "cmd": "screenshot lo"},
    ]
    emit("capabilities", caps)


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"\n🌟 Nova Web Portal starting...")
    print(f"   Open: http://{args.host}:{args.port}")
    print(f"   Stop: Ctrl+C\n")
    socketio.run(app, host=args.host, port=args.port, debug=False)
