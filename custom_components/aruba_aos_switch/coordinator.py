from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import ArubaApiClient
from .const import CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL,DOMAIN
from .exceptions import ArubaAuthError,ArubaError,ArubaRateLimitError
from .models import ArubaData
_LOGGER=logging.getLogger(__name__)
class ArubaCoordinator(DataUpdateCoordinator[ArubaData]):
    config_entry: ConfigEntry
    def __init__(self,hass: HomeAssistant,entry: ConfigEntry,client: ArubaApiClient)->None:
        self.client=client
        super().__init__(hass,_LOGGER,config_entry=entry,name=DOMAIN,update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL)),always_update=False)
    async def _async_update_data(self)->ArubaData:
        try: return await self.client.async_get_data()
        except ArubaAuthError as err: raise ConfigEntryAuthFailed from err
        except ArubaRateLimitError as err: raise UpdateFailed(f"Switch busy; retry suggested in {err.retry_after}s") from err
        except ArubaError as err: raise UpdateFailed(str(err)) from err
    async def async_set_port(self,port_id: str,enabled: bool)->None:
        await self.client.async_set_port(port_id,enabled)
        if self.data and port_id in self.data.ports:
            from dataclasses import replace
            ports=dict(self.data.ports); ports[port_id]=replace(ports[port_id],enabled=enabled)
            self.async_set_updated_data(replace(self.data,ports=ports))
        await self.async_request_refresh()
