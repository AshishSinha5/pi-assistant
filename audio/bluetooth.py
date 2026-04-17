"""
Bluetooth profile switching for Sony XM5 on Pi (PipeWire/pactl).

Pi only — raises RuntimeError if called on any other platform.

HFP  = mic enabled, degraded audio quality (used while listening)
A2DP = high quality audio, mic disabled  (used while playing music)
"""

import subprocess
import sys


def _require_pi():
    if sys.platform == "darwin":
        raise RuntimeError("Bluetooth profile switching is Pi-only.")


def get_card_id() -> str:
    """Detect the bluez card ID for the XM5 at runtime."""
    _require_pi()
    result = subprocess.run(
        ["pactl", "list", "cards", "short"],
        capture_output=True, text=True, check=True,
    )
    for line in result.stdout.splitlines():
        if "bluez" in line.lower():
            return line.split()[1]
    raise RuntimeError("Could not find a Bluetooth (bluez) card via pactl. Is XM5 connected?")


def _is_profile_available(card: str, profile: str) -> bool:
    """Return True if the given profile is listed as available for this card."""
    result = subprocess.run(
        ["pactl", "list", "cards"],
        capture_output=True, text=True, check=True,
    )
    in_card = False
    for line in result.stdout.splitlines():
        if card in line:
            in_card = True
        if in_card and profile in line:
            return "available: yes" in line
    return False


def switch_to_a2dp() -> None:
    """Switch XM5 to A2DP (high-quality playback, mic off)."""
    _require_pi()
    card = get_card_id()
    subprocess.run(
        ["pactl", "set-card-profile", card, "a2dp_sink"],
        check=True,
    )
    print(f"[bt] Switched {card} → A2DP", flush=True)


def switch_to_hfp() -> None:
    """Switch XM5 to HFP (mic on, degraded audio).

    HFP requires ofono or hsphfpd to be running on the Pi for PipeWire to
    negotiate the codec. If the profile is unavailable, logs a warning and
    continues in A2DP mode (mic will not work).
    """
    _require_pi()
    card = get_card_id()
    if not _is_profile_available(card, "handsfree_head_unit"):
        print(
            "[bt] WARNING: HFP profile not available — mic will not work. "
            "Install ofono to enable HFP: sudo apt install ofono",
            flush=True,
        )
        return
    subprocess.run(
        ["pactl", "set-card-profile", card, "handsfree_head_unit"],
        check=True,
    )
    print(f"[bt] Switched {card} → HFP", flush=True)
