# 🔍 MineBot Suggestion System Guide

## Overview

The Suggestion System enables server members to submit ideas, feedback, and feature requests directly through Discord. Each suggestion can be reviewed, approved, or rejected by staff members. The system includes reward capabilities for approved suggestions and utilizes Discord's interactive components for a seamless user experience.

## ✨ Key Features

- **Easy Submission Process**: Users submit suggestions via a Discord slash command and modal form
- **Staff Review Flow**: Moderators can approve or reject suggestions with feedback
- **Reward Integration**: Optionally reward users for approved suggestions (Discord roles and Minecraft items)
- **Notification System**: Automatic notifications for submission and review status
- **Multi-language Support**: Fully translatable interface for international communities
- **Database Storage**: Suggestions are stored and tracked in the database
- **Logging**: Comprehensive audit trail of all suggestion activity

## 🔄 How It Works

```mermaid
graph TD
    A[User Submits Suggestion] --> B[Bot Posts in Pending Channel]
    B --> C{Staff Review}
    C -->|Approve| D[Staff Provides Feedback]
    C -->|Reject| E[Staff Provides Feedback]
    D --> F[Suggestion Posted in Result Channel]
    E --> G[Rejection Posted in Result Channel]
    F --> H{Rewards Enabled?}
    H -->|Yes| I[Give Rewards to User]
    H -->|No| J[End Process]
    I --> J
```

1. A user runs the `/suggest` command (or localized equivalent)
2. The bot presents a modal form for entering suggestion details
3. Upon submission, the suggestion appears in a designated pending channel with approve/reject buttons
4. Staff members can review the suggestion by clicking one of these buttons
5. Staff provides feedback via a response modal
6. The suggestion with staff response is posted in a result channel
7. The user receives notifications about their suggestion's status
8. If approved and rewards are enabled, the user receives configured rewards

## ⚙️ Configuration Guide

The suggestion system is configured in your settings.json file under the `commands.suggest` section:

```json
"suggest": {
  "permissions": ["NONE"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  },
  "pending_channel": 1378844065197723778,
  "result_channel": 1370801109395837110,
  "reward": {
    "mode": "BOTH",
    "role": [1371228108598018089],
    "item": {
      "test1": ["give {minecraft_username} diamond 1"],
      "default": ["give {minecraft_username} apple 1"]
    }
  }
}
```

### Settings Explained:

| Setting           | Description                                 | Options                                   |
| ----------------- | ------------------------------------------- | ----------------------------------------- |
| `permissions`     | Required Discord permissions to use command | Array of permission names, or `"NONE"`    |
| `cooldown`        | Anti-spam settings for the command          | Object with algorithm and timing settings |
| `pending_channel` | Channel where initial suggestions appear    | Valid channel ID number                   |
| `result_channel`  | Channel where reviewed suggestions appear   | Valid channel ID number                   |
| `reward`          | Optional rewards for approved suggestions   | Object with role and item settings        |

## 🧩 Advanced Features

### Reward Integration

The suggestion system can automatically reward users whose suggestions are approved:

```json
"reward": {
  "mode": "BOTH",
  "role": [1371228108598018089],
  "item": {
    "test1": ["give {minecraft_username} diamond 1"],
    "default": ["give {minecraft_username} apple 1"]
  }
}
```

- `mode`: Set to `"ROLE"` for Discord roles only, `"ITEM"` for Minecraft items only, or `"BOTH"` for both
- `role`: Array of Discord role IDs to assign
- `item`: Minecraft commands to run per server, with variable replacement

### Variable Substitution

Your suggestion messages and rewards can include dynamic placeholders:

- `{discord_username}` - Username of the suggestion author
- `{discord_user_id}` - ID of the suggestion author
- `{discord_user_mention}` - Mentions the suggestion author
- `{discord_staff_username}` - Username of reviewing staff member
- `{discord_staff_user_id}` - ID of reviewing staff member
- `{discord_staff_user_mention}` - Mentions the staff member reviewing
- `{suggestion}` - The submitted suggestion text
- `{reason}` - The staff response/reason text
- `{minecraft_username}` - For users with linked accounts
- `{minecraft_uuid}` - For users with linked accounts

## 📋 Localization

The suggestion system supports full localization through the language files:

```json
"suggest": {
  "command": {
    "label": "suggest",
    "description": "Suggest a feature."
  },
  "messages": {
    "user": {
      "success": {
        "text": "Your suggestion has been submitted successfully."
      },
      "failure": {
        "text": "Failed to submit your suggestion."
      }
    },
    "pending": {
      "success": {
        "text": "New suggestion from {discord_user_mention}:\n\n{suggestion}"
      },
      "failure": {
        "text": "Failed to process suggestion from {discord_user_mention}."
      }
    },
    "result": {
      "approve": {
        "text": "**Suggestion by {discord_username} was approved**\n\n**Suggestion:**\n{suggestion}\n\n**Response from {discord_staff_username}:**\n{reason}"
      },
      "reject": {
        "text": "**Suggestion by {discord_username} was rejected**\n\n**Suggestion:**\n{suggestion}\n\n**Response from {discord_staff_username}:**\n{reason}"
      }
    }
  },
  "menu": {
    "confirmation": {
      "approve": {
        "label": "Approve",
        "emoji": "✅",
        "style": "SUCCESS"
      },
      "reject": {
        "label": "Reject",
        "emoji": "❌",
        "style": "DANGER"
      }
    }
  },
  "modal": {
    "send": {
      "title": "Give a Suggestion",
      "fields": {
        "suggestion": {
          "style": "PARAGRAPH",
          "label": "Suggestion",
          "placeholder": "Enter your suggestion here."
        }
      }
    },
    "respond": {
      "title": "Respond to Suggestion",
      "fields": {
        "response": {
          "style": "PARAGRAPH",
          "label": "Response",
          "placeholder": "Enter your response here."
        }
      }
    }
  }
}
```

## 🔍 Troubleshooting

| Issue                          | Solution                                                       |
| ------------------------------ | -------------------------------------------------------------- |
| Command not showing up         | Verify the command is properly registered and enabled          |
| Users can't use the command    | Check `permissions` setting; ensure bot has proper permissions |
| Suggestions not appearing      | Confirm `pending_channel` ID is correct and bot can post there |
| Results not appearing          | Confirm `result_channel` ID is correct and bot can post there  |
| Rewards not working            | Make sure users have linked their Minecraft accounts           |
| Staff can't review suggestions | Ensure they have proper Discord permissions                    |
| Database errors                | Check database connection and schema for SuggestionSchema      |
