# Alembic Migrations

This directory contains database migration scripts managed by Alembic.

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database URL

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Or edit `alembic.ini` directly.

### 3. Create Initial Migration

Generate a migration script based on your models:

```bash
cd src/server
alembic revision --autogenerate -m "Initial migration"
```

### 4. Apply Migrations

Apply all pending migrations to the database:

```bash
alembic upgrade head
```

## Common Commands

- **Create new migration**: `alembic revision --autogenerate -m "Description"`
- **Apply migrations**: `alembic upgrade head`
- **Rollback one version**: `alembic downgrade -1`
- **Show current version**: `alembic current`
- **Show migration history**: `alembic history`
- **Rollback to specific version**: `alembic downgrade <revision_id>`

## Migration Best Practices

1. Always review auto-generated migrations before applying
2. Test migrations in development before production
3. Keep migrations small and focused
4. Never edit applied migrations
5. Use descriptive migration messages

## Troubleshooting

### "Target database is not up to date"

Run: `alembic upgrade head`

### "Can't locate revision identified by"

Your database may be out of sync. Check with: `alembic current`

### Fresh database setup

If starting fresh, you can use:

```bash
alembic upgrade head
```

This will create all tables from scratch.
