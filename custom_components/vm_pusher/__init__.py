"""VictoriaMetrics Pusher — collects host metrics and pushes to VictoriaMetrics."""
from __future__ import annotations

import logging
import socket
from datetime import timedelta

import aiohttp
import psutil
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

DOMAIN = "vm_pusher"
LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("url"): cv.string,
                vol.Optional("interval", default=60): cv.positive_int,
                vol.Optional("host", default=socket.gethostname()): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config[DOMAIN]
    url = conf["url"]
    interval = conf["interval"]
    host = conf["host"]

    LOGGER.info("vm_pusher starting — url=%s host=%s interval=%ds", url, host, interval)

    async def push(_now=None) -> None:
        try:
            lines = await hass.async_add_executor_job(_collect, host)
            await _push(url, lines)
            LOGGER.info("vm_pusher: pushed %d metrics to %s", len(lines), url)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("vm_pusher: push failed — %s: %s", type(exc).__name__, exc)

    await push()
    async_track_time_interval(hass, push, timedelta(seconds=interval))
    return True


# ---------------------------------------------------------------------------
# Collection — runs in executor thread (psutil is blocking)
# ---------------------------------------------------------------------------

def _collect(host: str) -> list[str]:
    lbl = f'host="{host}"'
    lines: list[str] = []

    # CPU
    cpu = psutil.cpu_percent(interval=1)
    lines.append(f"ha_cpu_usage_percent{{{lbl}}} {cpu}")

    load1, load5, load15 = psutil.getloadavg()
    lines.append(f"ha_load_average_1m{{{lbl}}} {load1}")
    lines.append(f"ha_load_average_5m{{{lbl}}} {load5}")
    lines.append(f"ha_load_average_15m{{{lbl}}} {load15}")

    # Memory
    mem = psutil.virtual_memory()
    lines.append(f"ha_memory_total_bytes{{{lbl}}} {mem.total}")
    lines.append(f"ha_memory_used_bytes{{{lbl}}} {mem.used}")
    lines.append(f"ha_memory_available_bytes{{{lbl}}} {mem.available}")
    lines.append(f"ha_memory_used_percent{{{lbl}}} {mem.percent}")

    # Disk
    disk = psutil.disk_usage("/")
    lines.append(f"ha_disk_total_bytes{{{lbl}}} {disk.total}")
    lines.append(f"ha_disk_used_bytes{{{lbl}}} {disk.used}")
    lines.append(f"ha_disk_free_bytes{{{lbl}}} {disk.free}")
    lines.append(f"ha_disk_used_percent{{{lbl}}} {disk.percent}")

    # Network (cumulative counters)
    net = psutil.net_io_counters()
    lines.append(f"ha_network_bytes_sent_total{{{lbl}}} {net.bytes_sent}")
    lines.append(f"ha_network_bytes_recv_total{{{lbl}}} {net.bytes_recv}")

    return lines


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------

async def _push(url: str, lines: list[str]) -> None:
    body = "\n".join(lines)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data=body,
            headers={"Content-Type": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 204:
                LOGGER.warning("VM returned HTTP %d", resp.status)
