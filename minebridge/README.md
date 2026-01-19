# 🌉 MineBridge

<p align="center">
  <strong>A WebSocket-based communication plugin for seamless cross-server messaging and command execution in Minecraft networks.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/java-8+-orange?style=flat-square&logo=openjdk&logoColor=white" alt="Java 8+">
  <img src="https://img.shields.io/badge/maven-3.x-C71A36?style=flat-square&logo=apachemaven&logoColor=white" alt="Maven">
  <img src="https://img.shields.io/badge/version-1.1.1-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platforms-Bukkit%20|%20BungeeCord%20|%20Velocity-blue?style=flat-square" alt="Platforms">
</p>

---

## ✨ Features

### 🔌 WebSocket Communication

- **Secure Connections** - SSL/TLS encrypted WebSocket connections
- **Auto-Reconnect** - Automatic reconnection handling on connection loss
- **Certificate Support** - Custom SSL certificate management
- **Password Authentication** - Secure password-protected connections

### 🌐 Cross-Server Messaging

- **Global Messages** - Broadcast messages to all players on the network
- **Server Messages** - Send messages to all players on a specific server
- **Player Messages** - Direct message specific players across servers
- **Rich Message Types** - Support for chat, action bar, title, and more

### ⚡ Command System

- **Remote Execution** - Execute commands on remote servers
- **Command Interception** - Intercept and process commands across servers
- **Alias Support** - Configure command aliases for moderation tools
- **Execution Logging** - Track command execution across the network

### 📦 Multi-Platform Support

- **Bukkit/Spigot/Paper** - Full support for Bukkit-based servers (1.8+)
- **BungeeCord** - Native BungeeCord proxy integration
- **Velocity** - Modern Velocity proxy support
- **Standalone & Proxied** - Works with or without a proxy

---

## 📋 Requirements

- Java 8 or higher
- Maven 3.x (for building)
- One of the following server platforms:
  - Bukkit/Spigot/Paper (1.8+)
  - BungeeCord
  - Velocity

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/EgehanKilicarslan/minebridge
cd minebridge
```

### 2. Build the Project

```bash
mvn clean install
```

This will generate the following JAR files:

- `minebridge-bukkit/target/MineBridge-Bukkit-1.1.1.jar`
- `minebridge-bungeecord/target/MineBridge-BungeeCord-1.1.1.jar`
- `minebridge-velocity/target/MineBridge-Velocity-1.1.1.jar`

### 3. Install the Plugin

1. Copy the appropriate JAR file to your server's `plugins` folder
2. Start the server to generate configuration files
3. Configure the `settings.yml` with your WebSocket server details
4. Place your SSL certificate in `plugins/MineBridge/certs/`

### 4. Configure WebSocket

Edit `plugins/MineBridge/settings.yml`:

```yaml
websocket:
  host: "your-websocket-server.com"
  port: 8080
  password: "your-secure-password"
```

---

## 📁 Project Structure

```
minebridge/
├── minebridge-core/           # Core WebSocket client and schemas
│   └── src/main/java/
│       └── websocket/         # WebSocket client implementation
│       └── schema/            # Message schemas
│       └── settings/          # Configuration management
├── minebridge-proxy-core/     # Shared proxy functionality
│   └── src/main/java/
│       └── actions/           # Action handlers for proxies
├── minebridge-bukkit/         # Bukkit/Spigot plugin
│   └── src/main/java/
│       └── actions/           # Bukkit-specific handlers
│       └── listener/          # Event listeners
├── minebridge-bungeecord/     # BungeeCord plugin
│   └── src/main/java/
│       └── listener/          # BungeeCord listeners
└── minebridge-velocity/       # Velocity plugin
    └── src/main/java/
        └── listener/          # Velocity listeners
```

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Bukkit Server  │     │ BungeeCord/     │     │  Bukkit Server  │
│  (Standalone)   │     │ Velocity Proxy  │     │   (Proxied)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │    WebSocket (WSS)    │    Plugin Messaging   │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   WebSocket Server      │
                    │   (External Service)    │
                    └─────────────────────────┘
```

### 🖥️ Server Modes

| Mode           | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| **Standalone** | Bukkit servers connect directly to the WebSocket server       |
| **Proxied**    | Proxy handles WebSocket, relays via plugin messaging channels |

---

## 📨 Message Schemas

MineBridge uses structured schemas for cross-server communication:

| Schema              | Description                                        |
| ------------------- | -------------------------------------------------- |
| `SendGlobalMessage` | Broadcast a message to all players on the network  |
| `SendServerMessage` | Send a message to all players on a specific server |
| `SendPlayerMessage` | Send a message to a specific player                |
| `DispatchCommand`   | Execute a command on a remote server               |
| `CommandExecuted`   | Notification when a command is executed            |
| `PlayerStatusCheck` | Check if a player is online                        |
| `PlayerServerCheck` | Check which server a player is on                  |

---

## ⚙️ Configuration

### Command Aliases

Configure aliases for commands that should be intercepted:

```yaml
aliases:
  kick:
    - "kick"
    - "ekick"
  ban:
    - "ban"
    - "eban"
  tempban:
    - "tempban"
    - "etempban"
  unban:
    - "unban"
    - "pardon"
```

### Command Syntax

Define command structures for parsing:

```yaml
syntax:
  kick: "{alias} <target> [reason]"
  ban: "{alias} <target> [reason]"
```

---

## 🛠️ Development

### Creating Custom Action Handlers

Use the `@WebSocketAction` annotation to create custom handlers:

```java
@WebSocketAction("custom-action")
public void handleCustomAction(JsonObject data) {
    // Handle the incoming action
    String message = data.get("message").getAsString();
    // Process the message...
}
```

### Registering Handlers

```java
webSocketClient.registerActionHandler(
    new PlayerActionHandler(),
    new MessageActionHandler(),
    new CommandActionHandler()
);
```

---

## 🧰 Tech Stack

- **[Foundation](https://github.com/kangarko/Foundation)** - MineAcademy plugin framework
- **[Java-WebSocket](https://github.com/TooTallNate/Java-WebSocket)** - WebSocket client library
- **[Gson](https://github.com/google/gson)** - JSON serialization/deserialization
- **[Lombok](https://projectlombok.org/)** - Boilerplate code reduction
- **[Adventure](https://github.com/KyoriPowered/adventure)** - Modern text component library

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

<p align="center">
  Made with ❤️ by for <a href="https://mineacademy.org">MineAcademy</a>
</p>
