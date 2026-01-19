# 🔄 Minecraft Synchronization Guide

This document explains the Minecraft-Discord synchronization system for moderation actions in our bot. This powerful feature allows moderation actions to be automatically mirrored between your Discord server and Minecraft server(s).

## 🌐 What is Synchronization?

Synchronization allows moderation actions (kicks, bans, timeouts, etc.) to be automatically applied across platforms:

- When a moderator bans someone on Discord, they can also be banned on your Minecraft server
- When someone is punished on your Minecraft server, the same action can be applied on Discord

## 📋 Synchronization Configuration Structure

Synchronization is configured within each command's settings in the settings.json file:

```json
"ban": {
  "permissions": ["BAN_MEMBERS"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  },
  "log": 1377691201360232479,
  "synchronization": {
    "minecraft_to_discord": true,
    "discord_to_minecraft": true
  }
}
```

## 🧩 Configuration Options

The synchronization section has two key options:

| Property               | Purpose                               | Values            | Default |
| ---------------------- | ------------------------------------- | ----------------- | ------- |
| `minecraft_to_discord` | Send Minecraft punishments to Discord | `true` or `false` | `false` |
| `discord_to_minecraft` | Send Discord punishments to Minecraft | `true` or `false` | `false` |

- Setting both to `true` creates full two-way synchronization
- Setting only one to `true` creates one-way synchronization
- Setting both to `false` or omitting the section disables synchronization

## 🛠️ Supported Commands

The following moderation commands support synchronization:

| Command     | Discord Action          | Minecraft Equivalent |
| ----------- | ----------------------- | -------------------- |
| `kick`      | Remove user from server | `/kick` command      |
| `ban`       | Permanently ban user    | `/ban` command       |
| `unban`     | Remove existing ban     | `/pardon` command    |
| `timeout`   | Mute user temporarily   | `/mute` command      |
| `untimeout` | Remove timeout          | `/unmute` command    |

## ⚙️ How It Works

### 🔄 Two-Way Synchronization Flow

1. **Discord to Minecraft:**

   - When a Discord moderator uses a moderation command or the Discord system detects a moderation action (from audit logs)
   - If the user has a linked Minecraft account and `discord_to_minecraft` is `true` for the command
   - The equivalent Minecraft command is sent to all connected Minecraft servers
   - All parameters like duration and reason are transferred

2. **Minecraft to Discord:**
   - When a moderation action occurs on a Minecraft server
   - If the user has a linked Discord account and `minecraft_to_discord` is `true` for the command
   - The equivalent Discord action is applied to the user
   - The action is logged in the configured log channel

## 🌟 Example Configurations

### Full Two-Way Synchronization

```json
"ban": {
  "permissions": ["BAN_MEMBERS"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  },
  "log": 1377691201360232479,
  "synchronization": {
    "minecraft_to_discord": true,
    "discord_to_minecraft": true
  }
}
```

### One-Way (Discord to Minecraft Only)

```json
"timeout": {
  "permissions": ["MUTE_MEMBERS"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  },
  "log": 1377691201360232479,
  "synchronization": {
    "minecraft_to_discord": false,
    "discord_to_minecraft": true
  }
}
```

### No Synchronization

```json
"clear": {
  "permissions": ["MANAGE_MESSAGES"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  },
  "log": 1377691201360232479
}
```

## 🔐 Requirements for Synchronization

For synchronization to work properly:

1. **Account Linking:** Users must have their Discord and Minecraft accounts linked using the `/link_account` command
2. **WebSocket Connection:** The Minecraft server must be connected to the bot via the WebSocket connection
3. **Proper Configuration:** Synchronization must be enabled for the specific commands you want to synchronize
4. **Permissions:** The bot must have proper permissions on both Discord and Minecraft

## 💡 Benefits of Synchronization

| Benefit                   | Description                                                                      |
| ------------------------- | -------------------------------------------------------------------------------- |
| **Consistent Moderation** | Ensure rule-breakers can't escape punishment by switching platforms              |
| **Time Saving**           | Moderators only need to act once for both platforms                              |
| **Centralized Logging**   | All moderation actions get logged in one place on Discord                        |
| **Fair Warning**          | Players who are punished on one platform know they're also punished on the other |
| **Seamless Integration**  | Creates a unified community experience across both platforms                     |

## 🚨 Important Notes

- Punishments only synchronize for users who have linked their accounts
- Temporary punishments (like timeouts) will respect the duration across platforms
- If a punishment fails on one platform, it will still be applied on the other
- Custom punishments or non-standard moderation actions are not supported for synchronization
- All synchronized actions are logged in your configured log channel

## 📚 Configuration Cheat Sheet

```json
{
  "command-name": {
    "permissions": ["REQUIRED_PERMISSION"],
    "cooldown": {
      "algorithm": "fixed_window",
      "bucket": "user",
      "window_length": 60,
      "allowed_invocations": 1
    },
    "log": 1234567890123456789,
    "synchronization": {
      "minecraft_to_discord": true,
      "discord_to_minecraft": true
    }
  }
}
```

By properly configuring your synchronization settings, you can create a seamless moderation experience across both your Discord and Minecraft communities!
