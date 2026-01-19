# Discord Bot Message System Guide

## 📝 Introduction

Our Discord bot uses a structured JSON format to define all messages, ensuring consistency while providing flexibility in how messages appear to users. This guide explains how to create and customize messages for the bot.

## 💬 Message Types

The system supports two message types:

1. **Plain Messages**: Simple text messages
2. **Embed Messages**: Rich, formatted messages with multiple components

## 🔧 Basic Message Structure

All messages follow this schema:

```json
{
  "message_type": "plain|embed",
  "content": {
    // Content specific to the message type
  }
}
```

The `message_type` field determines which format to use and what content is required.

## ✏️ Plain Messages

Plain messages are straightforward text messages:

```json
{
  "message_type": "plain",
  "content": {
    "text": "This is a simple text message"
  }
}
```

| Requirement     | Description                       |
| --------------- | --------------------------------- |
| `text` field    | Required                          |
| Character limit | 1-2000 characters (Discord limit) |

## 🖼️ Embed Messages

Embed messages are rich, formatted messages with multiple customizable components:

```json
{
  "message_type": "embed",
  "content": {
    "title": "Welcome to our server!",
    "description": "We're glad to have you here.",
    "url": "https://your-website.com",
    "color": "#7289DA",
    "timestamp": "2025-04-13T12:00:00Z",
    "fields": [
      {
        "name": "Rules",
        "value": "Please check the rules channel",
        "inline": true
      },
      {
        "name": "Support",
        "value": "Ask in #help channel",
        "inline": true
      }
    ],
    "footer": {
      "text": "Powered by MineBot",
      "icon": "https://your-website.com/logo.png"
    },
    "image": "https://your-website.com/banner.png",
    "thumbnail": "https://your-website.com/thumbnail.png",
    "author": {
      "name": "Admin Team",
      "url": "https://your-website.com/team",
      "icon": "https://your-website.com/admin-icon.png"
    }
  }
}
```

### 📋 Embed Components

| Component     | Description             | Limits                   |
| ------------- | ----------------------- | ------------------------ |
| `title`       | Main heading            | Max 256 characters       |
| `description` | Body text               | Max 4096 characters      |
| `url`         | Clickable link on title | Valid URL required       |
| `color`       | Sidebar color           | Hex, RGB, or color name  |
| `timestamp`   | Timestamp display       | ISO format datetime      |
| `fields`      | Additional sections     | Up to 25 fields          |
| `footer`      | Bottom text & icon      | Text max 2048 characters |
| `image`       | Large image             | Valid image URL          |
| `thumbnail`   | Small image             | Valid image URL          |
| `author`      | Author information      | Name max 256 characters  |

### ⚠️ Requirements

- Either `title` or `description` must be provided
- All URLs must be valid HTTP/HTTPS URLs
- Field lengths must adhere to Discord's limits

### 🎨 Color Formats

For the `color` field, we support multiple formats:

- **Hex code**: `"#7289DA"` or `"7289DA"`
- **RGB format**: `"rgb(114, 137, 218)"`
- **Color names**: `"RED"`, `"BLUE"`, `"GREEN"`, `"BLACK"`, etc.

All color formats will be converted to the appropriate hex code when processed.

## 🔄 Dynamic Content with Variables

Messages can include variables that get replaced with actual values when sent:

```json
{
  "message_type": "plain",
  "content": {
    "text": "Hello {username}, welcome to {server_name}!"
  }
}
```

### 📚 Common Variables

| Variable        | Description                     |
| --------------- | ------------------------------- |
| `{user}`        | Mentions the user               |
| `{username}`    | User's name                     |
| `{server_name}` | Server name                     |
| `{reason}`      | Reason for actions (bans/kicks) |
| `{duration}`    | Time duration for temp actions  |

## 📁 Organization in Localization Files

Messages are organized in localization files by feature and scenario:

```json
{
  "ban": {
    "messages": {
      "user": {
        "success": {
          "message_type": "plain",
          "content": {
            "text": "User {user} has been banned successfully."
          }
        },
        "error": {
          "message_type": "embed",
          "content": {
            "title": "Error",
            "description": "Failed to ban {user}.",
            "color": "RED"
          }
        }
      }
    }
  }
}
```

This structure allows:

- Easy navigation by feature
- Multiple message variations for each scenario
- Consistent organization across language files

## ✅ Best Practices

1. **Keep messages concise** - Short, clear messages are easier for users to read
2. **Use embeds for complex information** - Plain messages for simple notifications, embeds for detailed info
3. **Be consistent with colors** - Use the same color scheme for similar message types
4. **Test variables** - Ensure all variables are properly defined and replaced
5. **Follow Discord limits** - Adhere to character limits to prevent message failures

## 🛡️ Validation

Our system validates all messages to ensure they meet Discord requirements before sending. This prevents runtime errors and ensures a smooth user experience.
