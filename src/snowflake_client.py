import os
from datetime import datetime
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

class SnowflakeClient:
    def __init__(self):
        self.account = os.getenv("SNOWFLAKE_ACCOUNT", "WAYITQN-YZ34843")
        self.user = os.getenv("SNOWFLAKE_USER", "snap_user")
        self.password = os.getenv("SNOWFLAKE_PASSWORD", "")
        self.role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_LEARNING_WH")
        self.database = os.getenv("SNOWFLAKE_DATABASE", "SNAP_DB")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA", "APP")

    def get_connection(self):
        conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            role=self.role,
            warehouse=self.warehouse,
        )
        try:
            cur = conn.cursor()
            if self.warehouse:
                cur.execute(f"USE WAREHOUSE {self.warehouse}")
            cur.close()
        except Exception:
            pass
        return conn

    def lookup_product(self, term: str) -> list[dict]:
        """Lookup in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            words = [w.strip() for w in term.replace("-", " ").split() if len(w.strip()) > 2]
            conditions = []
            params = []
            for w in words[:3]:
                conditions.append("(ILIKE(P_NAME, %s) OR ILIKE(P_BRAND, %s) OR ILIKE(P_TYPE, %s))")
                params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
            
            if not conditions:
                conditions = ["(ILIKE(P_NAME, %s) OR ILIKE(P_BRAND, %s))"]
                params = [f"%{term}%", f"%{term}%"]

            query = f"""
                SELECT P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE, P_SIZE, P_CONTAINER, P_RETAILPRICE, P_COMMENT
                FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART
                WHERE {' OR '.join(conditions)}
                LIMIT 5
            """
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()

    def lookup_receipt(self, order_key_or_term: str) -> list[dict]:
        """Lookup in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS and LINEITEM"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            clean_digits = "".join(filter(str.isdigit, str(order_key_or_term)))
            if clean_digits:
                query = """
                    SELECT O.O_ORDERKEY, O.O_ORDERDATE, O.O_TOTALPRICE, O.O_ORDERSTATUS, O.O_CLERK,
                           L.L_PARTKEY, L.L_QUANTITY, L.L_EXTENDEDPRICE
                    FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS O
                    LEFT JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM L ON O.O_ORDERKEY = L.L_ORDERKEY
                    WHERE O.O_ORDERKEY = %s
                    LIMIT 5
                """
                cur.execute(query, (int(clean_digits),))
            else:
                query = """
                    SELECT O_ORDERKEY, O_ORDERDATE, O_TOTALPRICE, O_ORDERSTATUS, O_CLERK
                    FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
                    LIMIT 3
                """
                cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()

    def lookup_supplier(self, term: str) -> list[dict]:
        """Lookup in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT S_SUPPKEY, S_NAME, S_ADDRESS, S_PHONE, S_ACCTBAL, S_COMMENT
                FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER
                WHERE ILIKE(S_NAME, %s) OR ILIKE(S_PHONE, %s)
                LIMIT 5
            """
            like_term = f"%{term}%"
            cur.execute(query, (like_term, like_term))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()

    def log_snap(self, category: str, language: str, source: str, item_identified: str):
        """Log snap to SNAP_DB.APP.SNAP_LOGS (never logs image binary)"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO SNAP_DB.APP.SNAP_LOGS (CATEGORY, LANGUAGE, GROUNDING_SOURCE, ITEM_IDENTIFIED)
                VALUES (%s, %s, %s, %s)
            """, (category, language, source, item_identified[:255]))
            conn.commit()
        except Exception as e:
            print(f"Failed to log snap to Snowflake: {e}")
        finally:
            conn.close()

    def get_dashboard_metrics(self) -> dict:
        """Fetch real-time analytics from SNAP_DB.APP.SNAP_LOGS"""
        conn = self.get_connection()
        metrics = {
            "total_snaps": 0,
            "by_category": [],
            "by_language": [],
            "by_source": [],
            "recent": []
        }
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM SNAP_DB.APP.SNAP_LOGS")
            metrics["total_snaps"] = cur.fetchone()[0]

            cur.execute("SELECT CATEGORY, COUNT(*) FROM SNAP_DB.APP.SNAP_LOGS GROUP BY CATEGORY ORDER BY 2 DESC")
            metrics["by_category"] = cur.fetchall()

            cur.execute("SELECT LANGUAGE, COUNT(*) FROM SNAP_DB.APP.SNAP_LOGS GROUP BY LANGUAGE ORDER BY 2 DESC")
            metrics["by_language"] = cur.fetchall()

            cur.execute("SELECT GROUNDING_SOURCE, COUNT(*) FROM SNAP_DB.APP.SNAP_LOGS GROUP BY GROUNDING_SOURCE")
            metrics["by_source"] = cur.fetchall()

            cur.execute("SELECT ID, CATEGORY, LANGUAGE, GROUNDING_SOURCE, ITEM_IDENTIFIED, TIMESTAMP FROM SNAP_DB.APP.SNAP_LOGS ORDER BY ID DESC LIMIT 10")
            metrics["recent"] = cur.fetchall()
        except Exception as e:
            print(f"Error loading dashboard metrics: {e}")
        finally:
            conn.close()
        return metrics
