# VictoriaMetrics Pusher for Home Assistant

Collects host machine metrics (CPU, memory, disk, network) every 60 seconds and pushes them to VictoriaMetrics.

## Metrics pushed

| Metric | Description |
|--------|-------------|
| `ha_cpu_usage_percent` | CPU usage % |
| `ha_load_average_1m/5m/15m` | System load averages |
| `ha_memory_total_bytes` | Total RAM |
| `ha_memory_used_bytes` | Used RAM |
| `ha_memory_available_bytes` | Available RAM |
| `ha_memory_used_percent` | RAM usage % |
| `ha_disk_total_bytes` | Total disk (/) |
| `ha_disk_used_bytes` | Used disk (/) |
| `ha_disk_free_bytes` | Free disk (/) |
| `ha_disk_used_percent` | Disk usage % |
| `ha_network_bytes_sent_total` | Cumulative bytes sent |
| `ha_network_bytes_recv_total` | Cumulative bytes received |

All metrics include a `host` label.

## Installation via HACS

1. In HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/antonzaytsev/ha-vm-pusher` — category: **Integration**
3. Install **VictoriaMetrics Pusher**
4. Restart Home Assistant

## Manual installation

Copy `custom_components/vm_pusher/` into your HA `config/custom_components/` directory and restart.

## Configuration

Add to `configuration.yaml`:

```yaml
vm_pusher:
  url: http://192.168.0.30:8428/api/v1/import/prometheus
  interval: 60       # seconds, optional (default: 60)
  host: homeassistant  # label value, optional (default: hostname)
```

Restart Home Assistant. Check logs for `vm_pusher` to confirm metrics are being pushed.
