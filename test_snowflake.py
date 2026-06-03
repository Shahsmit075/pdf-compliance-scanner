"""
Snowflake FULL verification — SNOWFLAKE_SAMPLE_DATA / TPCH_SF10
Correct credentials confirmed by discovery.
"""
import snowflake.connector

ACCOUNT   = "YSIBBUB-WV28708"
USER      = "SMITSHAH12"
PASSWORD  = "MVkw8eX4GKpfmR6"
ROLE      = "ACCOUNTADMIN"
WAREHOUSE = "COMPUTE_WH"
DATABASE  = "SNOWFLAKE_SAMPLE_DATA"   # ← correct
SCHEMA    = "TPCH_SF10"               # ← correct (schema inside SNOWFLAKE_SAMPLE_DATA)

print("=" * 65)
print("SNOWFLAKE CONNECTION — FULL VERIFICATION")
print("=" * 65)
print(f"  Account   : {ACCOUNT}")
print(f"  User      : {USER}")
print(f"  Database  : {DATABASE}")
print(f"  Schema    : {SCHEMA}")
print(f"  Warehouse : {WAREHOUSE}")
print(f"  Role      : {ROLE}")
print()

conn = snowflake.connector.connect(
    account   = ACCOUNT,
    user      = USER,
    password  = PASSWORD,
    role      = ROLE,
    warehouse = WAREHOUSE,
    database  = DATABASE,
    schema    = SCHEMA,
    login_timeout = 30,
)
cur = conn.cursor()
print("✓ Connected\n")

# ── TEST 1: Session context ────────────────────────────────────────────────────
print("── TEST 1: Session context ─────────────────────────────────────")
for q, label in [
    ("SELECT CURRENT_USER()",      "User"),
    ("SELECT CURRENT_ROLE()",      "Role"),
    ("SELECT CURRENT_DATABASE()",  "Database"),
    ("SELECT CURRENT_SCHEMA()",    "Schema"),
    ("SELECT CURRENT_WAREHOUSE()", "Warehouse"),
    ("SELECT CURRENT_VERSION()",   "Snowflake Version"),
]:
    cur.execute(q)
    print(f"  {label:<20}: {cur.fetchone()[0]}")

# ── TEST 2: All tables in TPCH_SF10 ───────────────────────────────────────────
print("\n── TEST 2: Tables in SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 ──────────")
cur.execute("SHOW TABLES IN SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF10")
tables = [r[1] for r in cur.fetchall()]
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF10.{t}")
    rc = cur.fetchone()[0]
    print(f"  📋 {t:<25} {rc:>15,} rows")

# ── TEST 3: Sample queries ─────────────────────────────────────────────────────
print("\n── TEST 3: Sample queries ──────────────────────────────────────")

# ORDERS
cur.execute("""
    SELECT O_ORDERKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE
    FROM   SNOWFLAKE_SAMPLE_DATA.TPCH_SF10.ORDERS
    ORDER  BY O_TOTALPRICE DESC
    LIMIT  5
""")
rows = cur.fetchall()
print("  Top 5 orders by value:")
for r in rows:
    print(f"    Key={r[0]:<10} Status={r[1]}  Price=${r[2]:>12,.2f}  Date={r[3]}")

# CUSTOMER count by nation (joining)
print("\n  Customer count by nation (top 5):")
cur.execute("""
    SELECT N.N_NAME, COUNT(*) AS CUST_COUNT
    FROM   SNOWFLAKE_SAMPLE_DATA.TPCH_SF10.CUSTOMER C
    JOIN   SNOWFLAKE_SAMPLE_DATA.TPCH_SF10.NATION   N ON C.C_NATIONKEY = N.N_NATIONKEY
    GROUP  BY N.N_NAME
    ORDER  BY CUST_COUNT DESC
    LIMIT  5
""")
for r in cur.fetchall():
    print(f"    {r[0]:<25} {r[1]:>8,} customers")

# Revenue by year
print("\n  Revenue by order year:")
cur.execute("""
    SELECT YEAR(O_ORDERDATE) AS YR, SUM(O_TOTALPRICE) AS TOTAL_REVENUE
    FROM   SNOWFLAKE_SAMPLE_DATA.TPCH_SF10.ORDERS
    GROUP  BY YR
    ORDER  BY YR
""")
for r in cur.fetchall():
    print(f"    {r[0]}  ${r[1]:>20,.2f}")

cur.close()
conn.close()

print("\n" + "=" * 65)
print("✅  ALL TESTS PASSED — Snowflake is fully connected and working!")
print("=" * 65)
print(f"\n📌 Use these in the app (Module 04 → Add New Source → Snowflake):")
print(f"   Account   : {ACCOUNT}")
print(f"   User      : {USER}")
print(f"   Database  : {DATABASE}")
print(f"   Schema    : {SCHEMA}")
print(f"   Warehouse : {WAREHOUSE}")
print(f"   Role      : {ROLE}")
