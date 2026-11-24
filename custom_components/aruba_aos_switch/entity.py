from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import ArubaCoordinator
class ArubaEntity(CoordinatorEntity[ArubaCoordinator]):
    _attr_has_entity_name=True
    def __init__(self,coordinator: ArubaCoordinator,port_id: str)->None:
        super().__init__(coordinator); self.port_id=port_id
        self._attr_unique_id=f"{coordinator.data.system.serial}_{port_id}_{self.__class__.__name__.lower()}"
    @property
    def device_info(self)->DeviceInfo:
        s=self.coordinator.data.system
        return DeviceInfo(identifiers={(DOMAIN,s.serial)},name=s.name,manufacturer="HPE Aruba Networking",model=s.model,sw_version=s.firmware,configuration_url=f"https://{self.coordinator.client.host}")
