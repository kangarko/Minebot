# 🎫 MineBot Ticket System Guide

## Overview

The Ticket System enables server members to create support tickets directly through Discord. Users can create different types of tickets (general support, reports, etc.) which are managed in dedicated channels or threads. Staff can respond to tickets and close them when resolved. The system includes transcript generation for record-keeping and supports various customization options.

## ✨ Key Features

- **Multiple Ticket Categories**: Configure different ticket types with specific staff roles
- **Flexible Creation Methods**: Create tickets as channels or threads
- **Interactive Creation**: Button or dropdown menu for intuitive ticket creation
- **Ticket Management**: Close tickets with confirmation dialog
- **Transcript Generation**: Save ticket conversations as HTML or plain text
- **Transcript Storage**: Upload to Discord channels or GitHub repository
- **Multi-language Support**: Fully translatable interface for international communities
- **Database Tracking**: Tickets are stored and tracked in the database
- **User Limits**: Configurable maximum number of tickets per user

## 🔄 How It Works

```mermaid
graph TD
    A[User Interacts with Ticket Panel] --> B{Selects Category}
    B --> C[Fills Ticket Modal Form]
    C --> D[Ticket Channel/Thread Created]
    D --> E[User & Staff Communicate]
    E --> F[Close Button Clicked]
    F --> G{Confirm Close?}
    G -->|No| E
    G -->|Yes| H[Generate Transcript]
    H --> I[Upload Transcript]
    I --> J[Delete Ticket Channel]
```

1. A user interacts with the ticket panel in a designated channel
2. User selects a ticket category using buttons or dropdown
3. User completes a modal form with necessary details
4. System creates a private channel or thread for the ticket
5. Staff and user communicate in the ticket
6. When resolved, staff closes the ticket using the close button
7. Staff confirms closing (two-step process)
8. System generates a transcript of the conversation
9. Transcript is uploaded to a log channel or GitHub repository
10. Ticket channel is deleted and database is updated

## ⚙️ Configuration Guide

The ticket system is configured in your settings.json file under the `systems.ticket` section:

```json
"ticket": {
  "categories": {
    "general": {
      "category_emoji": "📩",
      "category_name": "General Support",
      "category_description": "For general support and questions.",
      "channel_format": "{ticket_owner_discord_username}-general",
      "channel_id": 1377691206695391383,
      "staff_role": 1377691158897234000
    },
    "report": {
      "category_emoji": "🚨",
      "category_name": "Report",
      "category_description": "For reporting issues or rule violations.",
      "channel_format": "{ticket_owner_discord_username}-report",
      "channel_id": 1377691208683360379,
      "staff_role": 1382856462048428133
    }
  },
  "creation": {
    "channel_id": 1377691205156208770,
    "max_tickets_per_user": 1
  },
  "transcript": {
    "file_name": "{ticket_category}_{ticket_owner_discord_username}_{ticket_channel_id}.html",
    "upload": {
      "token": "github_pat_YOUR_GITHUB_TOKEN",
      "repository": "YourUsername/repository-name",
      "branch": "main"
    }
  },
  "log": 1377691201360232479
}
```

### Settings Explained:

#### Categories

Each category represents a type of ticket users can create:

| Setting                | Description                                                                                                    | Example                                   |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `category_emoji`       | Emoji displayed on button/dropdown                                                                             | "📩"                                      |
| `category_name`        | Display name for the category                                                                                  | "General Support"                         |
| `category_description` | Description shown in dropdown menu                                                                             | "For general support and questions."      |
| `channel_format`       | Naming pattern for created tickets                                                                             | "{ticket_owner_discord_username}-general" |
| `channel_id`           | For thread-based tickets: channel to create threads in<br>For channel-based tickets: use `category_id` instead | 1377691206695391383                       |
| `category_id`          | For channel-based tickets: category to create channels in                                                      | 1377691179721949336                       |
| `staff_role`           | Role ID with access to tickets                                                                                 | 1377691158897234000                       |

> **Note:** The first category determines whether tickets are created as channels (`category_id`) or threads (`channel_id`). All categories must use the same method.

#### Creation Settings

| Setting                | Description                                   | Example             |
| ---------------------- | --------------------------------------------- | ------------------- |
| `channel_id`           | Channel where ticket creation panel is posted | 1377691205156208770 |
| `max_tickets_per_user` | Maximum number of open tickets per user       | 1                   |

#### Transcript Settings

| Setting             | Description                                                       | Example                                                                      |
| ------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `file_name`         | Naming pattern for transcript files (use .txt or .html extension) | "{ticket*category}*{ticket*owner_discord_username}*{ticket_channel_id}.html" |
| `upload.token`      | GitHub personal access token (for GitHub upload)                  | "github_pat_YOUR_GITHUB_TOKEN"                                               |
| `upload.repository` | GitHub repository for transcript uploads                          | "YourUsername/repository-name"                                               |
| `upload.branch`     | Branch for transcript uploads                                     | "main"                                                                       |

