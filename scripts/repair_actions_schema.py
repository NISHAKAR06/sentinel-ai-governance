import os
import psycopg2


def to_sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return url


def column_type(cur, table: str, column: str):
    cur.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    row = cur.fetchone()
    return row[0] if row else None


def ensure_legacy_defaults(cur):
    stmts = [
        "ALTER TABLE actions ALTER COLUMN action_type SET DEFAULT 'READ'",
        "ALTER TABLE actions ALTER COLUMN payload SET DEFAULT '{}'::json",
        "ALTER TABLE actions ALTER COLUMN record_count SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN user_count SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN regulatory_tags SET DEFAULT '[]'::json",
        "ALTER TABLE actions ALTER COLUMN total_score SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN reversibility_score SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN data_scope_score SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN regulatory_score SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN confidence_score SET DEFAULT 0",
        "ALTER TABLE actions ALTER COLUMN tier SET DEFAULT 'low'",
        "ALTER TABLE actions ALTER COLUMN preview_language SET DEFAULT 'en'",
        "ALTER TABLE actions ALTER COLUMN action_type DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN payload DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN record_count DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN user_count DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN regulatory_tags DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN total_score DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN reversibility_score DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN data_scope_score DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN regulatory_score DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN confidence_score DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN tier DROP NOT NULL",
        "ALTER TABLE actions ALTER COLUMN preview_language DROP NOT NULL",
    ]
    for stmt in stmts:
        cur.execute(stmt)


def migrate_action_id_to_uuid(cur):
    id_type = column_type(cur, "actions", "id")
    if id_type == "uuid":
        print("actions.id is already uuid.")
        return
    if id_type != "integer":
        raise RuntimeError(f"Unsupported actions.id type: {id_type}")

    print("Migrating actions.id from integer to uuid...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    cur.execute("ALTER TABLE actions ADD COLUMN IF NOT EXISTS id_uuid uuid")
    cur.execute("UPDATE actions SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")

    # Drop legacy FKs that still point to integer actions.id.
    cur.execute(
        """
        SELECT conrelid::regclass::text AS table_name, conname
        FROM pg_constraint
        WHERE confrelid = 'actions'::regclass AND contype = 'f'
        """
    )
    for table_name, fk_name in cur.fetchall():
        if table_name == "audit_log":
            cur.execute(f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{fk_name}"')

    cur.execute(
        """
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'actions'::regclass AND contype = 'p'
        """
    )
    pk = cur.fetchone()
    if pk:
        cur.execute(f'ALTER TABLE actions DROP CONSTRAINT "{pk[0]}"')

    cur.execute("ALTER TABLE actions DROP COLUMN id")
    cur.execute("ALTER TABLE actions RENAME COLUMN id_uuid TO id")
    cur.execute("ALTER TABLE actions ALTER COLUMN id SET NOT NULL")
    cur.execute("ALTER TABLE actions ADD PRIMARY KEY (id)")
    cur.execute("ALTER TABLE actions ALTER COLUMN id SET DEFAULT gen_random_uuid()")

    print("actions.id migrated to uuid.")


def main():
    raw = os.getenv("DATABASE_URL") or os.getenv("PG_URL")
    if not raw:
        raise SystemExit("DATABASE_URL or PG_URL must be set")
    url = to_sync_url(raw)

    conn = psycopg2.connect(url)
    conn.autocommit = False
    try:
        cur = conn.cursor()
        ensure_legacy_defaults(cur)
        migrate_action_id_to_uuid(cur)
        conn.commit()
        print("Schema repair complete.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
