from homeassistant.components.binary_sensor import BinarySensorDeviceClass,BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_EXCLUDED_PORTS
from .coordinator import ArubaCoordinator
from .entity import ArubaEntity
async def async_setup_entry(hass: HomeAssistant,entry: ConfigEntry,async_add_entities: AddEntitiesCallback)->None:
    c: ArubaCoordinator=entry.runtime_data
    excluded={x.strip() for x in entry.options.get(CONF_EXCLUDED_PORTS,"").split(",") if x.strip()}
    async_add_entities(ArubaLinkSensor(c,p) for p in c.data.ports if p not in excluded)
class ArubaLinkSensor(ArubaEntity,BinarySensorEntity):
    _attr_device_class=BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon="mdi:lan-connect"
    def __init__(self,coordinator,port_id):
        super().__init__(coordinator,port_id); self._attr_name=f"Port {port_id} link"
    @property
    def is_on(self): return self.coordinator.data.ports[self.port_id].link_up
    @property
    def available(self): return super().available and self.is_on is not None
    @property
    def extra_state_attributes(self):
        p=self.coordinator.data.ports[self.port_id]
        return {"port_name":p.name,"admin_enabled":p.enabled,"config_mode":p.config_mode,"trunk_mode":p.trunk_mode,"lacp_status":p.lacp_status,"trunk_group":p.trunk_group}
