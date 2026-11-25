from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True, slots=True)
class ArubaSystem:
    name: str
    model: str
    serial: str
    firmware: str
    image_datetime: str = ""
    boot_image: str = ""
    boot_rom_version: str = ""
@dataclass(frozen=True, slots=True)
class ArubaPort:
    port_id: str
    name: str
    enabled: bool | None
    link_up: bool | None
    config_mode: str | None = None
    trunk_mode: str | None = None
    lacp_status: str | None = None
    trunk_group: str | None = None
    raw: dict[str, Any] | None = None
@dataclass(frozen=True, slots=True)
class ArubaData:
    system: ArubaSystem
    ports: dict[str, ArubaPort]
