# ArubaOS-Switch REST for Home Assistant

Custom Home Assistant integration for HPE ArubaOS-Switch 16.x, tested conceptually for the Aruba 2530 J9772A (48 ports). It creates one administrative switch and one real-link binary sensor per REST port.

## Highlights
- UI config flow and options flow
- One bulk `/rest/v4/ports` poll for every port
- Shared asynchronous HTTP session and safe cookie jar for IP hosts
- Serialized login and write operations
- Automatic one-time reauthentication on HTTP 401/403
- Coordinator availability/backoff behavior
- Optimistic cache update after writes, immediately followed by authoritative refresh
- Diagnostics with credentials and session data redacted
- Configurable polling interval (10-300 seconds) and excluded ports
- Firmware version sensor and also displayed in Home Assistant device information

## Switch prerequisites
```text
configure terminal
rest-interface
web-management ssl
write memory
show rest-interface
```
Use a dedicated manager account. Never expose port 443 to the Internet.

## HACS installation
1. Publish this repository on GitHub after replacing `YOUR_GITHUB_USERNAME` in `manifest.json`.
2. HACS > Integrations > Custom repositories.
3. Add the repository URL with category **Integration**.
4. Install **ArubaOS-Switch REST** and restart Home Assistant.
5. Settings > Devices & services > Add integration > ArubaOS-Switch REST.

## Manual installation
Copy `custom_components/aruba_aos_switch` to `/config/custom_components/` and restart HA.

## Configuration
- Host: IP/FQDN without protocol
- REST version: `v4` recommended for ArubaOS-Switch 16.11
- Verify TLS: recommended with a certificate trusted by the HA host
- Polling: default 15 seconds; use 30-60 seconds for larger installations
- Excluded ports: e.g. `47,48` for uplinks

The integration retrieves the firmware version from the system information returned by the ArubaOS-Switch REST API.

## Safety
Exclude HA's own uplink, trunks, LACP members, firewall/router ports and any management path. Disabling these can isolate Home Assistant.

## Release
Create a GitHub release whose tag matches `manifest.json`, for example `v1.0.0`. Run the included GitHub Actions validation first.

## REST behavior
Login uses `POST /rest/v1/login-sessions`; data and writes use the configured schema, normally `/rest/v4/ports`. Port writes send a real JSON Boolean: `{"id":"17","is_port_enabled":false}`.

## License
MIT

Visual in this repository was generated with Microsoft Copilot.
