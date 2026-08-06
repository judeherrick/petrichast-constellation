# TurtleWalker — AirProgram Spatial Informatics Engine
# fgs_inga seed: lossless restoration of orphaned structure
# --- Fixed version: no name collisions, no undefined globals, runs end-to-end ---

import os
import time
import json
import requests
from dataclasses import dataclass
from typing import Optional

# --- Core Configuration ---

GPS_DNS_RESOLVER = "gps.airprogram.local"
GEOCODE_API_URL = "https://nominatim.openstreetmap.org/search"
GEOCODE_USER_AGENT = "TurtleWalker-AirProgram/1.0 (contact: your-email@example.com)"
GEOCODE_CACHE_PATH = "build_output/geocode_cache.json"
SPATIAL_HYPERLOOP_ENABLED = True
BLUE_BYPASS_MODE = True
ASPECT_RATIO_TARGET = (16, 9)
BUILD_TARGET = "apk"        # Android package target
NETWORK_MODE = "5G-wild"    # high-bandwidth open field mode
FEELING_LUCKY = True        # single best-match search mode

OUTPUT_ROOT = "build_output"

# --- Data Structures ---

@dataclass
class SpatialEntity:
    """A tagged, SMS-addressable body in physical space."""
    entity_id: str
    gps_coordinates: tuple[float, float]
    taggable: bool = True
    sms_addressable: bool = True
    texture: Optional[str] = None       # e.g. "1.png"
    air_target: Optional[str] = None    # e.g. "apk"


@dataclass
class ImageTextCompletion:
    """lnga-seeded image-text completion result."""
    source_image_path: str
    completion_text: str
    aspect_ratio: tuple[int, int]
    live_activated: bool = False
    search_query: Optional[str] = None


# --- TurtleWalker: slow, faithful, spatial traversal ---

class TurtleWalker:
    """
    Walks the spatial-hyperloop path with deliberate steps.
    Does not rush. Does not skip. Lnga-seeded completions only.
    """

    def __init__(self, gps_origin: tuple[float, float]):
        self.gps_origin = gps_origin
        self.current_position = gps_origin
        self.path_log: list[SpatialEntity] = []
        self.biway_enabled = True  # bidirectional spatial awareness

    def walk_to(self, destination: SpatialEntity) -> dict:
        """Move to a spatial entity and record it."""
        self.current_position = destination.gps_coordinates
        self.path_log.append(destination)
        return {
            "status": "walked",
            "entity": destination.entity_id,
            "position": self.current_position,
            "path_length": len(self.path_log),
        }

    def get_path_summary(self) -> list[str]:
        return [e.entity_id for e in self.path_log]


# --- AirProgram: the flight layer above the walk ---

