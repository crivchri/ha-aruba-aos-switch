from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_EXCLUDED_PORTS
from .coordinator import ArubaCoordinator
from .entity import ArubaEntity
async def async_setup_entry(hass: HomeAssistant,entry: ConfigEntry,async_add_entities: AddEntitiesCallback)->None:
    c: ArubaCoordinator=entry.runtime_data
    excluded={x.strip() for x in entry.options.get(CONF_EXCLUDED_PORTS,"").split(",") if x.strip()}
    async_add_entities(ArubaPortSwitch(c,p) for p in c.data.ports if p not in excluded)
class ArubaPortSwitch(ArubaEntity,SwitchEntity):
    _attr_icon="mdi:ethernet"
    def __init__(self,coordinator,port_id):
        super().__init__(coordinator,port_id); self._attr_name=f"Port {port_id} administration"
    @property
    def is_on(self): return self.coordinator.data.ports[self.port_id].enabled
    @property
    def available(self): return super().available and self.is_on is not None
    async def async_turn_on(self,**kwargs): await self.coordinator.async_set_port(self.port_id,True)
    async def async_turn_off(self,**kwargs): await self.coordinator.async_set_port(self.port_id,False)
