#!/bin/bash
# Nova AI Bot - Linux Setup Script

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Nova Voice AI Bot - Setup Script   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── System dependencies ──────────────────────────────────────────────────────
echo "📦 Installing system dependencies..."

if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y \
        python3 python3-pip python3-venv \
        portaudio19-dev \
        espeak espeak-ng \
        ffmpeg \
        scrot \
        brightnessctl \
        pulseaudio-utils \
        libxcb-xinerama0 \
        xclip xdotool \
        git curl wget \
        2>/dev/null || true
elif command -v dnf &>/dev/null; then
    sudo dnf install -y \
        python3 python3-pip \
        portaudio-devel \
        espeak \
        ffmpeg \
        scrot \
        git curl wget \
        2>/dev/null || true
elif command -v pacman &>/dev/null; then
    sudo pacman -Sy --noconfirm \
        python python-pip \
        portaudio \
        espeak-ng \
        ffmpeg \
        scrot \
        git curl wget \
        2>/dev/null || true
fi

echo "✓ System dependencies installed"

# ── Python virtual environment ────────────────────────────────────────────────
echo ""
echo "🐍 Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install --upgrade pip -q

# ── Python packages ───────────────────────────────────────────────────────────
echo ""
echo "📦 Installing Python packages..."

# Install packages one by one to skip failures gracefully
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    pip install "$line" -q 2>/dev/null || echo "  ⚠ Skipped (optional): $line"
done < requirements.txt

echo "✓ Python packages installed"

# ── Environment file ──────────────────────────────────────────────────────────
echo ""
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   nano .env"
    echo ""
    echo "   Required:"
    echo "   • ANTHROPIC_API_KEY  — get from https://console.anthropic.com"
    echo ""
    echo "   Optional (for extra features):"
    echo "   • OPENWEATHER_API_KEY — weather (free at openweathermap.org)"
    echo "   • NEWS_API_KEY        — news (free at newsapi.org)"
    echo "   • EMAIL_ADDRESS / EMAIL_PASSWORD — send emails"
else
    echo "✓ .env already exists"
fi

# ── Nova data directory ───────────────────────────────────────────────────────
mkdir -p ~/.nova
echo "✓ Nova data directory ready: ~/.nova"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║          Setup Complete! ✅           ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "To start Nova:"
echo "  source venv/bin/activate"
echo "  python main.py           # Voice mode"
echo "  python main.py --text    # Text-only mode"
echo "  python main.py --no-tts  # No text-to-speech"
echo ""
