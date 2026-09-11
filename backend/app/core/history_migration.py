from sqlalchemy import inspect, text


def migrate_history(engine):
    additions = {
        "members": [("archived_at", "TIMESTAMP")],
        "transactions": [("booking_type", "VARCHAR(40)")],
        "transaction_items": [("snapshot_version", "INTEGER"), ("product_group_name", "VARCHAR(120)"),
            ("category_name", "VARCHAR(120)"), ("tax_rate_snapshot", "FLOAT"),
            ("internal_material_unit_value_cents", "INTEGER")],
    }
    with engine.begin() as conn:
        for table, columns in additions.items():
            existing = {c["name"] for c in inspect(conn).get_columns(table)}
            for name, sql_type in columns:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_members_archived_at ON members(archived_at)"))
        # Historical catalog/tax values cannot be reconstructed reliably. Leave them NULL.
        conn.execute(text("""UPDATE transactions SET booking_type = 'MEMBER_BALANCE_RECHARGE'
            WHERE type = 'RECHARGE' AND booking_type IS NULL AND member_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM club_account_entries c WHERE c.transaction_id = transactions.id)"""))
        conn.execute(text("""UPDATE transactions SET booking_type = 'CLUB_ACCOUNT_TOP_UP'
            WHERE type = 'RECHARGE' AND booking_type IS NULL
            AND EXISTS (SELECT 1 FROM club_account_entries c WHERE c.transaction_id = transactions.id)"""))