#### Other Settings

| Setting | Description                                | Example             |
| ------- | ------------------------------------------ | ------------------- |
| `log`   | Channel ID for ticket logs and transcripts | 1377691201360232479 |

## 🧩 Advanced Features

### Channel vs Thread-based Tickets

You can choose between two methods for ticket creation:

- **Channel-based**: Creates a new text channel for each ticket

  - Requires `category_id` in configuration
  - Provides full channel permissions control
  - More visible in server channel list

- **Thread-based**: Creates a private thread for each ticket
  - Requires `channel_id` in configuration
  - Keeps server channel list cleaner
  - Uses Discord's built-in thread functionality

### Button vs Dropdown Creation Style

The system automatically determines the creation style based on your configuration:

- **Button Style**: Creates a button for each ticket category

  - Set `category_button_style` for each category (PRIMARY, SECONDARY, SUCCESS, DANGER)
  - Best for 1-5 ticket categories
  - More visual and direct

- **Dropdown Style**: Creates a dropdown menu for selecting ticket categories
  - Uses `category_description` for dropdown option descriptions
  - Better for 6+ ticket categories
  - Cleaner interface for many options

### Transcript Options

Two transcript formats are supported:

- **HTML Transcripts**: Rich formatting, includes avatars and embeds

  - Use `.html` extension in `transcript.file_name`
  - More visually appealing

- **Text Transcripts**: Simple text format
  - Use `.txt` extension in `transcript.file_name`
  - Smaller file size, simpler format

### GitHub Integration

Transcripts can be uploaded to GitHub for permanent storage:

```json
"transcript": {
  "file_name": "{ticket_category}_{ticket_owner_discord_username}_{ticket_channel_id}.html",
  "upload": {
    "token": "github_pat_YOUR_GITHUB_TOKEN",
    "repository": "YourUsername/repository-name",
    "branch": "main"
  }
}
```

Benefits:

- Permanent storage outside Discord
- Version history through Git
- Accessible through web URLs
- GitHub Pages support for HTML transcripts

To use GitHub Pages, enable it in your repository settings. The system will automatically use GitHub Pages URLs when available.

### Variable Substitution

Your ticket messages and channel names can include dynamic placeholders:

- `{ticket_owner_discord_username}` - Username of the ticket creator
- `{ticket_owner_discord_user_id}` - ID of the ticket creator
- `{ticket_owner_discord_user_mention}` - Mentions the ticket creator
- `{ticket_channel_name}` - Name of the ticket channel
- `{ticket_channel_id}` - ID of the ticket channel
- `{ticket_channel_mention}` - Mentions the ticket channel
- `{ticket_category}` - Name of the ticket category
- `{ticket_transcript_url}` - URL to the transcript (when using GitHub)

## 📋 Localization

The ticket system supports full localization through the language files:

