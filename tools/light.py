"""
Light control tool — turns a Tapo smart light on or off via python-kasa.

Requires:
  pip install python-kasa

Env vars (set in .env):
  KASA_USERNAME — Tapo/Kasa account email
  KASA_PASSWORD — Tapo/Kasa account password
  TAPO_HOST     — IP address of the Tapo bulb/plug on the local network
"""

import asyncio
import config


TURN_ON_SCHEMA = {
    "name": "turn_on_light",
    "description": "Turn on the Tapo smart light.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

TURN_OFF_SCHEMA = {
    "name": "turn_off_light",
    "description": "Turn off the Tapo smart light.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}


async def _set_light(on: bool) -> str:
    try:
        from kasa import Discover, Credentials
    except ImportError:
        return "Error: python-kasa not installed. Run: pip install python-kasa"

    if not config.TAPO_HOST:
        return "Error: TAPO_HOST is not set in .env"
    if not config.KASA_USERNAME or not config.KASA_PASSWORD:
        return "Error: KASA_USERNAME or KASA_PASSWORD is not set in .env"

    credentials = Credentials(config.KASA_USERNAME, config.KASA_PASSWORD)
    device = await Discover.discover_single(
        config.TAPO_HOST,
        credentials=credentials,
    )
    await device.update()

    if on:
        await device.turn_on()
        return "Light turned on."
    else:
        await device.turn_off()
        return "Light turned off."


def turn_on_light() -> str:
    """Turn the Tapo light on."""
    return asyncio.run(_set_light(on=True))


def turn_off_light() -> str:
    """Turn the Tapo light off."""
    return asyncio.run(_set_light(on=False))
