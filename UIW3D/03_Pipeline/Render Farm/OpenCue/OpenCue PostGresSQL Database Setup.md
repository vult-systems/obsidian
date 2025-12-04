
---
## Server

- **Host**: 10.40.14.25 (Ubuntu 24.04.3 LTS)
- **Memory**: 31GB RAM
- **Existing services**: Perforce (native)

## What We Installed

1. **Java 17** - Required for Cuebot
   ```bash
   sudo apt install openjdk-17-jre-headless
   ```

2. **PostgreSQL 16** - Database for OpenCue
   ```bash
   sudo apt install postgresql postgresql-contrib
   ```
  
3. **Flyway** - Database migration tool
   ```bash
   sudo snap install flyway
   ```
  
4. **OpenCue repository**
   ```bash
   git clone https://github.com/AcademySoftwareFoundation/OpenCue.git ~/OpenCue
   ```

---
## Database Configuration

**Credentials:**
- Database name: `cuebot_local`
- Database user: `cuebot`
- Database password: `uiw3d`
- Host: `localhost`
- Port: `5432`

**Setup commands executed:**
```bash
# Create superuser for admin commands

sudo -u postgres createuser -s $USER

# Create database and user
createdb cuebot_local
createuser cuebot --pwprompt

# Grant permissions
psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO cuebot" cuebot_local
psql -c "GRANT CREATE ON DATABASE cuebot_local TO cuebot" cuebot_local
psql -c "GRANT ALL ON SCHEMA public TO cuebot" cuebot_local
```

---
## Schema Migration

Applied 28 migrations using Flyway:
```bash
cd ~/OpenCue

flyway -url=jdbc:postgresql://localhost/cuebot_local -user=cuebot -password=uiw3d -locations=filesystem:cuebot/src/main/resources/conf/ddl/postgres/migrations migrate

```

Loaded seed data:
```bash
psql -h localhost -U cuebot -f cuebot/src/main/resources/conf/ddl/postgres/seed_data.sql cuebot_local
```

---
## Why Flyway?
Flyway manages database schema as versioned migrations. Future OpenCue updates publish new migrations that can be applied incrementally without rebuilding the database - critical for production where job history must be preserved.
## Status
Database ready for Cuebot connection.

## Next Step
Deploy Cuebot (scheduler/dispatcher service).