```json
"ticket": {
  "messages": {
    "minecraft": {
      "staff": {
        "notify_on_mention": {
          "text": "{discord_username} has mentioned you in <click:open_url:'{discord_channel_url}'>a ticket channel</click>. Please check the ticket for more details."
        }
      },
      "user": {
        "notify_on_mention": {
          "text": "You have mentioned by staff member in <click:open_url:'{discord_channel_url}'>a ticket channel</click>. Please check the ticket for more details."
        },
        "notify_on_close": {
          "text": "Your ticket has been closed by {discord_staff_username}. If you have any further questions, please create a new ticket."
        }
      }
    },
    "system": {
      "startup": {
        "message_type": "embed",
        "content": {
          "title": "Ticket System",
          "description": "The ticket system is now online. You can create a ticket by selecting category under that message.",
          "color": "GREEN"
        }
      },
      "creation": {
        "general": {
          "message_type": "embed",
          "content": {
            "title": "New Ticket Created",
            "description": "A new ticket has been created by {ticket_owner_discord_user_mention}.",
            "color": "BLUE",
            "fields": [
              {
                "name": "Content",
                "value": "{ticket_general_content}"
              }
            ]
          }
        }
      }
    },
    "user": {
      "success": {
        "message_type": "embed",
        "content": {
          "title": "Ticket Created",
          "description": "Your ticket has been created successfully. Please check your DMs for further instructions.",
          "color": "BLUE"
        }
      },
      "failure": {
        "message_type": "embed",
        "content": {
          "title": "Ticket Creation Failed",
          "description": "Failed to create a ticket. Please try again later.",
          "color": "RED"
        }
      }
    },
    "log": {
      "transcript": {
        "message_type": "embed",
        "content": {
          "title": "Ticket Transcript",
          "description": "{ticket_owner_discord_user_mention}'s ticket transcript.",
          "color": "BLUE",
          "fields": [
            {
              "name": "Ticket Owner",
              "value": "{ticket_owner_discord_user_mention}"
            },
            {
              "name": "Ticket Category",
              "value": "{ticket_category}"
            },
            {
              "name": "Ticket ID",
              "value": "{ticket_channel_id}"
            },
            {
              "name": "Transcript",
              "value": "[Click here to see the transcript]({ticket_transcript_url})"
            }
          ]
        }
      }
    }
  },
  "menu": {
    "inner": {
      "close": {
        "emoji": "🔒",
        "label": "Close Ticket",
        "style": "DANGER"
      }
    },
    "outer": {
      "confirm": {
        "emoji": "✅",
        "label": "Confirm",
        "style": "SUCCESS"
      },
      "cancel": {
        "emoji": "❌",
        "label": "Cancel",
        "style": "SECONDARY"
      }
    }
  },
  "modal": {
    "general": {
      "title": "General Ticket",
      "fields": {
        "content": {
          "style": "PARAGRAPH",
          "label": "Content",
          "placeholder": "Enter the content of your ticket here."
        }
      }
    },
    "report": {
      "title": "Report Ticket",
      "fields": {
        "username": {
          "style": "SHORT",
          "label": "Username",
          "placeholder": "Enter the username of the user you want to report."
        },
        "content": {
          "style": "PARAGRAPH",
          "label": "Report Content",
          "placeholder": "Enter the content of your report here."
        }
      }
    }
  }
}
```

## 🔍 Troubleshooting

| Issue                       | Solution                                                                                |
| --------------------------- | --------------------------------------------------------------------------------------- |
| Ticket panel not appearing  | Check `creation.channel_id` is correct and bot has proper permissions                   |
| "Max tickets reached" error | User has reached their `max_tickets_per_user` limit; they should close existing tickets |
| Transcripts not generating  | Ensure hikari-chat-exporter is installed; check file permissions                        |
| GitHub uploads failing      | Verify GitHub token has correct permissions; check repository exists and is accessible  |
| Staff can't access tickets  | Ensure `staff_role` IDs are correct and roles are properly assigned                     |
| Error messages in console   | Look for error logs related to "ticket system" for specific issues                      |
| "Ticket system is disabled" | Ensure the system is properly configured in settings.json                               |
| Thread tickets not working  | Check if bot has permission to create private threads                                   |
| Channel tickets not working | Verify bot has permission to create channels and set permissions                        |
| Localization issues         | Ensure all required localization keys are present in your language files                |

## 📚 Examples

### Simple Thread-based Setup

```json
"ticket": {
  "categories": {
    "help": {
      "category_emoji": "❓",
      "category_name": "Help Desk",
      "category_description": "Get assistance with server features",
      "channel_format": "help-{ticket_owner_discord_username}",
      "channel_id": 1234567890123456789,
      "staff_role": 9876543210987654321
    }
  },
  "creation": {
    "channel_id": 1111222233334444555,
    "max_tickets_per_user": 1
  },
  "log": 5555666677778888999
}
```

### Advanced Channel-based Setup with Multiple Categories

```json
"ticket": {
  "categories": {
    "general": {
      "category_emoji": "📩",
      "category_name": "General Support",
      "category_button_style": "PRIMARY",
      "channel_format": "{ticket_owner_discord_username}-support",
      "category_id": 1111222233334444555,
      "staff_role": 9876543210987654321
    },
    "bugs": {
      "category_emoji": "🐛",
      "category_name": "Bug Reports",
      "category_button_style": "DANGER",
      "channel_format": "bug-{ticket_owner_discord_username}",
      "category_id": 1111222233334444555,
      "staff_role": 9876543210987654321
    },
    "appeals": {
      "category_emoji": "⚖️",
      "category_name": "Ban Appeals",
      "category_button_style": "SECONDARY",
      "channel_format": "appeal-{ticket_owner_discord_username}",
      "category_id": 1111222233334444555,
      "staff_role": 8765432109876543210
    }
  },
  "creation": {
    "channel_id": 2222333344445555666,
    "max_tickets_per_user": 2
  },
  "transcript": {
    "file_name": "{ticket_category}_{ticket_owner_discord_username}_{ticket_channel_id}.html",
    "upload": {
      "token": "github_pat_YOUR_GITHUB_TOKEN",
      "repository": "YourUsername/ticket-logs",
      "branch": "main"
    }
  },
  "log": 3333444455556666777
}
```
