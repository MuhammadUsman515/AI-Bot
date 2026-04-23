import os
import subprocess
import tempfile
import json
from pathlib import Path
from nova.utils.helpers import run_command, is_linux, is_windows, is_mac


LANG_EXTENSIONS = {
    "python": ".py", "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "java": ".java",
    "c": ".c",
    "cpp": ".cpp", "c++": ".cpp",
    "go": ".go",
    "rust": ".rs",
    "ruby": ".rb",
    "php": ".php",
    "bash": ".sh", "shell": ".sh",
}

LANG_RUNNERS = {
    ".py": ["python3", "{file}"],
    ".js": ["node", "{file}"],
    ".ts": ["ts-node", "{file}"],
    ".rb": ["ruby", "{file}"],
    ".php": ["php", "{file}"],
    ".go": ["go", "run", "{file}"],
    ".sh": ["bash", "{file}"],
}


class Developer:

    def __init__(self, config):
        self.config = config

    # ── Tool Definitions ────────────────────────────────────────────────────

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "run_code",
                "description": "Execute a code snippet in any language and return the output",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to execute"},
                        "language": {"type": "string", "description": "Programming language (python, js, bash, etc.)"},
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "git_operation",
                "description": "Perform git operations: status, add, commit, push, pull, branch, log, clone",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["status", "add", "commit", "push", "pull", "branch", "log", "diff", "clone", "init", "stash"],
                            "description": "Git operation"
                        },
                        "args": {"type": "string", "description": "Additional arguments (e.g. commit message, branch name, repo URL)"},
                        "path": {"type": "string", "description": "Repository path (default: current directory)"},
                    },
                    "required": ["operation"]
                }
            },
            {
                "name": "run_linux_command",
                "description": "Run a Linux/shell command and return output",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to run"},
                        "working_directory": {"type": "string", "description": "Working directory for the command"},
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "test_api",
                "description": "Make HTTP API requests (GET, POST, PUT, DELETE) and show the response",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "API endpoint URL"},
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                            "description": "HTTP method"
                        },
                        "headers": {"type": "object", "description": "Request headers as key-value pairs"},
                        "body": {"type": "object", "description": "Request body as JSON object"},
                        "params": {"type": "object", "description": "Query parameters"},
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "manage_docker",
                "description": "Manage Docker containers: list, start, stop, remove, pull, ps",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["ps", "images", "start", "stop", "rm", "pull", "logs", "exec"],
                            "description": "Docker action"
                        },
                        "target": {"type": "string", "description": "Container name/ID or image name"},
                        "args": {"type": "string", "description": "Additional arguments"},
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "format_code",
                "description": "Format/beautify code in Python, JS, JSON, HTML, CSS",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to format"},
                        "language": {"type": "string", "description": "Language: python, json, js, html, css"},
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "check_code_security",
                "description": "Perform a basic security audit of code for common vulnerabilities",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to audit"},
                        "language": {"type": "string", "description": "Programming language"},
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "manage_packages",
                "description": "Install, uninstall, or list packages for pip, npm, apt, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["install", "uninstall", "list", "update"],
                            "description": "Package action"
                        },
                        "package": {"type": "string", "description": "Package name (for install/uninstall)"},
                        "manager": {
                            "type": "string",
                            "enum": ["pip", "npm", "apt", "brew", "cargo", "gem"],
                            "description": "Package manager (default: pip)"
                        },
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "create_project_structure",
                "description": "Create a new project scaffolding for Python, Node, React, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_type": {
                            "type": "string",
                            "enum": ["python", "node", "react", "flask", "fastapi", "django", "rust", "go"],
                            "description": "Project type"
                        },
                        "project_name": {"type": "string", "description": "Project name"},
                        "location": {"type": "string", "description": "Where to create the project"},
                    },
                    "required": ["project_type", "project_name"]
                }
            },
            {
                "name": "search_code",
                "description": "Search for a pattern, function, or variable in code files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Pattern or keyword to search"},
                        "directory": {"type": "string", "description": "Directory to search in"},
                        "file_extension": {"type": "string", "description": "File type filter e.g. 'py', 'js'"},
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "open_editor",
                "description": "Open a file or folder in VS Code or another editor",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File or folder to open"},
                        "editor": {"type": "string", "description": "Editor: 'vscode', 'nano', 'vim' (default: vscode)"},
                    },
                    "required": ["path"]
                }
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "run_code": self.run_code,
            "git_operation": self.git_operation,
            "run_linux_command": self.run_linux_command,
            "test_api": self.test_api,
            "manage_docker": self.manage_docker,
            "format_code": self.format_code,
            "check_code_security": self.check_code_security,
            "manage_packages": self.manage_packages,
            "create_project_structure": self.create_project_structure,
            "search_code": self.search_code,
            "open_editor": self.open_editor,
        }

    # ── Implementations ──────────────────────────────────────────────────────

    def run_code(self, code: str, language: str) -> str:
        lang = language.lower().strip()
        ext = LANG_EXTENSIONS.get(lang, f".{lang}")

        if ext == ".py":
            return self._run_python(code)

        if ext not in LANG_RUNNERS:
            return f"Unsupported language: {language}. Supported: {list(LANG_EXTENSIONS.keys())}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
            f.write(code)
            tmp_path = f.name
        try:
            runner_template = LANG_RUNNERS[ext]
            cmd = [c.replace("{file}", tmp_path) for c in runner_template]
            out, err, code_rc = run_command(cmd)
            result = out or ""
            if err:
                result += f"\nSTDERR:\n{err}"
            return result or "(no output)"
        finally:
            os.unlink(tmp_path)

    def _run_python(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp = f.name
        try:
            out, err, _ = run_command(["python3", tmp])
            result = out or ""
            if err:
                result += f"\nError:\n{err}"
            return result or "(no output)"
        finally:
            os.unlink(tmp)

    def git_operation(self, operation: str, args: str = None, path: str = None) -> str:
        cwd = path or os.getcwd()
        cmd_map = {
            "status": ["git", "status"],
            "add": ["git", "add"] + (args.split() if args else ["."]),
            "commit": ["git", "commit", "-m", args or "Update"],
            "push": ["git", "push"] + (args.split() if args else []),
            "pull": ["git", "pull"] + (args.split() if args else []),
            "branch": ["git", "branch"] + (args.split() if args else []),
            "log": ["git", "log", "--oneline", "-10"],
            "diff": ["git", "diff"] + (args.split() if args else []),
            "clone": ["git", "clone"] + (args.split() if args else []),
            "init": ["git", "init"],
            "stash": ["git", "stash"] + (args.split() if args else []),
        }
        cmd = cmd_map.get(operation)
        if not cmd:
            return f"Unknown operation: {operation}"
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=60
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if result.returncode != 0 and err:
                return f"Git error:\n{err}"
            return out or err or f"git {operation} completed"
        except Exception as e:
            return f"Git error: {e}"

    def run_linux_command(self, command: str, working_directory: str = None) -> str:
        cwd = working_directory or os.getcwd()
        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=30
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if result.returncode != 0 and err:
                return f"Error (code {result.returncode}):\n{err}"
            return out or err or "(no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Command error: {e}"

    def test_api(self, url: str, method: str = "GET", headers: dict = None,
                 body: dict = None, params: dict = None) -> str:
        try:
            import requests
            kwargs = {"timeout": 15}
            if headers:
                kwargs["headers"] = headers
            if params:
                kwargs["params"] = params
            if body:
                kwargs["json"] = body

            resp = getattr(requests, method.lower())(url, **kwargs)

            result_lines = [
                f"Status: {resp.status_code} {resp.reason}",
                f"Time: {resp.elapsed.total_seconds():.2f}s",
                f"Headers: {dict(resp.headers)}",
            ]

            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                try:
                    body_str = json.dumps(resp.json(), indent=2)[:2000]
                    result_lines.append(f"Body:\n{body_str}")
                except Exception:
                    result_lines.append(f"Body:\n{resp.text[:2000]}")
            else:
                result_lines.append(f"Body:\n{resp.text[:2000]}")

            return "\n".join(result_lines)
        except Exception as e:
            return f"API test error: {e}"

    def manage_docker(self, action: str, target: str = None, args: str = None) -> str:
        cmd_map = {
            "ps": ["docker", "ps", "-a"],
            "images": ["docker", "images"],
            "start": ["docker", "start"] + ([target] if target else []),
            "stop": ["docker", "stop"] + ([target] if target else []),
            "rm": ["docker", "rm"] + ([target] if target else []),
            "pull": ["docker", "pull"] + ([target] if target else []),
            "logs": ["docker", "logs"] + ([target] if target else []),
            "exec": ["docker", "exec", "-it"] + ([target] + (args.split() if args else []) if target else []),
        }
        cmd = cmd_map.get(action)
        if not cmd:
            return f"Unknown Docker action: {action}"
        out, err, code = run_command(cmd)
        return out or err or f"Docker {action} completed"

    def format_code(self, code: str, language: str) -> str:
        lang = language.lower()
        if lang == "json":
            try:
                parsed = json.loads(code)
                return json.dumps(parsed, indent=2)
            except Exception as e:
                return f"JSON format error: {e}"

        if lang == "python":
            try:
                import ast
                ast.parse(code)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(code)
                    tmp = f.name
                out, err, rc = run_command(["black", "--quiet", tmp])
                if rc == 0:
                    formatted = Path(tmp).read_text()
                    os.unlink(tmp)
                    return formatted
                os.unlink(tmp)
            except Exception:
                pass
            return code

        if lang in ("js", "javascript", "ts", "typescript", "css", "html"):
            with tempfile.NamedTemporaryFile(mode="w", suffix=f".{lang}", delete=False) as f:
                f.write(code)
                tmp = f.name
            out, err, rc = run_command(["prettier", "--write", tmp])
            if rc == 0:
                formatted = Path(tmp).read_text()
                os.unlink(tmp)
                return formatted
            os.unlink(tmp)
            return code

        return code

    def check_code_security(self, code: str, language: str) -> str:
        issues = []
        lang = language.lower()

        common_patterns = [
            ("eval(", "Dangerous: eval() can execute arbitrary code"),
            ("exec(", "Dangerous: exec() can execute arbitrary code"),
            ("os.system(", "Risk: os.system() is vulnerable to shell injection"),
            ("subprocess.call(shell=True", "Risk: shell=True enables shell injection"),
            ("password", "Review: hardcoded password detected"),
            ("secret", "Review: hardcoded secret detected"),
            ("api_key", "Review: hardcoded API key detected"),
            ("TODO", "Info: TODO comment found - incomplete implementation"),
            ("FIXME", "Info: FIXME comment found"),
        ]

        if lang == "python":
            common_patterns += [
                ("pickle.loads(", "Risk: pickle deserialization can execute code"),
                ("yaml.load(", "Risk: yaml.load without Loader is unsafe"),
                ("input(", "Review: user input - ensure proper validation"),
                ("open(", "Review: file operation - check path traversal"),
            ]

        if lang in ("js", "javascript"):
            common_patterns += [
                ("innerHTML", "Risk: innerHTML can lead to XSS"),
                ("document.write(", "Risk: document.write can lead to XSS"),
                ("dangerouslySetInnerHTML", "Risk: React XSS vulnerability possible"),
            ]

        if lang == "php":
            common_patterns += [
                ("$_GET[", "Risk: unsanitized GET input"),
                ("$_POST[", "Risk: unsanitized POST input"),
                ("mysql_query(", "Risk: use PDO/prepared statements instead"),
            ]

        for line_num, line in enumerate(code.splitlines(), 1):
            for pattern, msg in common_patterns:
                if pattern in line:
                    issues.append(f"Line {line_num}: {msg}\n  → {line.strip()}")

        if not issues:
            return "No obvious security issues found. Consider a full security audit for production code."

        return f"Security audit results ({len(issues)} issue(s) found):\n\n" + "\n\n".join(issues)

    def manage_packages(self, action: str, package: str = None, manager: str = "pip") -> str:
        cmd_map = {
            "pip": {
                "install": ["pip", "install", package or ""],
                "uninstall": ["pip", "uninstall", "-y", package or ""],
                "list": ["pip", "list"],
                "update": ["pip", "install", "--upgrade", package or "pip"],
            },
            "npm": {
                "install": ["npm", "install", package or ""],
                "uninstall": ["npm", "uninstall", package or ""],
                "list": ["npm", "list"],
                "update": ["npm", "update", package or ""],
            },
            "apt": {
                "install": ["sudo", "apt", "install", "-y", package or ""],
                "uninstall": ["sudo", "apt", "remove", "-y", package or ""],
                "list": ["apt", "list", "--installed"],
                "update": ["sudo", "apt", "update"],
            },
        }
        if manager not in cmd_map:
            return f"Unknown package manager: {manager}"
        cmd = cmd_map[manager].get(action)
        if not cmd:
            return f"Unknown action: {action}"
        out, err, code = run_command(cmd)
        return out or err or f"{manager} {action} completed"

    def create_project_structure(self, project_type: str, project_name: str, location: str = None) -> str:
        base = Path(location) if location else Path.home() / "Projects"
        project_dir = base / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        templates = {
            "python": {
                f"{project_name}/__init__.py": "",
                f"{project_name}/main.py": f'"""Main module for {project_name}"""\n\ndef main():\n    print("Hello from {project_name}!")\n\nif __name__ == "__main__":\n    main()\n',
                "requirements.txt": "# Add dependencies here\n",
                "README.md": f"# {project_name}\n\nPython project.\n",
                ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n",
            },
            "flask": {
                "app/__init__.py": 'from flask import Flask\napp = Flask(__name__)\nfrom app import routes\n',
                "app/routes.py": 'from app import app\n\n@app.route("/")\ndef index():\n    return "Hello, World!"\n',
                "run.py": 'from app import app\nif __name__ == "__main__":\n    app.run(debug=True)\n',
                "requirements.txt": "flask\npython-dotenv\n",
                ".env": "FLASK_APP=run.py\nFLASK_ENV=development\n",
                ".gitignore": "venv/\n.env\n__pycache__/\n",
            },
            "node": {
                "src/index.js": 'console.log("Hello from {project_name}!");\n'.replace("{project_name}", project_name),
                "package.json": json.dumps({"name": project_name, "version": "1.0.0", "main": "src/index.js", "scripts": {"start": "node src/index.js"}}, indent=2),
                "README.md": f"# {project_name}\n",
                ".gitignore": "node_modules/\n.env\n",
            },
            "react": {
                "src/App.jsx": f'export default function App() {{\n  return <h1>Hello from {project_name}</h1>;\n}}\n',
                "src/main.jsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\nReactDOM.createRoot(document.getElementById("root")).render(<App />);\n',
                "index.html": f'<!DOCTYPE html>\n<html>\n<head><title>{project_name}</title></head>\n<body>\n<div id="root"></div>\n</body>\n</html>\n',
                ".gitignore": "node_modules/\ndist/\n.env\n",
            },
        }

        template = templates.get(project_type, templates["python"])
        created = []
        for rel_path, content in template.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created.append(str(file_path))

        return f"{project_type.capitalize()} project '{project_name}' created at {project_dir}\nFiles created:\n" + "\n".join(f"  {f}" for f in created)

    def search_code(self, pattern: str, directory: str = None, file_extension: str = None) -> str:
        search_dir = directory or os.getcwd()
        ext = f"*.{file_extension.lstrip('.')}" if file_extension else "*.*"
        try:
            if is_linux() or is_mac():
                cmd = ["grep", "-rn", "--include", ext, pattern, search_dir]
                out, err, code = run_command(cmd)
                if out:
                    lines = out.splitlines()[:30]
                    return f"Found {len(out.splitlines())} match(es):\n" + "\n".join(lines)
                return f"No matches for '{pattern}'"
            else:
                results = []
                for fp in Path(search_dir).rglob(ext):
                    try:
                        content = fp.read_text(errors="replace")
                        for i, line in enumerate(content.splitlines(), 1):
                            if pattern.lower() in line.lower():
                                results.append(f"{fp}:{i}: {line.strip()}")
                                if len(results) >= 30:
                                    break
                    except Exception:
                        pass
                if results:
                    return f"Found {len(results)} match(es):\n" + "\n".join(results)
                return f"No matches for '{pattern}'"
        except Exception as e:
            return f"Search error: {e}"

    def open_editor(self, path: str, editor: str = "vscode") -> str:
        editors = {
            "vscode": ["code", path],
            "code": ["code", path],
            "nano": ["nano", path],
            "vim": ["vim", path],
            "gedit": ["gedit", path],
        }
        cmd = editors.get(editor.lower(), ["code", path])
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened '{path}' in {editor}"
        except FileNotFoundError:
            return f"Editor '{editor}' not found"
        except Exception as e:
            return f"Error opening editor: {e}"
