# 🌐 MineBot Localization Guide

## Overview

MineBot's localization system allows full customization of all messages, menus, and command labels in multiple languages. This guide explains:

- 📂 How localization files are organized
- 💬 Message structure and formatting options
- 🔤 Available variables for dynamic content
- ✅ Best practices for localization

## File Structure

Localization files are stored in the following directory:

```
configuration/
└── localization/
    ├── en-US.json     # English (US)
    ├── tr.json        # Turkish
    └── [locale].json  # Other language files
```

Each file must be named according to the Discord locale identifier (e.g., `en-US`, `tr`).

## Message Structure

Messages in MineBot can be formatted in two primary ways:

### Plain Text Messages

```json
{
  "message_type": "plain",
  "content": {
    "text": "Hello, {discord_user_mention}!"
  }
}
```

### Embedded Messages

```json
{
  "message_type": "embed",
  "content": {
    "title": "Welcome Message",
    "description": "Welcome to our server, {discord_user_mention}!",
    "color": "GREEN",
    "fields": [
      {
        "name": "Server Rules",
        "value": "Please check the rules channel."
      }
    ]
  }
}
```

## Variable Reference

Variables allow you to insert dynamic content into messages. Different contexts provide different variables.

### Global Variables (Available Everywhere)

| Variable          | Description                   | Example               |
| ----------------- | ----------------------------- | --------------------- |
| `{error_message}` | Error details when applicable | "Invalid permissions" |

### User Variables

| Variable                       | Description                    | Example            |
| ------------------------------ | ------------------------------ | ------------------ |
| `{discord_user_mention}`       | Mentions the user              | @Username          |
| `{discord_username}`           | Username without mention       | Username           |
| `{discord_user_id}`            | Discord ID of the user         | 123456789012345678 |
| `{discord_staff_user_mention}` | Mentions the staff member      | @StaffName         |
| `{discord_staff_username}`     | Staff username without mention | StaffName          |
| `{discord_staff_user_id}`      | Discord ID of staff member     | 123456789012345678 |

### Minecraft-Related Variables

| Variable               | Description               | Example                 |
| ---------------------- | ------------------------- | ----------------------- |
| `{minecraft_username}` | Linked Minecraft username | Steve                   |
| `{minecraft_uuid}`     | Minecraft UUID            | a1b2c3d4-e5f6-g7h8-i9j0 |
| `{confirmation_code}`  | Account linking code      | ABC123                  |

### Channel & Server Variables

| Variable                | Description                | Example                          |
| ----------------------- | -------------------------- | -------------------------------- |
| `{channel_mention}`     | Mentions the channel       | #channel-name                    |
| `{discord_channel_url}` | Direct URL to the channel  | https://discord.com/channels/... |
| `{server_name}`         | Name of the Discord server | My Gaming Server                 |

### Moderation Variables

| Variable               | Description                         | Example           |
| ---------------------- | ----------------------------------- | ----------------- |
| `{reason}`             | Reason for moderation action        | "Violated rule 3" |
| `{duration}`           | Duration of temporary action        | "3 days"          |
| `{amount}`             | Number (for message clearing, etc.) | 15                |
| `{remaining_cooldown}` | Time left on cooldown               | "30 seconds"      |

### Ticket System Variables

| Variable                              | Description               | Example                             |
| ------------------------------------- | ------------------------- | ----------------------------------- |
| `{ticket_owner_discord_user_mention}` | Mentions ticket creator   | @Username                           |
| `{ticket_category}`                   | Category of the ticket    | "support"                           |
| `{ticket_channel_id}`                 | ID of the ticket channel  | 123456789012345678                  |
| `{ticket_transcript_url}`             | URL to ticket transcript  | https://example.com/transcripts/... |
| `{ticket_general_content}`            | Content of general ticket | "I need help with..."               |
| `{ticket_report_username}`            | Reported username         | "BadPlayer123"                      |
| `{ticket_report_content}`             | Content of report ticket  | "This user was harassing..."        |
| `{max_tickets}`                       | Maximum tickets per user  | 1                                   |

### Suggestion System Variables

| Variable       | Description         | Example             |
| -------------- | ------------------- | ------------------- |
| `{suggestion}` | The suggestion text | "Add new game mode" |

### Wiki System Variables

| Variable   | Description                | Example                   |
| ---------- | -------------------------- | ------------------------- |
| `{query}`  | Search query for wiki      | "rules"                   |
| `{result}` | Wiki search result content | "The server rules are..." |

## Context-Specific Sections

Different parts of the bot have different available variables:

### Moderation Commands

```json
"ban": {
  "messages": {
    "user": {
      "success": {
        "message_type": "embed",
        "content": {
          "title": "Ban Successful",
          "description": "{discord_user_mention} has been banned.",
          "color": "GREEN"
        }
      }
    },
    "log": {
      "success": {
        "message_type": "embed",
        "content": {
          "title": "User Banned",
          "description": "{discord_user_mention} has been banned.",
          "fields": [
            {
              "name": "Moderator",
              "value": "{discord_staff_user_mention}"
            },
            {
              "name": "Reason",
              "value": "{reason}"
            },
            {
              "name": "Duration",
              "value": "{duration}"
            }
          ]
        }
      }
    }
  }
}
```

### Suggestion System

```json
"suggest": {
  "messages": {
    "pending": {
      "success": {
        "message_type": "embed",
        "content": {
          "title": "Suggestion Submitted",
          "description": "{discord_user_mention} has submitted a suggestion.",
          "fields": [
            {
              "name": "Suggestion",
              "value": "{suggestion}"
            }
          ]
        }
      }
    },
    "result": {
      "approve": {
        "message_type": "embed",
        "content": {
          "title": "Suggestion Approved",
          "description": "{discord_user_mention}'s suggestion has been approved.",
          "fields": [
            {
              "name": "Moderator",
              "value": "{discord_staff_user_mention}"
            },
            {
              "name": "Reason",
              "value": "{reason}"
            },
            {
              "name": "Suggestion",
              "value": "{suggestion}"
            }
          ]
        }
      }
    }
  }
}
```

### Ticket System

```json
"ticket": {
  "messages": {
    "system": {
      "creation": {
        "general": {
          "message_type": "embed",
          "content": {
            "title": "New Ticket Created",
            "description": "A new ticket has been created by {ticket_owner_discord_user_mention}.",
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
    "log": {
      "transcript": {
        "message_type": "embed",
        "content": {
          "title": "Ticket Transcript",
          "description": "{ticket_owner_discord_user_mention}'s ticket transcript.",
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
              "name": "Transcript",
              "value": "[Click here to see the transcript]({ticket_transcript_url})"
            }
          ]
        }
      }
    }
  }
}
```

## Command Localization

Commands and options can be localized with these structures:

```json
"command": {
  "label": "wiki",
  "description": "Get information from the wiki.",
  "options": {
    "query": {
      "label": "query",
      "description": "The query to search for."
    }
  }
}
```

## Time Format Variables

Time units can be customized in your locale file:

```json
"time_units": {
  "year": {
    "singular": ["year", "yr", "y"],
    "plural": ["years", "yrs", "y"]
  },
  "month": {
    "singular": ["month", "mo"],
    "plural": ["months", "mos"]
  },
  // ... other time units
}
```
