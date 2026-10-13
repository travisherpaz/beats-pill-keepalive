#!/usr/bin/env python3
"""Keeps a USB/line-connected Beats Pill (or any auto-sleeping speaker) awake
by periodically playing a near-inaudible ping on macOS's current default output device.
"""

import array
import json
import math
import os
import subprocess
import time
import wave

APP_DIR = os.path.expanduser("~/Library/Application Support/BeatsKeepAlive")
SILENCE_FILE = os.path.join(APP_DIR, "silence.wav")
META_FILE = os.path.join(APP_DIR, "silence.meta.json")
LOG_FILE = os.path.join(APP_DIR, "keepalive.log")

SAMPLE_RATE = 44100
CHANNELS = 2
DURATION_SEC = 1.0     # length of each ping
FREQUENCY_HZ = 19000    # near-ultrasonic tone: inaudible to most adults, but real AC signal
AMPLITUDE = 40          # out of 32767 (~ -58 dBFS), very quiet
INTERVAL_SEC = 20       # seconds between pings; must be well under the 60-min auto-sleep window
DIAG_EVERY_N_PINGS = 15  # roughly every 5 minutes at INTERVAL_SEC=20; log the default output device

# NOTE: a *constant* (DC) "silent" sample is a bad idea here - real speaker/amp
# circuits have AC-coupling (DC-blocking) capacitors that filter DC out before
# it ever reaches the auto-sleep detection logic, so it can look like "no signal"
# no matter how high you set the amplitude. Using a real (if tiny and inaudible)
# AC tone avoids that trap.

CURRENT_SETTINGS = {
    "sample_rate": SAMPLE_RATE,
    "channels": CHANNELS,
    "duration_sec": DURATION_SEC,
    "frequency_hz": FREQUENCY_HZ,
    "amplitude": AMPLITUDE,
}


def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def ensure_silence_file():
    os.makedirs(APP_DIR, exist_ok=True)

    if os.path.exists(SILENCE_FILE) and os.path.exists(META_FILE):
        try:
            with open(META_FILE) as f:
                saved = json.load(f)
            if saved == CURRENT_SETTINGS:
                return
        except (OSError, json.JSONDecodeError):
            pass
        log("settings changed - regenerating silence file")

    n_frames = int(SAMPLE_RATE * DURATION_SEC)
    samples = array.array("h")
    for i in range(n_frames):
        value = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY_HZ * i / SAMPLE_RATE))
        samples.append(value)  # left
        samples.append(value)  # right

    with wave.open(SILENCE_FILE, "w") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.tobytes())

    with open(META_FILE, "w") as f:
        json.dump(CURRENT_SETTINGS, f)

    log(f"generated silence file: {CURRENT_SETTINGS}")


def play_once():
    try:
        subprocess.run(
            ["afplay", SILENCE_FILE],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=DURATION_SEC + 5,
        )
    except subprocess.CalledProcessError as e:
        log(f"afplay failed: {e}")
    except subprocess.TimeoutExpired:
        log("afplay timed out")


def get_default_output_name():
    try:
        result = subprocess.run(
            ["system_profiler", "SPAudioDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        data = json.loads(result.stdout)
        for item in data.get("SPAudioDataType", []):
            for dev in item.get("_items", []):
                if dev.get("coreaudio_default_audio_output_device") == "spaudio_yes":
                    return dev.get("_name")
    except Exception as e:
        log(f"device-check failed: {e}")
    return None


def main():
    ensure_silence_file()
    log("keepalive loop started")

    initial_device = get_default_output_name()
    log(f"initial default output device: {initial_device}")

    ping_count = 0
    while True:
        play_once()
        ping_count += 1

        if ping_count % DIAG_EVERY_N_PINGS == 0:
            current_device = get_default_output_name()
            if current_device != initial_device:
                log(f"WARNING: default output device changed: '{initial_device}' -> '{current_device}'")
            else:
                log(f"device-check OK: default output still '{current_device}'")

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