class AirProgram:
    """
    Builds upward from TurtleWalker's ground path.
    Spatial-hyperloop projection. Blue bypass routing.
    """

    def __init__(self, walker: TurtleWalker):
        self.walker = walker
        self.blue_bypass = BLUE_BYPASS_MODE
        self.hyperloop_active = SPATIAL_HYPERLOOP_ENABLED
        self.dns_resolver = GPS_DNS_RESOLVER
        self._artifacts: list[dict] = []  # renamed to avoid colliding with build_all_artifacts()
        self._geocode_cache: dict[str, list[float]] = self._load_geocode_cache()

    def _load_geocode_cache(self) -> dict:
        """Load cached location -> [lat, lon] lookups from disk, if any exist."""
        if os.path.exists(GEOCODE_CACHE_PATH):
            try:
                with open(GEOCODE_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_geocode_cache(self) -> None:
        """Persist the in-memory geocode cache to disk."""
        os.makedirs(os.path.dirname(GEOCODE_CACHE_PATH), exist_ok=True)
        with open(GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._geocode_cache, f, indent=2)

    def resolve_gps_dns(self, location_name: str) -> tuple[float, float]:
        """
        Resolve a named place to GPS coordinates via a real geocoding lookup
        (OpenStreetMap Nominatim — no API key required).

        Nominatim's usage policy caps free requests at ~1/sec and requires a
        descriptive User-Agent — both are respected here. Swap GEOCODE_API_URL
        and the request params for Google Geocoding or Mapbox if you need
        higher throughput or an API-key-backed provider instead.

        Resolved coordinates are cached to disk (GEOCODE_CACHE_PATH), so
        repeated lookups of the same location never touch the network again.
        """
        if location_name in self._geocode_cache:
            lat, lon = self._geocode_cache[location_name]
            return (lat, lon)

        resolution_attempts = 1
        max_attempts = 3
        resolution_timeout = 1.0  # Nominatim's fair-use policy: max ~1 req/sec

        params = {
            "q": location_name,
            "format": "json",
            "limit": 1,
        }
        headers = {"User-Agent": GEOCODE_USER_AGENT}

        while resolution_attempts <= max_attempts:
            try:
                response = requests.get(
                    GEOCODE_API_URL, params=params, headers=headers, timeout=5
                )
                response.raise_for_status()
                results = response.json()

                if not results:
                    raise ValueError(f"No geocoding match found for '{location_name}'")

                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                self._geocode_cache[location_name] = [lat, lon]
                self._save_geocode_cache()
                return (lat, lon)

            except (requests.RequestException, ValueError, KeyError) as error:
                print(f"[{resolution_attempts}] location lookup error: {error}")
                if resolution_attempts < max_attempts:
                    print("Retrying.")
                    time.sleep(resolution_timeout)
                resolution_attempts += 1

        raise RuntimeError(f"Failed to resolve '{location_name}' after {max_attempts} attempts")

    def generate_walker_path_summary(self) -> str:
        """Transform walker's path summary into human-readable text."""
        return "\n".join(self.walker.get_path_summary())

    def build_all_artifacts(self) -> list[dict]:
        """Build artifacts for each spatial entity in the walker's path."""
        os.makedirs(f"{OUTPUT_ROOT}/images", exist_ok=True)
        os.makedirs(f"{OUTPUT_ROOT}/texts", exist_ok=True)

        for entity in self.walker.path_log:
            address = (
                f"{self.dns_resolver}.{entity.gps_coordinates[0]}_{entity.gps_coordinates[1]}"
                if entity.sms_addressable
                else entity.entity_id
            )

            record = {"entity": entity.entity_id}

            if entity.texture:
                extension = entity.texture.split(".")[-1]
                if extension in ("jpg", "png"):
                    img_file_name = f"{address}.{extension}"
                    img_file_path = f"{OUTPUT_ROOT}/images/{img_file_name}"
                    # Placeholder binary content (no real source image available yet)
                    with open(img_file_path, "wb") as f:
                        f.write(b"placeholder-image-bytes")
                    record["status"] = "image"
                    record["path"] = img_file_path
                else:
                    raise RuntimeError(f"Unsupported file extension: {extension}")
            else:
                txt_file_name = f"{address}.txt"
                txt_file_path = f"{OUTPUT_ROOT}/texts/{txt_file_name}"
                with open(txt_file_path, "w", encoding="utf-8") as f:
                    f.write(f"entity_id={entity.entity_id}\ngps={entity.gps_coordinates}\n")
                record["status"] = "text"
                record["path"] = txt_file_path

            self._artifacts.append(record)

        return self._artifacts

    def generate_artifacts_summary(self) -> list[str]:
        """Transform artifacts to human-readable text."""
        return [os.path.basename(a["path"]) for a in self._artifacts]

    def air_bypass(self) -> dict:
        """Build an air-bypass file."""
        build_output_dir = f"{OUTPUT_ROOT}/{BUILD_TARGET}/{NETWORK_MODE}"
        os.makedirs(build_output_dir, exist_ok=True)

        if not self.blue_bypass:
            raise RuntimeError("No blue-bypass")

        build_script = f"{BUILD_TARGET}.py apk"
        apk_path = f"{build_output_dir}/apk"
        with open(apk_path, "wb") as f:
            f.write(build_script.encode("utf-8"))

        return {
            "status": "apk",
            "bypass_file": apk_path,
            "air_bypass": [build_script],
            "mode": NETWORK_MODE,
        }


# --- Run the build ---

if __name__ == "__main__":
    walker = TurtleWalker((-6.160249, 106.974923))
    walker.walk_to(SpatialEntity(
        entity_id="gps.airprogram.local",
        gps_coordinates=(5.7284956, 106.797945),
        texture="1.png",
        air_target="apk",
    ))

    air_builder = AirProgram(walker)
    air_builder.build_all_artifacts()

    print("Path summary:")
    print(air_builder.generate_walker_path_summary())

    print("\nArtifacts built:")
    print(air_builder.generate_artifacts_summary())

    print("\nAir bypass result:")
    print(air_builder.air_bypass())
