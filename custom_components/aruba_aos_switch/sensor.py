from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArubaCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ArubaCoordinator = entry.runtime_data

    async_add_entities([
        ArubaFirmwareSensor(coordinator),
    ])


class ArubaFirmwareSensor(
    CoordinatorEntity[ArubaCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True
    _attr_name = "Firmware version"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: ArubaCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.data.system.serial}_firmware"
        )

    @property
    def native_value(self) -> str:
        return self.coordinator.data.system.firmware

    @property
    def device_info(self) -> DeviceInfo:
        system = self.coordinator.data.system

        return DeviceInfo(
            identifiers={(DOMAIN, system.serial)},
            name=system.name,
            manufacturer="HPE Aruba Networking",
            model=system.model,
            sw_version=system.firmware,
            configuration_url=(
                f"https://{self.coordinator.client.host}"
            ),
        )