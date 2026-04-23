import os
import subprocess
import platform
import psutil
import datetime
from pathlib import Path
from nova.utils.helpers import run_command, format_bytes, format_uptime, is_linux, is_windows, is_mac


class SystemControl:

    # ── Tool Definitions ────────────────────────────────────────────────────

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "get_system_info",
                "description": "Get PC system information: CPU, RAM, disk, OS, uptime, battery",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["all", "cpu", "memory", "disk", "os", "battery", "network", "temperature"],
                            "description": "Category of info to retrieve"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "control_power",
                "description": "Shutdown, restart, sleep, hibernate, or lock the PC",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["shutdown", "restart", "sleep", "hibernate", "lock"],
                            "description": "Power action to perform"
                        },
                        "delay_seconds": {
                            "type": "integer",
                            "description": "Delay in seconds before action (default 0)"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "control_volume",
                "description": "Increase, decrease, mute, unmute, or set system volume",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["up", "down", "mute", "unmute", "set", "get"],
                            "description": "Volume action"
                        },
                        "level": {
                            "type": "integer",
                            "description": "Volume level 0-100 (only for 'set')"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "control_brightness",
                "description": "Increase, decrease, or set screen brightness",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["up", "down", "set", "get"],
                            "description": "Brightness action"
                        },
                        "level": {
                            "type": "integer",
                            "description": "Brightness level 0-100 (only for 'set')"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "launch_application",
                "description": "Open / launch any application by name",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the application to launch (e.g. 'chrome', 'vscode', 'spotify')"
                        }
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "take_screenshot",
                "description": "Take a screenshot of the screen",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Optional filename for the screenshot"
                        },
                        "region": {
                            "type": "string",
                            "description": "Optional region: 'full' or 'active_window'"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "manage_wifi",
                "description": "List, connect, or disconnect WiFi networks",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "connect", "disconnect", "status"],
                            "description": "WiFi action"
                        },
                        "network_name": {
                            "type": "string",
                            "description": "SSID to connect to (only for 'connect')"
                        },
                        "password": {
                            "type": "string",
                            "description": "WiFi password (only for 'connect')"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "check_network_speed",
                "description": "Check current internet network speed and ping",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "manage_task_manager",
                "description": "List running processes, kill a stuck app, or show top CPU/RAM processes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "kill", "top_cpu", "top_ram"],
                            "description": "Task manager action"
                        },
                        "process_name": {
                            "type": "string",
                            "description": "Process name to kill (only for 'kill')"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "empty_trash",
                "description": "Empty the system recycle bin / trash",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "control_mic",
                "description": "Mute or unmute the microphone",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["mute", "unmute", "toggle", "status"],
                            "description": "Microphone action"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "toggle_night_mode",
                "description": "Enable or disable night mode / dark mode / blue light filter",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "enable": {
                            "type": "boolean",
                            "description": "True to enable, False to disable"
                        }
                    },
                    "required": ["enable"]
                }
            },
            {
                "name": "sync_time",
                "description": "Synchronize system clock with internet time servers",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "clean_disk",
                "description": "Clean junk files, temp files, and cache to free up disk space",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "manage_bluetooth",
                "description": "List, connect, or disconnect Bluetooth devices",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "connect", "disconnect", "status"],
                            "description": "Bluetooth action"
                        },
                        "device_name": {
                            "type": "string",
                            "description": "Device name or MAC address"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "control_webcam",
                "description": "Check webcam status or capture a webcam photo",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["capture", "status"],
                            "description": "Webcam action"
                        }
                    },
                    "required": ["action"]
                }
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "get_system_info": self.get_system_info,
            "control_power": self.control_power,
            "control_volume": self.control_volume,
            "control_brightness": self.control_brightness,
            "launch_application": self.launch_application,
            "take_screenshot": self.take_screenshot,
            "manage_wifi": self.manage_wifi,
            "check_network_speed": self.check_network_speed,
            "manage_task_manager": self.manage_task_manager,
            "empty_trash": self.empty_trash,
            "control_mic": self.control_mic,
            "toggle_night_mode": self.toggle_night_mode,
            "sync_time": self.sync_time,
            "clean_disk": self.clean_disk,
            "manage_bluetooth": self.manage_bluetooth,
            "control_webcam": self.control_webcam,
        }

    # ── Implementations ──────────────────────────────────────────────────────

    def get_system_info(self, category: str = "all") -> str:
        info = {}
        try:
            if category in ("all", "cpu"):
                info["cpu_usage"] = f"{psutil.cpu_percent(interval=1)}%"
                info["cpu_cores"] = psutil.cpu_count(logical=False)
                info["cpu_threads"] = psutil.cpu_count(logical=True)
                freq = psutil.cpu_freq()
                if freq:
                    info["cpu_freq"] = f"{freq.current:.0f} MHz"

            if category in ("all", "memory"):
                mem = psutil.virtual_memory()
                info["ram_total"] = format_bytes(mem.total)
                info["ram_used"] = format_bytes(mem.used)
                info["ram_free"] = format_bytes(mem.available)
                info["ram_percent"] = f"{mem.percent}%"
                swap = psutil.swap_memory()
                info["swap_used"] = format_bytes(swap.used)

            if category in ("all", "disk"):
                disk = psutil.disk_usage("/")
                info["disk_total"] = format_bytes(disk.total)
                info["disk_used"] = format_bytes(disk.used)
                info["disk_free"] = format_bytes(disk.free)
                info["disk_percent"] = f"{disk.percent}%"

            if category in ("all", "os"):
                info["os"] = platform.system()
                info["os_version"] = platform.release()
                info["hostname"] = platform.node()
                info["architecture"] = platform.machine()
                info["python_version"] = platform.python_version()
                boot = psutil.boot_time()
                uptime = datetime.datetime.now().timestamp() - boot
                info["uptime"] = format_uptime(uptime)

            if category in ("all", "battery"):
                batt = psutil.sensors_battery()
                if batt:
                    info["battery_percent"] = f"{batt.percent:.0f}%"
                    info["plugged_in"] = batt.power_plugged
                    if not batt.power_plugged and batt.secsleft > 0:
                        info["time_left"] = format_uptime(batt.secsleft)
                else:
                    info["battery"] = "No battery (desktop)"

            if category in ("all", "temperature"):
                try:
                    temps = psutil.sensors_temperatures()
                    for name, entries in (temps or {}).items():
                        for e in entries[:2]:
                            info[f"temp_{name}"] = f"{e.current:.1f}°C"
                except Exception:
                    info["temperature"] = "Not available"

            if category in ("all", "network"):
                net = psutil.net_io_counters()
                info["bytes_sent"] = format_bytes(net.bytes_sent)
                info["bytes_recv"] = format_bytes(net.bytes_recv)

        except Exception as e:
            return f"Error getting system info: {e}"

        lines = [f"{k}: {v}" for k, v in info.items()]
        return "\n".join(lines)

    def control_power(self, action: str, delay_seconds: int = 0) -> str:
        delay = delay_seconds or 0
        try:
            if is_linux():
                cmds = {
                    "shutdown": ["shutdown", "-h", f"+{delay//60 or 'now'}"],
                    "restart": ["reboot"],
                    "sleep": ["systemctl", "suspend"],
                    "hibernate": ["systemctl", "hibernate"],
                    "lock": ["loginctl", "lock-session"],
                }
            elif is_windows():
                cmds = {
                    "shutdown": ["shutdown", "/s", f"/t {delay}"],
                    "restart": ["shutdown", "/r", f"/t {delay}"],
                    "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                    "hibernate": ["shutdown", "/h"],
                    "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
                }
            elif is_mac():
                cmds = {
                    "shutdown": ["osascript", "-e", 'tell app "System Events" to shut down'],
                    "restart": ["osascript", "-e", 'tell app "System Events" to restart'],
                    "sleep": ["pmset", "sleepnow"],
                    "lock": ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"],
                }
            else:
                return "Unsupported OS"

            cmd = cmds.get(action)
            if not cmd:
                return f"Unknown action: {action}"

            run_command(cmd, capture_output=False)
            return f"Power action '{action}' executed"
        except Exception as e:
            return f"Error: {e}"

    def control_volume(self, action: str, level: int = None) -> str:
        try:
            if is_linux():
                if action == "up":
                    run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])
                    return "Volume increased by 5%"
                elif action == "down":
                    run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])
                    return "Volume decreased by 5%"
                elif action == "mute":
                    run_command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"])
                    return "Volume muted"
                elif action == "unmute":
                    run_command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"])
                    return "Volume unmuted"
                elif action == "set" and level is not None:
                    run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"])
                    return f"Volume set to {level}%"
                elif action == "get":
                    out, _, _ = run_command(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
                    return f"Current volume: {out}"
            elif is_windows():
                if action == "mute":
                    run_command(["nircmd.exe", "mutesysvolume", "1"])
                elif action == "unmute":
                    run_command(["nircmd.exe", "mutesysvolume", "0"])
                elif action == "set" and level is not None:
                    vol = int(level * 655.35)
                    run_command(["nircmd.exe", "setsysvolume", str(vol)])
                return f"Volume action '{action}' done"
            elif is_mac():
                if action == "set" and level is not None:
                    run_command(["osascript", "-e", f"set volume output volume {level}"])
                elif action == "mute":
                    run_command(["osascript", "-e", "set volume with output muted"])
                elif action == "unmute":
                    run_command(["osascript", "-e", "set volume without output muted"])
                elif action == "up":
                    run_command(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
                elif action == "down":
                    run_command(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
                return f"Volume action '{action}' done"
        except Exception as e:
            return f"Volume error: {e}"
        return "Volume action completed"

    def control_brightness(self, action: str, level: int = None) -> str:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness(display=0)
            if isinstance(current, list):
                current = current[0]
            if action == "get":
                return f"Current brightness: {current}%"
            elif action == "up":
                new = min(100, current + 10)
                sbc.set_brightness(new, display=0)
                return f"Brightness increased to {new}%"
            elif action == "down":
                new = max(0, current - 10)
                sbc.set_brightness(new, display=0)
                return f"Brightness decreased to {new}%"
            elif action == "set" and level is not None:
                sbc.set_brightness(level, display=0)
                return f"Brightness set to {level}%"
        except ImportError:
            if is_linux():
                if action == "up":
                    run_command(["brightnessctl", "set", "+10%"])
                elif action == "down":
                    run_command(["brightnessctl", "set", "10%-"])
                elif action == "set" and level is not None:
                    run_command(["brightnessctl", "set", f"{level}%"])
                return f"Brightness action '{action}' done"
        except Exception as e:
            return f"Brightness error: {e}"
        return "Brightness adjusted"

    def launch_application(self, app_name: str) -> str:
        app = app_name.lower().strip()
        app_map = {
            "chrome": ["google-chrome", "chromium", "chromium-browser"],
            "firefox": ["firefox"],
            "vscode": ["code"],
            "vs code": ["code"],
            "terminal": ["gnome-terminal", "xterm", "konsole"],
            "files": ["nautilus", "thunar", "nemo"],
            "calculator": ["gnome-calculator", "kcalc", "xcalc"],
            "text editor": ["gedit", "mousepad", "kate"],
            "spotify": ["spotify"],
            "vlc": ["vlc"],
            "gimp": ["gimp"],
            "discord": ["discord"],
            "slack": ["slack"],
            "zoom": ["zoom"],
            "steam": ["steam"],
        }
        candidates = app_map.get(app, [app])
        for candidate in candidates:
            try:
                subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Launched {app_name}"
            except FileNotFoundError:
                continue
        return f"Could not find application: {app_name}"

    def take_screenshot(self, filename: str = None, region: str = "full") -> str:
        import datetime, os

        # Screenshots folder — web portal se serve hogi
        ss_dir = Path.home() / "Pictures" / "nova_screenshots"
        ss_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"screenshot_{ts}.png"
        filepath = ss_dir / fname

        # Linux: DISPLAY aur WAYLAND_DISPLAY auto-set
        if is_linux():
            if not os.environ.get("DISPLAY"):
                os.environ["DISPLAY"] = ":0"
            if not os.environ.get("WAYLAND_DISPLAY"):
                os.environ["WAYLAND_DISPLAY"] = "wayland-0"

        # Try karo multiple tools — jo pehla kaam kare
        taken = (
            self._ss_pyautogui(filepath)
            or self._ss_scrot(filepath)
            or self._ss_gnome(filepath)
            or self._ss_grim(filepath)       # Wayland
            or self._ss_import(filepath)     # ImageMagick
            or self._ss_xwd(filepath)        # xwd fallback
        )

        if taken and filepath.exists():
            return f"Screenshot le li! [IMG:/screenshots/{fname}]"
        return (
            "Screenshot nahi le saka. Possible fixes:\n"
            "  sudo apt install scrot   (X11)\n"
            "  sudo apt install grim    (Wayland)\n"
            "  pip install pyautogui Pillow\n"
            f"  DISPLAY={os.environ.get('DISPLAY','?')}  WAYLAND={os.environ.get('WAYLAND_DISPLAY','?')}"
        )

    # ── Screenshot backends ──────────────────────────────

    def _ss_pyautogui(self, path: Path) -> bool:
        try:
            import pyautogui
            pyautogui.screenshot().save(str(path))
            return path.exists()
        except Exception:
            return False

    def _ss_scrot(self, path: Path) -> bool:
        _, _, code = run_command(["scrot", str(path)])
        return code == 0 and path.exists()

    def _ss_gnome(self, path: Path) -> bool:
        _, _, code = run_command(["gnome-screenshot", "-f", str(path)])
        return code == 0 and path.exists()

    def _ss_grim(self, path: Path) -> bool:
        _, _, code = run_command(["grim", str(path)])
        return code == 0 and path.exists()

    def _ss_import(self, path: Path) -> bool:
        _, _, code = run_command(["import", "-window", "root", str(path)])
        return code == 0 and path.exists()

    def _ss_xwd(self, path: Path) -> bool:
        import tempfile
        xwd_path = str(path).replace(".png", ".xwd")
        _, _, c1 = run_command(["xwd", "-root", "-silent", "-out", xwd_path])
        if c1 == 0:
            _, _, c2 = run_command(["convert", xwd_path, str(path)])
            try:
                Path(xwd_path).unlink()
            except Exception:
                pass
            return c2 == 0 and path.exists()
        return False

    def manage_wifi(self, action: str, network_name: str = None, password: str = None) -> str:
        try:
            if is_linux():
                if action == "list":
                    out, _, _ = run_command(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
                    return out or "No networks found"
                elif action == "connect" and network_name:
                    if password:
                        out, err, code = run_command(["nmcli", "device", "wifi", "connect", network_name, "password", password])
                    else:
                        out, err, code = run_command(["nmcli", "device", "wifi", "connect", network_name])
                    return out if code == 0 else f"Failed: {err}"
                elif action == "disconnect":
                    out, err, code = run_command(["nmcli", "device", "disconnect", "wifi"])
                    return out if code == 0 else f"Failed: {err}"
                elif action == "status":
                    out, _, _ = run_command(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device", "status"])
                    return out or "WiFi status unavailable"
            elif is_windows():
                if action == "list":
                    out, _, _ = run_command(["netsh", "wlan", "show", "networks"])
                    return out
                elif action == "status":
                    out, _, _ = run_command(["netsh", "wlan", "show", "interfaces"])
                    return out
        except Exception as e:
            return f"WiFi error: {e}"
        return "WiFi action completed"

    def check_network_speed(self) -> str:
        try:
            import requests
            import time
            url = "http://speed.cloudflare.com/__down?bytes=10000000"
            start = time.time()
            resp = requests.get(url, timeout=30, stream=True)
            total = 0
            for chunk in resp.iter_content(1024 * 64):
                total += len(chunk)
            elapsed = time.time() - start
            speed_mbps = (total * 8) / (elapsed * 1_000_000)

            net1 = psutil.net_io_counters()
            time.sleep(1)
            net2 = psutil.net_io_counters()
            recv_kbps = (net2.bytes_recv - net1.bytes_recv) / 1024
            return (
                f"Download speed: ~{speed_mbps:.1f} Mbps\n"
                f"Current recv rate: {recv_kbps:.0f} KB/s"
            )
        except Exception as e:
            return f"Speed test failed: {e}"

    def manage_task_manager(self, action: str, process_name: str = None) -> str:
        try:
            if action == "list":
                procs = []
                for p in psutil.process_iter(["pid", "name", "status"]):
                    procs.append(f"{p.info['pid']:>6}  {p.info['name']:<30}  {p.info['status']}")
                return "\n".join(procs[:30])

            elif action == "kill" and process_name:
                killed = []
                for p in psutil.process_iter(["pid", "name"]):
                    if process_name.lower() in p.info["name"].lower():
                        p.terminate()
                        killed.append(p.info["name"])
                return f"Killed: {', '.join(killed)}" if killed else f"No process found: {process_name}"

            elif action == "top_cpu":
                procs = sorted(
                    psutil.process_iter(["pid", "name", "cpu_percent"]),
                    key=lambda p: p.info.get("cpu_percent", 0) or 0,
                    reverse=True,
                )
                lines = [f"{p.info['name']:<30}  CPU: {p.info['cpu_percent']}%" for p in procs[:10]]
                return "\n".join(lines)

            elif action == "top_ram":
                procs = sorted(
                    psutil.process_iter(["pid", "name", "memory_percent"]),
                    key=lambda p: p.info.get("memory_percent", 0) or 0,
                    reverse=True,
                )
                lines = [f"{p.info['name']:<30}  RAM: {p.info['memory_percent']:.1f}%" for p in procs[:10]]
                return "\n".join(lines)

        except Exception as e:
            return f"Task manager error: {e}"
        return "Task manager action completed"

    def empty_trash(self) -> str:
        try:
            if is_linux():
                trash = Path.home() / ".local/share/Trash"
                import shutil
                for sub in ["files", "info", "expunged"]:
                    p = trash / sub
                    if p.exists():
                        for item in p.iterdir():
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                return "Trash emptied"
            elif is_windows():
                run_command(["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"])
                return "Recycle bin emptied"
            elif is_mac():
                run_command(["osascript", "-e", 'tell app "Finder" to empty trash'])
                return "Trash emptied"
        except Exception as e:
            return f"Error emptying trash: {e}"

    def control_mic(self, action: str) -> str:
        try:
            if is_linux():
                if action == "mute":
                    run_command(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1"])
                    return "Microphone muted"
                elif action == "unmute":
                    run_command(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"])
                    return "Microphone unmuted"
                elif action == "toggle":
                    run_command(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"])
                    return "Microphone toggled"
                elif action == "status":
                    out, _, _ = run_command(["pactl", "get-source-mute", "@DEFAULT_SOURCE@"])
                    return f"Microphone: {out}"
            elif is_mac():
                if action == "mute":
                    run_command(["osascript", "-e", "set volume input volume 0"])
                elif action == "unmute":
                    run_command(["osascript", "-e", "set volume input volume 50"])
                return f"Microphone {action}d"
        except Exception as e:
            return f"Mic error: {e}"
        return "Mic action done"

    def toggle_night_mode(self, enable: bool) -> str:
        try:
            if is_linux():
                if enable:
                    run_command(["gsettings", "set", "org.gnome.settings-daemon.plugins.color", "night-light-enabled", "true"])
                    return "Night mode / blue light filter enabled"
                else:
                    run_command(["gsettings", "set", "org.gnome.settings-daemon.plugins.color", "night-light-enabled", "false"])
                    return "Night mode disabled"
            elif is_windows():
                import winreg
                key = winreg.HKEY_CURRENT_USER
                sub = r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\DefaultAccount\Current\default$windows.data.bluelightreduction.settings"
                return "Night mode toggled (please enable manually in Windows Settings)"
            elif is_mac():
                if enable:
                    run_command(["osascript", "-e", 'tell application "System Events" to tell appearance preferences to set dark mode to true'])
                    return "Dark mode enabled"
                else:
                    run_command(["osascript", "-e", 'tell application "System Events" to tell appearance preferences to set dark mode to false'])
                    return "Dark mode disabled"
        except Exception as e:
            return f"Night mode error: {e}"

    def sync_time(self) -> str:
        try:
            if is_linux():
                out, err, code = run_command(["timedatectl", "set-ntp", "true"])
                if code == 0:
                    return "System time synchronized with NTP"
                return f"Time sync: {err or 'done'}"
            elif is_windows():
                run_command(["w32tm", "/resync"])
                return "Windows time synchronized"
            elif is_mac():
                run_command(["sntp", "-sS", "time.apple.com"])
                return "Time synchronized"
        except Exception as e:
            return f"Time sync error: {e}"

    def clean_disk(self) -> str:
        import shutil, tempfile
        cleaned = []
        freed = 0
        try:
            tmp = Path(tempfile.gettempdir())
            for item in tmp.iterdir():
                try:
                    size = item.stat().st_size if item.is_file() else 0
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink()
                    freed += size
                    cleaned.append(str(item.name))
                except Exception:
                    pass
        except Exception:
            pass

        if is_linux():
            caches = [
                Path.home() / ".cache",
                Path("/var/tmp"),
            ]
            for cache in caches:
                if cache.exists():
                    for item in cache.iterdir():
                        try:
                            size = item.stat().st_size if item.is_file() else 0
                            if item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                            else:
                                item.unlink()
                            freed += size
                        except Exception:
                            pass

        return f"Disk cleaned. Freed approximately {freed / (1024**2):.1f} MB"

    def manage_bluetooth(self, action: str, device_name: str = None) -> str:
        try:
            if is_linux():
                if action == "list":
                    out, _, _ = run_command(["bluetoothctl", "devices"])
                    return out or "No Bluetooth devices paired"
                elif action == "connect" and device_name:
                    out, err, code = run_command(["bluetoothctl", "connect", device_name])
                    return out if code == 0 else f"Failed: {err}"
                elif action == "disconnect" and device_name:
                    out, err, code = run_command(["bluetoothctl", "disconnect", device_name])
                    return out if code == 0 else f"Failed: {err}"
                elif action == "status":
                    out, _, _ = run_command(["bluetoothctl", "show"])
                    return out or "Bluetooth status unavailable"
        except Exception as e:
            return f"Bluetooth error: {e}"
        return "Bluetooth action completed"

    def control_webcam(self, action: str) -> str:
        try:
            if action == "capture":
                import cv2, datetime
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    return "No webcam found"
                ret, frame = cap.read()
                cap.release()
                if ret:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = str(Path.home() / "Pictures" / f"webcam_{ts}.jpg")
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(filename, frame)
                    return f"Webcam photo saved to {filename}"
                return "Failed to capture from webcam"
            elif action == "status":
                import cv2
                cap = cv2.VideoCapture(0)
                available = cap.isOpened()
                cap.release()
                return "Webcam is available" if available else "No webcam found"
        except ImportError:
            return "OpenCV not installed. Run: pip install opencv-python-headless"
        except Exception as e:
            return f"Webcam error: {e}"
