from __future__ import annotations
import asyncio
import logging
import base64
import re
from typing import Any
from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from .exceptions import ArubaAuthError, ArubaConnectionError, ArubaProtocolError, ArubaRateLimitError
from .models import ArubaData, ArubaPort, ArubaSystem
_LOGGER=logging.getLogger(__name__)
class ArubaApiClient:
    """Async ArubaOS-S REST client with one shared HA session and serialized login."""
    def __init__(self, host: str, username: str, password: str, api_version: str, session: ClientSession, verify_ssl: bool=True) -> None:
        self.host=host.strip().rstrip('/'); self.username=username; self.password=password
        self.api_version=api_version.strip('/'); self.session=session; self.verify_ssl=verify_ssl
        self.base_url=f"https://{self.host}/rest"; self._login_lock=asyncio.Lock(); self._write_lock=asyncio.Lock()
        self._authenticated=False; self._system: ArubaSystem | None=None; self.timeout=ClientTimeout(total=12,connect=5,sock_read=8)
    async def _json(self,response: ClientResponse)->dict[str,Any]:
        try: data=await response.json(content_type=None)
        except (ValueError,ClientError) as err: raise ArubaProtocolError(f"Invalid JSON (HTTP {response.status})") from err
        if not isinstance(data,dict): raise ArubaProtocolError("JSON root is not an object")
        return data
    async def async_login(self, force: bool=False)->None:
        async with self._login_lock:
            if self._authenticated and not force: return
            try:
                async with self.session.post(f"{self.base_url}/v1/login-sessions",json={"userName":self.username,"password":self.password},ssl=self.verify_ssl,timeout=self.timeout) as response:
                    if response.status in (401,403): raise ArubaAuthError("Invalid username or password")
                    if response.status>=400: raise ArubaConnectionError(f"Login failed: HTTP {response.status}")
                    data=await self._json(response)
                    cookie=data.get("cookie")
                    if cookie and "=" in str(cookie):
                        name,value=str(cookie).split("=",1)
                        self.session.cookie_jar.update_cookies({name:value})
                    self._authenticated=True
            except ArubaAuthError: raise
            except (ClientError,asyncio.TimeoutError) as err: raise ArubaConnectionError(str(err)) from err
    async def _request(self,method: str,path: str,body: dict[str,Any]|None=None,retry_auth: bool=True)->dict[str,Any]:
        await self.async_login()
        try:
            async with self.session.request(method,f"{self.base_url}/{path.lstrip('/')}",json=body,ssl=self.verify_ssl,timeout=self.timeout) as response:
                if response.status in (401,403):
                    self._authenticated=False
                    if retry_auth:
                        await self.async_login(force=True)
                        return await self._request(method,path,body,False)
                    raise ArubaAuthError("REST session rejected")
                if response.status in (429,503):
                    delay=int(response.headers.get("Retry-After","5"))
                    raise ArubaRateLimitError(f"Switch busy: HTTP {response.status}",delay)
                if response.status>=400:
                    text=(await response.text())[:300]
                    raise ArubaProtocolError(f"HTTP {response.status}: {text}")
                if response.status==204: return {}
                return await self._json(response)
        except (ArubaAuthError,ArubaRateLimitError,ArubaProtocolError): raise
        except (ClientError,asyncio.TimeoutError) as err: raise ArubaConnectionError(str(err)) from err
    async def async_get_firmware_version(self) -> str:
        """Get firmware version using the AOS-S AnyCLI REST endpoint."""
        data = await self._request(
            "POST",
            f"{self.api_version}/cli",
            {"cmd": "show version"},
        )

        if data.get("status") != "CCS_SUCCESS":
            raise ArubaProtocolError(
                f"show version failed: {data.get('error_msg', 'Unknown error')}"
            )

        encoded = data.get("result_base64_encoded")
        if not encoded:
            raise ArubaProtocolError(
                "show version returned no CLI output"
            )

        try:
            output = base64.b64decode(encoded).decode(
                "utf-8", errors="replace"
            )
        except (ValueError, TypeError) as err:
            raise ArubaProtocolError(
                "Unable to decode show version output"
            ) from err

        match = re.search(
            r"(?m)^\s*((?:YA|YB)\.\d{2}\.\d{2}\.\d{4})\s*$",
            output,
        )

        if not match:
            raise ArubaProtocolError(
                f"Could not extract firmware version from show version: {output}"
            )

        return match.group(1)
    async def async_get_system(self, refresh: bool=False)->ArubaSystem:
        if self._system is not None and not refresh: return self._system
        data=await self._request("GET",f"{self.api_version}/system")
        firmware=await self.async_get_firmware_version()
        self._system=ArubaSystem(
            str(data.get("name") or self.host),
            str(
                data.get("product_name")
                or data.get("model")
                or "ArubaOS-Switch"
            ),
            str(
                data.get("serial_number")
                or data.get("serial")
                or self.host
            ),
            str(firmware))
        return self._system
    @staticmethod
    def _bool(value: Any)->bool|None:
        if isinstance(value,bool): return value
        if isinstance(value,int): return bool(value)
        if isinstance(value,str):
            value=value.lower().strip()
            if value in {"true","up","enabled","active","1"}: return True
            if value in {"false","down","disabled","inactive","0"}: return False
        return None
    async def async_get_data(self)->ArubaData:
        system, payload=await asyncio.gather(self.async_get_system(),self._request("GET",f"{self.api_version}/ports"))
        ports={}
        for item in payload.get("port_element",[]):
            pid=str(item.get("id","")).strip()
            if not pid: continue
            link=next((self._bool(item[k]) for k in ("is_port_up","is_link_up","link_up","oper_status","operational_status") if k in item),None)
            ports[pid]=ArubaPort(pid,str(item.get("name") or f"Port {pid}"),self._bool(item.get("is_port_enabled")),link,item.get("config_mode"),item.get("trunk_mode"),item.get("lacp_status"),item.get("trunk_group"),item)
        if not ports: raise ArubaProtocolError("No ports returned by the switch")
        return ArubaData(system,ports)
    async def async_set_port(self,port_id: str,enabled: bool)->None:
        async with self._write_lock:
            await self._request("PUT",f"{self.api_version}/ports/{port_id}",{"id":str(port_id),"is_port_enabled":bool(enabled)})
    async def async_close(self)->None:
        """Shared HA session is owned by Home Assistant; only clear local state."""
        self._authenticated=False; self._system=None
