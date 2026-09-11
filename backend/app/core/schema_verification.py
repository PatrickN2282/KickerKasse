"""Small, explicit postconditions for the existing startup migrations."""

from sqlalchemy import CheckConstraint, Enum, String, inspect, text

from app.models import Base


CONSTRAINT_COLUMN_DEPENDENCIES = {
    "products": {
        "ck_products_price_nonnegative": {"price_cents"},
        "ck_products_member_price_nonnegative": {"member_price_cents"},
        "ck_products_stock_nonnegative": {"stock_quantity"},
        "ck_products_minimum_stock_nonnegative": {"minimum_stock_quantity"},
        "ck_products_tax_rate_range": {"tax_rate"},
        "ck_products_name_not_blank": {"name"},
    },
    "members": {
        "ck_members_balance_nonnegative": {"balance_cents"},
        "ck_members_name_not_blank": {"name"},
        "ck_members_combined_name_length": {"first_name", "last_name"},
    },
    "categories": {
        "ck_categories_name_not_blank": {"name"},
    },
}


def _constraint_dependencies(table_name, constraint_name):
    return CONSTRAINT_COLUMN_DEPENDENCIES.get(table_name, {}).get(constraint_name, set())


def verify_schema(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    errors = []
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            errors.append(f"missing table {table.name}")
            continue
        actual = {column["name"]: column for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in actual:
                errors.append(f"missing column {table.name}.{column.name}")
                continue
            expected, found = column.type, actual[column.name]["type"]
            if isinstance(expected, Enum):
                if not set(expected.enums) <= set(getattr(found, "enums", [])):
                    errors.append(f"incomplete enum {table.name}.{column.name}")
            elif expected._type_affinity is not found._type_affinity:
                errors.append(f"wrong column type {table.name}.{column.name}")
            elif isinstance(expected, String) and expected.length:
                capacity = getattr(found, "length", None)
                if capacity is not None and capacity < expected.length:
                    errors.append(f"column too short {table.name}.{column.name}")
    if errors:
        raise RuntimeError("Schema verification failed: " + "; ".join(errors))


def validate_existing_data(engine):
    """Report offending IDs; never repair balances or quantities implicitly."""
    errors = []
    with engine.connect() as conn:
        for table_name in ("products", "members", "categories"):
            table = Base.metadata.tables[table_name]
            existing_columns = {column["name"] for column in inspect(conn).get_columns(table_name)}
            rules = [(c.name, str(c.sqltext)) for c in table.constraints if isinstance(c, CheckConstraint)]
            for column in table.columns:
                if column.name not in existing_columns:
                    continue
                if not column.nullable:
                    rules.append((column.name + "_required", f'"{column.name}" IS NOT NULL'))
                if isinstance(column.type, String) and not isinstance(column.type, Enum) and column.type.length:
                    rules.append((column.name + "_length", f'length("{column.name}") <= {column.type.length}'))
            for name, expression in rules:
                referenced_columns = _constraint_dependencies(table_name, name)
                if name.endswith("_required") or name.endswith("_length"):
                    referenced_columns = {name.rsplit("_", 1)[0]}
                if not referenced_columns <= existing_columns:
                    continue
                ids = conn.execute(text(f'SELECT id FROM "{table_name}" WHERE NOT ({expression}) ORDER BY id LIMIT 20')).scalars().all()
                if ids:
                    errors.append(f"{table_name}.{name}: IDs {ids}")
    if errors:
        raise RuntimeError("Invalid existing data; review before upgrade (up to 20 IDs per rule): " + "; ".join(errors))


def ensure_data_constraints(engine):
    validate_existing_data(engine)
    with engine.begin() as conn:
        inspector = inspect(conn)
        for table_name in ("products", "members", "categories"):
            existing = {c["name"] for c in inspector.get_check_constraints(table_name)}
            columns = {c["name"]: c for c in inspector.get_columns(table_name)}
            for column in Base.metadata.tables[table_name].columns:
                if column.name not in columns:
                    continue
                if not column.nullable and columns[column.name]["nullable"]:
                    conn.execute(text(f'ALTER TABLE "{table_name}" ALTER COLUMN "{column.name}" SET NOT NULL'))
            for constraint in Base.metadata.tables[table_name].constraints:
                if not isinstance(constraint, CheckConstraint):
                    continue
                referenced_columns = _constraint_dependencies(table_name, constraint.name)
                if not referenced_columns <= columns.keys():
                    continue
                if constraint.name not in existing:
                    conn.execute(text(f'ALTER TABLE "{table_name}" ADD CONSTRAINT "{constraint.name}" CHECK ({constraint.sqltext}) NOT VALID'))
                conn.execute(text(f'ALTER TABLE "{table_name}" VALIDATE CONSTRAINT "{constraint.name}"'))


def verify_data_constraints(engine):
    inspector = inspect(engine)
    for table_name in ("products", "members", "categories"):
        actual = {c["name"] for c in inspector.get_check_constraints(table_name)}
        required = {c.name for c in Base.metadata.tables[table_name].constraints if isinstance(c, CheckConstraint)}
        if not required <= actual:
            raise RuntimeError(f"Missing constraints in {table_name}: {sorted(required - actual)}")
        columns = {c["name"]: c for c in inspector.get_columns(table_name)}
        for column in Base.metadata.tables[table_name].columns:
            if not column.nullable and columns[column.name]["nullable"]:
                raise RuntimeError(f"Missing NOT NULL constraint: {table_name}.{column.name}")
    with engine.connect() as conn:
        invalid = conn.execute(text("SELECT conname FROM pg_constraint WHERE contype='c' AND NOT convalidated AND connamespace=current_schema()::regnamespace")).scalars().all()
        if invalid:
            raise RuntimeError(f"Unvalidated constraints: {invalid}")


def run_versioned_steps(engine, steps):
    """Journal successful steps only; interrupted idempotent steps run again."""
    with engine.connect() as lock:
        lock.execute(text("SELECT pg_advisory_lock(614065)"))
        lock.commit()
        try:
            with engine.begin() as conn:
                conn.execute(text("""CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(30) NOT NULL, step VARCHAR(80) NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (version, step))"""))
            for version, name, operation in steps:
                with engine.connect() as conn:
                    applied = conn.execute(text("SELECT 1 FROM schema_migrations WHERE version=:v AND step=:s"),
                                           {"v": version, "s": name}).scalar()
                if applied:
                    continue
                operation()
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO schema_migrations(version,step) VALUES (:v,:s)"),
                                 {"v": version, "s": name})
            verify_schema(engine)
            verify_data_constraints(engine)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(614065)"))
            lock.commit()
