# 📚 Wiki System Configuration Guide

## Overview

The Wiki System in MineBot provides an accessible knowledge base within your Discord server. This feature enables:

- 📋 **In-Discord documentation** for server rules, guides, and information
- 🌐 **Multi-language support** with locale-specific content
- 🔍 **Quick access** through slash commands with autocomplete
- 📱 **Embedded responses** for clean, formatted information

## Configuration Structure

The Wiki system is configured in the settings.json file under the `commands.wiki` section:

```json
"wiki": {
  "permissions": ["NONE"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 60,
    "allowed_invocations": 1
  }
}
```

## Configuration Options

| Option        | Description                     | Example           | Notes                              |
| ------------- | ------------------------------- | ----------------- | ---------------------------------- |
| `permissions` | Required Discord permissions    | `["NONE"]`        | Use `"NONE"` for all users         |
| `cooldown`    | Rate limiting for command usage | See configuration | Prevents abuse of the wiki command |

### Cooldown Configuration

| Option                | Description                       | Default          | Notes                                 |
| --------------------- | --------------------------------- | ---------------- | ------------------------------------- |
| `algorithm`           | Method for tracking cooldowns     | `"fixed_window"` | Options: fixed_window, sliding_window |
| `bucket`              | Scope of the cooldown             | `"user"`         | Options: user, channel, guild, global |
| `window_length`       | Duration of cooldown in seconds   | `60`             | Adjust based on usage patterns        |
| `allowed_invocations` | Number of uses allowed per window | `1`              | Balances accessibility with limits    |

## File Structure

Wiki content is organized in markdown files within the following directory structure:

```
configuration/
└── wiki/
    ├── en-US/        # English content
    │   ├── rules.md
    │   └── faq.md
    ├── tr/        # Turkish content
    │   ├── kurallar.md
    │   └── sss.md
    └── [locale]/     # Other language folders
```

## Wiki File Format

Each wiki file should be formatted as a markdown document with proper formatting:

```markdown
---
__Documentation Title__

- __[Useful Link](https://example.com)__ - Description of the link
---

### Section Header

Content goes here with standard markdown formatting.

## Larger Section Header

More content with **bold**, _italic_, or `code` formatting.
```

## Localization

Wiki messages are automatically localized through language files. Example from en-US.json:

```json
"wiki": {
  "command": {
    "label": "wiki",
    "description": "Get information from the wiki.",
    "options": {
      "query": {
        "label": "query",
        "description": "The query to search for."
      }
    }
  },
  "messages": {
    "user": {
      "success": {
        "message_type": "embed",
        "content": {
          "title": "{query} - Wiki Search Result",
          "description": "{result}",
          "color": "BLUE"
        }
      },
      "failure": {
        "message_type": "embed",
        "content": {
          "title": "Wiki Search Failed",
          "description": "Failed to retrieve the wiki information. Please try again later.",
          "color": "RED"
        }
      }
    }
  }
}
```

## Usage Instructions

### Adding Wiki Content

1. Create markdown files in the appropriate locale folder
2. Name files descriptively (e.g., `commands.md`, `rules.md`)
3. Use proper markdown formatting for clean display

### Accessing Wiki Content

Users can access wiki content using the slash command:

- Type `/wiki` to start
- Use autocomplete to find available articles
- Select an article to view its contents

## Example Configurations

### Basic Setup

```json
"wiki": {
  "permissions": ["NONE"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 30,
    "allowed_invocations": 3
  }
}
```

### Moderator-Only Wiki

```json
"wiki": {
  "permissions": ["MODERATE_MEMBERS"],
  "cooldown": {
    "algorithm": "fixed_window",
    "bucket": "user",
    "window_length": 10,
    "allowed_invocations": 5
  }
}
```
