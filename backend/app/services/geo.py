"""IP geolocation resolution.

Production deployments should swap this out for a real provider (MaxMind
GeoIP2 local database, or an HTTP service like ipapi.co / ipinfo.io). To keep
this project runnable offline with no external API keys, we ship a small
deterministic mock resolver: a handful of known demo IPs map to real cities
(used by the seed data / demo script to reliably trigger the impossible
travel detector), and any other IP hashes to a stable pseudo-random location
so the same IP always resolves to the same place within a single deployment.
"""
from __future__ import annotations

import hashlib
import ipaddress
from dataclasses import dataclass

_KNOWN_LOCATIONS: dict[str, "GeoLocation"] = {}

_DEMO_CITIES = [
    ("Houston", "United States", 29.7604, -95.3698),
    ("Tokyo", "Japan", 35.6762, 139.6503),
    ("London", "United Kingdom", 51.5074, -0.1278),
    ("Sydney", "Australia", -33.8688, 151.2093),
    ("Sao Paulo", "Brazil", -23.5505, -46.6333),
    ("Lagos", "Nigeria", 6.5244, 3.3792),
    ("New York", "United States", 40.7128, -74.0060),
    ("Frankfurt", "Germany", 50.1109, 8.6821),
    ("Singapore", "Singapore", 1.3521, 103.8198),
    ("Toronto", "Canada", 43.6532, -79.3832),
]


@dataclass
class GeoLocation:
    city: str
    country: str
    latitude: float
    longitude: float


def register_demo_ip(ip: str, city: str, country: str, lat: float, lon: float) -> None:
    _KNOWN_LOCATIONS[ip] = GeoLocation(city=city, country=country, latitude=lat, longitude=lon)


def resolve_ip(ip: str) -> GeoLocation:
    if ip in _KNOWN_LOCATIONS:
        return _KNOWN_LOCATIONS[ip]

    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback:
            city, country, lat, lon = _DEMO_CITIES[0]
            return GeoLocation(city=city, country=country, latitude=lat, longitude=lon)
    except ValueError:
        pass

    digest = hashlib.sha256(ip.encode("utf-8")).digest()
    index = digest[0] % len(_DEMO_CITIES)
    city, country, lat, lon = _DEMO_CITIES[index]
    # Add small deterministic jitter so not every IP in the same bucket is identical.
    jitter_lat = ((digest[1] / 255.0) - 0.5) * 2.0
    jitter_lon = ((digest[2] / 255.0) - 0.5) * 2.0
    return GeoLocation(city=city, country=country, latitude=lat + jitter_lat, longitude=lon + jitter_lon)
