# Database Setup Quick Start

This script helps you set up the database with ORM models.

## Prerequisites

- PostgreSQL installed and running
- Python virtual environment activated
- DATABASE_URL environment variable set

## Steps

### 1. Install Dependencies

```bash
cd src/server
pip install -r requirements.txt
```

### 2. Set Database URL

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/postgres"
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/postgres"
```

### 3. Initialize Database

Choose one of the following methods:

#### Option A: Using Alembic (Recommended for production)

```bash
# Navigate to server directory
cd src/server

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head

# Verify
alembic current
```

#### Option B: Direct Table Creation (Quick for development)

```bash
cd src/server
python -c "from core.database import init_db; init_db(); print('Database initialized!')"
```

### 4. Verify Tables Created

Connect to PostgreSQL and check:

```sql
\dt  -- List all tables

-- You should see:
-- users
-- conversations
-- messages
-- conversation_tags
-- message_references
```

## Troubleshooting

### Error: "relation already exists"

Your tables already exist. Either:
- Drop existing tables: `DROP TABLE IF EXISTS users, conversations, messages CASCADE;`
- Or use Alembic to manage: `alembic stamp head`

### Error: "could not connect to server"

Check:
1. PostgreSQL is running
2. DATABASE_URL is correct
3. User has proper permissions

### Error: "No module named 'alembic'"

Install dependencies: `pip install -r requirements.txt`

## Next Steps

After setup, you can:
- Start the server: `uvicorn api.main:app --reload`
- Create a new conversation via API
- Test with the chat widget

For more details, see: `docs/ORM_MIGRATION_GUIDE.md`
