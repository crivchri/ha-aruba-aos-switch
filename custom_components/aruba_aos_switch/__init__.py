from aiohttp import CookieJar
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST,CONF_PASSWORD,CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .api import ArubaApiClient
from .const import CONF_API_VERSION,CONF_VERIFY_SSL,DEFAULT_API_VERSION,DEFAULT_VERIFY_SSL,PLATFORMS
from .coordinator import ArubaCoordinator
async def async_setup_entry(hass: HomeAssistant,entry: ConfigEntry)->bool:
    session=async_create_clientsession(hass,cookie_jar=CookieJar(unsafe=True))
    client=ArubaApiClient(entry.data[CONF_HOST],entry.data[CONF_USERNAME],entry.data[CONF_PASSWORD],entry.data.get(CONF_API_VERSION,DEFAULT_API_VERSION),session,entry.data.get(CONF_VERIFY_SSL,DEFAULT_VERIFY_SSL))
    coordinator=ArubaCoordinator(hass,entry,client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data=coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS)
    return True
async def async_unload_entry(hass: HomeAssistant,entry: ConfigEntry)->bool:
    if ok:=await hass.config_entries.async_unload_platforms(entry,PLATFORMS): await entry.runtime_data.client.async_close()
    return ok
async def _async_reload(hass: HomeAssistant,entry: ConfigEntry)->None: await hass.config_entries.async_reload(entry.entry_id)
