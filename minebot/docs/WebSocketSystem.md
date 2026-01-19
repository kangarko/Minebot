# WebSocket Configuration Guide

## Overview

The WebSocket system in MineBot allows external applications to communicate with your bot in real-time. This feature enables:

- 🔄 **Real-time data exchange** between your bot and external tools
- 🧩 **Integration** with custom dashboards or control panels
- 🤖 **Automated workflows** through programmatic interaction

## Configuration Structure

The WebSocket server settings are defined in the `settings.json` file under the `server.websocket` section:

```json
"server": {
  "websocket": {
    "host": "localhost",
    "port": 8080,
    "auth": {
      "allowed_ip": "127.0.0.1",
      "password": "MineAcademy"
    }
  }
}
```

## Configuration Options

| Option       | Description                       | Default       | Notes                            |
| ------------ | --------------------------------- | ------------- | -------------------------------- |
| `host`       | Address where server listens      | `localhost`   | Use `0.0.0.0` for all interfaces |
| `port`       | Port number for connections       | `8080`        | Choose an available port         |
| `allowed_ip` | IP addresses permitted to connect | `127.0.0.1`   | Comma-separated for multiple IPs |
| `password`   | Authentication password           | `MineAcademy` | Change this in production!       |

## Security Considerations

### ⚠️ Important Security Measures

1. **IP Restrictions**: By default, connections are limited to `localhost`
2. **Authentication**: Password verification is required for all connections
3. **Default Values**: Change the default password before deploying in production
4. **Access Control**: Limit connections to trusted IPs only

## Advanced Configuration

### 🛡️ Recommended Production Settings

| Aspect       | Basic Setup      | Enhanced Security                        |
| ------------ | ---------------- | ---------------------------------------- |
| Port         | Default (8080)   | Custom port (e.g., 8443)                 |
| IP Filtering | localhost only   | Specific trusted IP address              |
| Password     | Default password | Strong, unique password (16+ characters) |

### 📝 Example Secure Configuration

```json
"server": {
  "websocket": {
    "host": "localhost",
    "port": 8443,
    "auth": {
      "allowed_ip": "123.123.123.123",
      "password": "y8F$p2Z!kL9@vB3#xD7&"
    }
  }
}
```

## Important Notes

- ⚠️ **Validation Rules**:

  - `host` must be a valid hostname or IP address
  - `port` must be a number between 1-65535
  - `password` should be at least 8 characters for security

- 📌 **Tips**:
  - Restart your bot after changing WebSocket configuration
