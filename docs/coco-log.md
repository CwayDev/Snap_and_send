# Snowflake Cortex Code (CoCo) Session Log

This document records the prompts executed with Snowflake Cortex Code (CoCo) / Cortex CLI, along with the SQL queries, schema investigations, and pipeline/dashboard logic produced during the development of **Snap & Understand**.

---

## Session 1: Dataset & Catalog Discovery

- **Timestamp:** 2026-10-24 13:04:10
- **CLI / Tool:** Snowflake CLI (`snow`) / Cortex Code (`cortex`)
- **Prompt:** "Explore available shared datasets and tables in SNOWFLAKE_SAMPLE_DATA to identify schemas with product catalog, retail parts, orders, and supplier data for multimodal entity grounding."
- **Generated Queries / Response:**
  ```sql
  SHOW SCHEMAS IN DATABASE SNOWFLAKE_SAMPLE_DATA;
  -- Result: TPCH_SF1, TPCH_SF10, TPCDS_SF10TCL, TPCDS_SF100TCL

  SHOW TABLES IN SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1;
  -- Tables discovered:
  -- 1. PART (200,000 items: manufacturer, brand, container, size, retail price)
  -- 2. ORDERS (1,500,000 order receipts: order key, order date, total price, clerk, status)
  -- 3. LINEITEM (6,000,000 line item entries: quantities, extended prices, discounts, taxes)
  -- 4. SUPPLIER (10,000 vendors/suppliers: address, phone, account balance)
  -- 5. CUSTOMER (150,000 purchasers: market segment, account balance)
  ```
- **Action Taken:** Selected `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` as the primary grounding dataset. The 3 categories mapped are:
  1. `Product Label` -> Queried against `TPCH_SF1.PART`
  2. `Receipt / Invoice` -> Queried against `TPCH_SF1.ORDERS` and `TPCH_SF1.LINEITEM`
  3. `Supplier / Vendor Document` -> Queried against `TPCH_SF1.SUPPLIER`

---

## Session 2: Schema Inspection & Lookup Query Generation

- **Timestamp:** 2026-10-24 13:05:56
- **CLI / Tool:** Cortex Code (`cortex`) / Snowflake CLI
- **Prompt:** "Generate optimized SQL queries to look up parts by name or brand, orders by order key, and suppliers by name from the TPCH_SF1 dataset with case-insensitive search and fuzzy matching."
- **Generated Queries:**
  ```sql
  -- 1. Product / Part Lookup
  SELECT P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE, P_SIZE, P_CONTAINER, P_RETAILPRICE, P_COMMENT
  FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART
  WHERE ILIKE(P_NAME, '%:search_term%') OR ILIKE(P_BRAND, '%:search_term%')
  LIMIT 5;

  -- 2. Receipt / Order Lookup
  SELECT O.O_ORDERKEY, O.O_ORDERDATE, O.O_TOTALPRICE, O.O_ORDERSTATUS, O.O_CLERK,
         L.L_PARTKEY, L.L_QUANTITY, L.L_EXTENDEDPRICE
  FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS O
  LEFT JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM L ON O.O_ORDERKEY = L.L_ORDERKEY
  WHERE O.O_ORDERKEY = :order_key
  LIMIT 10;

  -- 3. Supplier / Vendor Lookup
  SELECT S_SUPPKEY, S_NAME, S_ADDRESS, S_PHONE, S_ACCTBAL, S_COMMENT
  FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER
  WHERE ILIKE(S_NAME, '%:search_term%') OR ILIKE(S_PHONE, '%:search_term%')
  LIMIT 5;
  ```
- **Action Taken:** Integrated these parameterized lookup queries into the core application grounding engine (`src/snowflake_client.py`).

---

## Session 3: Snap Logging Schema & Analytics Dashboard Queries

- **Timestamp:** 2026-10-24 13:06:53
- **CLI / Tool:** Cortex Code (`cortex`)
- **Prompt:** "Design an audit table SNAP_LOGS inside database SNAP_DB, schema APP to log image snaps (category, language, grounding source, item identified, timestamp). Then write aggregation queries for an interactive Streamlit dashboard."
- **Generated Queries:**
  ```sql
  -- Create audit table (never logs image binary, only metadata)
  CREATE DATABASE IF NOT EXISTS SNAP_DB;
  CREATE SCHEMA IF NOT EXISTS SNAP_DB.APP;
  CREATE TABLE IF NOT EXISTS SNAP_DB.APP.SNAP_LOGS (
      ID NUMBER AUTOINCREMENT,
      CATEGORY VARCHAR(100),
      LANGUAGE VARCHAR(50),
      GROUNDING_SOURCE VARCHAR(50),
      ITEM_IDENTIFIED VARCHAR(255),
      TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
  );

  -- Dashboard Metric: Total Snaps
  SELECT COUNT(*) AS TOTAL_SNAPS FROM SNAP_DB.APP.SNAP_LOGS;

  -- Dashboard Metric: Counts by Category
  SELECT CATEGORY, COUNT(*) AS COUNT
  FROM SNAP_DB.APP.SNAP_LOGS
  GROUP BY CATEGORY
  ORDER BY COUNT DESC;

  -- Dashboard Metric: Counts by Language
  SELECT LANGUAGE, COUNT(*) AS COUNT
  FROM SNAP_DB.APP.SNAP_LOGS
  GROUP BY LANGUAGE
  ORDER BY COUNT DESC;

  -- Dashboard Metric: Counts by Grounding Source (Snowflake vs Web Fallback)
  SELECT GROUNDING_SOURCE, COUNT(*) AS COUNT
  FROM SNAP_DB.APP.SNAP_LOGS
  GROUP BY GROUNDING_SOURCE;
  ```
- **Action Taken:** Successfully created `SNAP_DB.APP.SNAP_LOGS` table and built dashboard visualization queries into `app.py`.
