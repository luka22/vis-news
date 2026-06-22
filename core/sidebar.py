"""Fetch live sidebar data: sea conditions and sun times for Vis island."""
from datetime import datetime, UTC
import httpx

VIS_LAT = 43.06
VIS_LON = 16.19
TIMEOUT = 10

_WIND_DIRS = ["S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
              "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE"]


def _deg_to_compass(deg: float) -> str:
    return _WIND_DIRS[round(deg / 22.5) % 16]


def fetch_sea_conditions() -> dict:
    """Returns sea_temp, wave_height, wave_direction, wave_period or empty dict on error."""
    try:
        url = (
            "https://marine-api.open-meteo.com/v1/marine"
            f"?latitude={VIS_LAT}&longitude={VIS_LON}"
            "&current=sea_surface_temperature,wave_height,wave_direction,wave_period"
        )
        r = httpx.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        current = r.json()["current"]
        return {
            "sea_temp": round(current["sea_surface_temperature"], 1),
            "wave_height": round(current["wave_height"], 2),
            "wave_direction": _deg_to_compass(current["wave_direction"]),
            "wave_period": round(current["wave_period"], 1),
        }
    except Exception as e:
        print(f"[sidebar] sea conditions error: {e}")
        return {}


def fetch_sun_times() -> dict:
    """Returns sunrise, sunset, day_length as formatted strings or empty dict on error."""
    try:
        url = (
            "https://api.sunrise-sunset.org/json"
            f"?lat={VIS_LAT}&lng={VIS_LON}&formatted=0&tzid=Europe/Zagreb"
        )
        r = httpx.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data["status"] != "OK":
            return {}
        results = data["results"]

        def fmt(iso: str) -> str:
            return datetime.fromisoformat(iso).strftime("%H:%M")

        day_seconds = results["day_length"]
        hours, mins = divmod(day_seconds // 60, 60)

        return {
            "sunrise": fmt(results["sunrise"]),
            "sunset": fmt(results["sunset"]),
            "day_length": f"{hours}h {mins:02d}min",
        }
    except Exception as e:
        print(f"[sidebar] sun times error: {e}")
        return {}


def fetch_all() -> dict:
    return {
        "sea": fetch_sea_conditions(),
        "sun": fetch_sun_times(),
        "fetched_at": datetime.now(UTC),
    }
