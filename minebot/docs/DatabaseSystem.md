# Database URL Configuration Guide for MineBot

MineBot supports three types of database connections through SQLAlchemy's URL-based connection system. Each database type requires a specific format for proper connection.

## 🗄️ Supported Database Types

MineBot supports three database engines:

| Database Type  | Description                | Best For                         |
| -------------- | -------------------------- | -------------------------------- |
| **SQLite**     | File-based, lightweight    | Development, small installations |
| **MySQL**      | Server-based, widely used  | Medium-sized deployments         |
| **PostgreSQL** | Server-based, feature-rich | Production, large deployments    |

## 🔌 Database URL Formats

### 1. SQLite

```
sqlite+aiosqlite:///path/to/database.db
```

- 📁 Simple, file-based database
- 🚀 Ideal for development or small installations
- ℹ️ The three slashes (`///`) indicate a relative path from the current directory
- 📝 Example: `sqlite+aiosqlite:///data/bot.db`

### 2. MySQL

```
mysql+aiomysql://username:password@hostname:port/database_name
```

- 🖥️ Server-based database requiring MySQL/MariaDB installation
- 📝 Example: `mysql+aiomysql://minebot_user:secure_password@localhost:3306/minebot_db`

### 3. PostgreSQL

```
postgresql+asyncpg://username:password@hostname:port/database_name
```

- 🖥️ Server-based database requiring PostgreSQL installation
- 📝 Example: `postgresql+asyncpg://minebot_user:secure_password@localhost:5432/minebot_db`

## ⚙️ Configuration

To configure your database connection:

1. Edit the `settings.json` file in the configuration directory
2. Update the `database.url` property with your chosen connection string:

```json
"database": {
  "url": "your_database_url_here"
}
```

## 🔒 Security Considerations

| Best Practice             | Description                                                      |
| ------------------------- | ---------------------------------------------------------------- |
| **Secure Credentials**    | Store database credentials in a safe location                    |
| **Strong Passwords**      | Use complex passwords for database users                         |
| **Environment Variables** | Consider using environment variables for sensitive information   |
| **Least Privilege**       | Restrict database user permissions to only what's necessary      |
| **Network Security**      | For remote databases, ensure proper firewall and access controls |

## 📋 Quick Reference

| Database   | Default Port | Driver    | URL Format Example                                      |
| ---------- | ------------ | --------- | ------------------------------------------------------- |
| SQLite     | N/A          | aiosqlite | `sqlite+aiosqlite:///data/bot.db`                       |
| MySQL      | 3306         | aiomysql  | `mysql+aiomysql://user:pass@localhost:3306/db_name`     |
| PostgreSQL | 5432         | asyncpg   | `postgresql+asyncpg://user:pass@localhost:5432/db_name` |

## 🔄 Backup

- Always back up your database before major changes
- For production use, implement regular backup schedules
