# 🤖 MineBot

<p align="center">
  <strong>A modern, all-in-one Discord bot with Minecraft integration and powerful moderation tools.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/hikari-2.5.0-blueviolet?style=flat-square" alt="Hikari">
  <img src="https://img.shields.io/badge/version-1.1.1-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
</p>

---

## ✨ Features

### 🔗 Minecraft Integration

- **Account Linking** - Connect Discord accounts with Minecraft usernames
- **Cross-Platform Rewards** - Give in-game items through Discord events
- **Two-Way Moderation Sync** - Synchronize bans, kicks, and timeouts between Discord and Minecraft servers
- **Real-Time Communication** - WebSocket server for instant Minecraft server communication

### 🛡️ Moderation Tools

- **Ban/Unban** - Permanently ban or unban users
- **Kick** - Remove users from the server
- **Timeout/Untimeout** - Temporarily mute users
- **Lock/Unlock** - Lock channels to prevent messages
- **Slowmode** - Set channel slowmode
- **Clear** - Bulk delete messages
- **Punishment Logging** - Complete audit trail of all moderation actions

### 🎫 Ticket System

- **Multiple Categories** - Configure different ticket types (support, reports, etc.)
- **Thread or Channel Mode** - Create tickets as threads or dedicated channels
- **Transcript Generation** - Export conversations as HTML or plain text
- **GitHub Integration** - Automatically upload transcripts to a repository
- **Staff Roles** - Assign specific roles to handle different ticket categories

### 💡 Suggestion System

- **User Submissions** - Members can submit ideas via slash commands
- **Staff Review** - Approve or reject suggestions with feedback
- **Reward Integration** - Automatically reward users for approved suggestions

### 🎁 Boost Rewards

- **Automatic Detection** - Detect new server boosters instantly
- **Role Rewards** - Automatically assign special roles
- **Minecraft Rewards** - Give in-game items to boosters
- **Server-Specific Rewards** - Configure different rewards per Minecraft server

### 📚 Wiki System

- **Markdown Support** - Create help articles using Markdown
- **Multi-Language** - Localized wiki pages based on user locale

### 🌐 Localization

- **Full Translation Support** - Translate all messages, commands, and UI elements
- **Multiple Languages** - Built-in support for English and Turkish
- **Discord Locale Integration** - Automatically detect user's language preference

---

## 📋 Requirements

- Python 3.10+
- One of: SQLite, MySQL, or PostgreSQL
- Discord Bot Token
- (Optional) Minecraft server with WebSocket plugin

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/EgehanKilicarslan/minebot.git
cd minebot
```

### 2. Create Virtual Environment

```bash
# Using conda (recommended)
conda create -n hikari python=3.10
conda activate hikari

# Or using venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. Configure the Bot

Edit `configuration/settings.json`:

```json
{
  "secret": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "default_guild": 123456789012345678
  },
  "database": {
    "url": "sqlite+aiosqlite:///data/bot.db"
  }
}
```

### 5. Run the Bot

```bash
python -OO src/__main__.py
```

---

## 📁 Project Structure

```
minebot/
├── configuration/           # Bot configuration files
│   ├── settings.json        # Main settings
│   ├── debug.json           # Debug configuration
│   └── localization/        # Language files
│       ├── en-US.json
│       └── tr.json
├── docs/                    # Documentation
├── src/                     # Source code
│   ├── components/          # UI components (menus, modals)
│   ├── core/                # Core bot functionality
│   ├── database/            # Database models and services
│   ├── events/              # Event handlers
│   ├── extensions/          # Slash commands
│   │   ├── minecraft/       # Minecraft-related commands
│   │   ├── moderation/      # Moderation commands
│   │   └── user/            # User commands
│   ├── helper/              # Utility helpers
│   ├── websocket/           # WebSocket server
│   └── ...
└── pyproject.toml           # Project metadata
```

---

## ⚙️ Configuration

### Database Setup

MineBot supports three database backends:

| Database   | URL Format                                              |
| ---------- | ------------------------------------------------------- |
| SQLite     | `sqlite+aiosqlite:///data/bot.db`                       |
| MySQL      | `mysql+aiomysql://user:pass@localhost:3306/minebot`     |
| PostgreSQL | `postgresql+asyncpg://user:pass@localhost:5432/minebot` |

### WebSocket Server

Configure the WebSocket server for Minecraft integration:

```json
"server": {
  "websocket": {
    "host": "localhost",
    "port": 8080,
    "auth": {
      "allowed_ip": "127.0.0.1",
      "password": "your_secure_password"
    }
  }
}
```

### Moderation Synchronization

Enable two-way moderation sync between Discord and Minecraft:

```json
"ban": {
  "synchronization": {
    "minecraft_to_discord": true,
    "discord_to_minecraft": true
  }
}
```

---

## 📖 Documentation

Detailed documentation is available in the [docs/](docs/) directory:

- [Boost Reward System](docs/BoostRewardSystem.md) - Configure booster rewards
- [Bot Activity System](docs/BotActivitySystem.md) - Set bot status and activity
- [Command System](docs/CommandSystem.md) - Command configuration guide
- [Database System](docs/DatabaseSystem.md) - Database setup and connection
- [Localization Guide](docs/LocalizationGuide.md) - Translation system
- [Message System](docs/MessageSystem.md) - Custom message formatting
- [Minecraft Synchronization](docs/MinecraftSynchronization.md) - Cross-platform sync
- [Reward System](docs/RewardSystem.md) - Reward configuration
- [Suggestion System](docs/SuggestionSystem.md) - Suggestion feature setup
- [Ticket System](docs/TicketSystem.md) - Support ticket configuration
- [WebSocket System](docs/WebSocketSystem.md) - Real-time communication
- [Wiki System](docs/WikiSystem.md) - Wiki article system

---

## 🛠️ Tech Stack

- **[Hikari](https://github.com/hikari-py/hikari)** - Modern Discord API wrapper
- **[Lightbulb](https://github.com/tandemdude/hikari-lightbulb)** - Command framework for Hikari
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Database ORM with async support
- **[Pydantic](https://pydantic.dev/)** - Data validation
- **[WebSockets](https://websockets.readthedocs.io/)** - Real-time communication
- **[uvloop](https://github.com/MagicStack/uvloop)** - Fast event loop (Linux/macOS)

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for the  <a href="https://mineacademy.org">MineAcademy</a> 
</p>
