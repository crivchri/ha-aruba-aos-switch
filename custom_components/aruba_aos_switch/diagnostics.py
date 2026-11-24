from homeassistant.components.diagnostics import async_redact_data
TO_REDACT={"password","cookie","sessionId"}
async def async_get_config_entry_diagnostics(hass,entry):
    c=entry.runtime_data
    ports={pid:{"name":p.name,"enabled":p.enabled,"link_up":p.link_up,"config_mode":p.config_mode,"trunk_mode":p.trunk_mode,"lacp_status":p.lacp_status,"trunk_group":p.trunk_group} for pid,p in c.data.ports.items()}
    return async_redact_data({"entry":dict(entry.data),"options":dict(entry.options),"system":c.data.system.__dict__ if hasattr(c.data.system,"__dict__") else {"name":c.data.system.name,"model":c.data.system.model,"serial":c.data.system.serial,"firmware":c.data.system.firmware},"ports":ports},TO_REDACT)
