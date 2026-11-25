from __future__ import annotations
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST,CONF_PASSWORD,CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import ArubaApiClient
from .const import *
from .exceptions import ArubaAuthError,ArubaError

def schema(defaults=None):
    d=defaults or {}
    return vol.Schema({vol.Required(CONF_HOST,default=d.get(CONF_HOST,"")):str,vol.Required(CONF_USERNAME,default=d.get(CONF_USERNAME,"homeassistant")):str,vol.Required(CONF_PASSWORD):str,vol.Optional(CONF_API_VERSION,default=d.get(CONF_API_VERSION,DEFAULT_API_VERSION)):vol.In(["v1","v2","v3","v4"]),vol.Optional(CONF_VERIFY_SSL,default=d.get(CONF_VERIFY_SSL,DEFAULT_VERIFY_SSL)):bool})

class ArubaConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1
    
    async def async_step_user(self,user_input: dict[str,Any]|None=None)->FlowResult:
        errors={}
        if user_input:
            session = async_create_clientsession(self.hass)
            
            c = ArubaApiClient(
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_API_VERSION],
                session,
                user_input[CONF_VERIFY_SSL]
            )
            
            try:
                data = await c.async_get_data()
            
            except ArubaAuthError:
                errors["base"] = "invalid_auth"
            
            except ArubaError:
                errors["base"] = "cannot_connect"
            
            else:
                await self.async_set_unique_id(data.system.serial)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=data.system.name,
                    data=user_input
                )
            
            finally:
                await c.async_close()
                
        return self.async_show_form(step_id="user",data_schema=schema(user_input),errors=errors)
    
    @staticmethod
    def async_get_options_flow(config_entry): return ArubaOptionsFlow()

class ArubaOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self,user_input=None):
        if user_input is not None: return self.async_create_entry(title="",data=user_input)
        o=self.config_entry.options
        return self.async_show_form(step_id="init",data_schema=vol.Schema({vol.Optional(CONF_SCAN_INTERVAL,default=o.get(CONF_SCAN_INTERVAL,DEFAULT_SCAN_INTERVAL)):vol.All(vol.Coerce(int),vol.Range(min=MIN_SCAN_INTERVAL,max=MAX_SCAN_INTERVAL)),vol.Optional(CONF_EXCLUDED_PORTS,default=o.get(CONF_EXCLUDED_PORTS,"")):str}))
