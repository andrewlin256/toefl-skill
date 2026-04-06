#!/usr/bin/env python3
"""
TOEFL Skill Environment Setup
Sets up uv, .venv, and all dependencies.

Usage:
    python setup_env.py [--target ./my-project]
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PYPROJECT_TOML = """\
[project]
name = "toefl-prep"
version = "1.0.0"
description = "TOEFL iBT 2026 Study Environment"
requires-python = ">=3.10"
dependencies = [
    "edge-tts>=7.0.0",
    "genanki>=0.13.0",
    "pydub>=0.25.1",
]

[project.optional-dependencies]
offline-tts = ["kokoro>=0.9.2", "soundfile"]
"""


def run(cmd: list[str], check=True, **kwargs):
    """Run a command, print it, and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kwargs)


def ensure_uv():
    """Install uv if not present."""
    if shutil.which("uv"):
        print("✅ uv already installed")
        return
    print("📦 Installing uv...")
    r = run(["pip", "install", "uv", "--break-system-packages"], check=False)
    if r.returncode != 0:
        # Try pipx or curl fallback
        r2 = run(["curl", "-LsSf", "https://astral.sh/uv/install.sh"], check=False)
        if r2.returncode == 0:
            run(["sh", "-c", r2.stdout], check=False)
    if shutil.which("uv"):
        print("✅ uv installed")
    else:
        print("⚠️  Could not install uv globally. Falling back to pip.")


def ensure_ffmpeg():
    """Check for ffmpeg (needed by pydub for audio concat)."""
    if shutil.which("ffmpeg"):
        print("✅ ffmpeg available")
        return True
    print("⚠️  ffmpeg not found — audio concatenation features will be limited")
    print("   Install: apt install ffmpeg  /  brew install ffmpeg")
    return False


def setup(target: Path):
    """Full environment setup."""
    print("=" * 50)
    print("🎯 TOEFL Prep Environment Setup")
    print("=" * 50)

    # 1. Ensure uv
    ensure_uv()

    # 2. Write pyproject.toml
    toml_path = target / "pyproject.toml"
    if not toml_path.exists():
        with open(toml_path, "w") as f:
            f.write(PYPROJECT_TOML)
        print(f"✅ Created {toml_path}")
    else:
        print(f"✅ {toml_path} already exists")

    # 3. Create venv + install deps
    if shutil.which("uv"):
        print("\n📦 Creating .venv and installing dependencies with uv...")
        run(["uv", "venv", str(target / ".venv")], check=False, cwd=str(target))
        run(["uv", "pip", "install", "-e", "."], check=False, cwd=str(target))
        print("✅ Dependencies installed via uv")
    else:
        print("\n📦 Falling back to pip...")
        run([sys.executable, "-m", "venv", str(target / ".venv")], check=False)
        pip_path = target / ".venv" / "bin" / "pip"
        if pip_path.exists():
            run([str(pip_path), "install", "edge-tts", "genanki", "pydub"], check=False)
        else:
            run([sys.executable, "-m", "pip", "install", "--break-system-packages",
                 "edge-tts", "genanki", "pydub"], check=False)
        print("✅ Dependencies installed via pip")

    # 4. Check ffmpeg
    ensure_ffmpeg()

    # 5. Write .gitignore
    gitignore_path = target / ".gitignore"
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write(".venv/\n__pycache__/\n*.pyc\n*.apkg\n*.mp3\n*.wav\n")
        print(f"✅ Created {gitignore_path}")

    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print(f"   Run scripts with: uv run python scripts/xxx.py")
    print(f"   Or activate venv: source {target / '.venv' / 'bin' / 'activate'}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=".", help="Project root directory")
    args = parser.parse_args()
    setup(Path(args.target).resolve())
