# Docker API Proxy - Restricted Access for Sandbox Executor Manager

This proxy provides secure, filtered access to the Docker API for the sandbox executor manager.

## Security Features

- **No privileged mode**: Runs without elevated privileges
- **Read-only socket access**: Docker socket is mounted read-only
- **API filtering**: Only allows specific Docker API operations
- **Network isolation**: Only exposes necessary ports
- **Process isolation**: Runs as non-privileged user

## Allowed Operations

The proxy permits only the following Docker API operations:

### Container Operations
- `POST /containers/create` - Create new containers
- `GET /containers/json` - List containers
- `GET /containers/{id}/json` - Get container details
- `POST /containers/{id}/exec` - Execute commands in containers
- `POST /containers/{id}/start` - Start containers
- `GET /containers/{id}/logs` - Get container logs
- `GET /containers/{id}/wait` - Wait for container completion
- `GET /containers/{id}/archive` - Get container files
- `DELETE /containers/{id}` - Remove containers

### Image Operations
- `GET /images/json` - List images
- `POST /images/create` - Pull images

### System Operations
- `GET /info` - Get Docker system info
- `GET /version` - Get Docker version
- `GET /_ping` - Health check

## Blocked Operations

The following operations are explicitly blocked:

- Volume management (create, remove, inspect volumes)
- Network management (create, remove, inspect networks)
- Host path mounts (security risk)
- Privileged container creation
- Docker socket mounting into containers
- Service/Stack management
- Swarm operations
- Plugin management
- Secret/Config management

## Architecture

```
┌─────────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
│  executor_manager   │ ──TCP──▶│   docker_api_proxy  │ ──UNIX──▶│   Docker Daemon     │
│                     │ :2376  │  (filtered access)  │ /var/run │                     │
│  - no socket mount  │        │                     │ docker.sock│                     │
│  - no privileges    │        │  Allowed:           │           │                     │
│  - cap_drop: ALL    │        │  • container CRUD   │           │                     │
│                     │        │  • exec, logs       │           │                     │
│                     │        │  • images (list)    │           │                     │
│                     │        │  • info, version    │           │                     │
└─────────────────────┘        └─────────────────────┘           └─────────────────────┘
```

## Usage

1. Build the proxy:
   ```bash
   docker build -t sandbox-docker-proxy ./docker_api_proxy
   ```

2. Start the proxy:
   ```bash
   docker run -d \
     --name sandbox-docker-proxy \
     -p 2376:2376 \
     -v /var/run/docker.sock:/var/run/docker.sock:ro \
     --restart=always \
     sandbox-docker-proxy
   ```

3. Configure executor manager to use proxy:
   ```bash
   export DOCKER_HOST=tcp://localhost:2376
   ```

## Testing

```bash
# Test allowed operations
curl -X POST http://localhost:2376/containers/create -H "Content-Type: application/json" -d '{"Image": "alpine"}'

# Test blocked operations (should return 403)
curl -X POST http://localhost:2376/volumes/create -H "Content-Type: application/json" -d '{"Name": "test"}'
```

## Security Best Practices

- **Monitor logs**: Regularly check proxy logs for suspicious activity
- **Update regularly**: Keep the proxy and Docker daemon updated
- **Network isolation**: Run in a trusted network segment
- **Audit access**: Monitor which containers are being created
- **Use with gVisor**: Combine with gVisor for syscall-level isolation

## Troubleshooting

- **Proxy not starting**: Check Docker socket permissions
- **API calls failing**: Verify allowed endpoints match Docker API version
- **Performance issues**: Monitor proxy resource usage
- **Connection timeouts**: Check Docker daemon status