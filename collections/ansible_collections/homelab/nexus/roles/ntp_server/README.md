# NTP Server Role

This role deploys a containerized NTP server using the 11notes/chrony container image.

## Requirements

- Docker and docker-compose installed on the target host
- Port 123/UDP available on the host

## Role Variables

```yaml
# NTP Server Configuration
ntp_timezone: "UTC"
ntp_container_name: "ntp-server"
ntp_container_image: "11notes/chrony:4.7"
ntp_config_path: "/opt/chrony"

# NTP pools to use
ntp_pools:
  - "ch.pool.ntp.org iburst maxsources 5"
  - "ntp.ubuntu.com iburst maxsources 5"

# Networks allowed to query NTP
ntp_allowed_networks:
  - "10.60.0.0/16"  # Management network
  - "10.50.0.0/16"  # Secure network
```

## Dependencies

None.

## Example Playbook

```yaml
- hosts: nexus
  become: yes
  roles:
    - homelab.nexus.ntp_server
```

## Security

- Container runs with read-only filesystem
- Runs as non-root user (UID 1000)
- Only allows NTP queries from specified internal networks
- Uses scratch-based distroless image (1.22MB)

## Testing

```bash
# Run molecule tests
./test.sh test nexus-ntp-server

# Test NTP server after deployment
ntpdate -q your-ntp-server
```

## License

MIT