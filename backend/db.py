import snowflake.connector
import os
from typing import Optional, Dict, List, Any

class SnowflakeDB:
    """Snowflake database connection and operations manager"""
    
    def __init__(self):
        self.user = os.getenv('SNOWFLAKE_USER')
        self.password = os.getenv('SNOWFLAKE_PASSWORD')
        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
        self.database = os.getenv('SNOWFLAKE_DATABASE')
        self.schema = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
    
    def get_connection(self) -> Optional[snowflake.connector.SnowflakeConnection]:
        """Create and return a Snowflake connection"""
        try:
            conn = snowflake.connector.connect(
                user=self.user,
                password=self.password,
                account=self.account,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            return conn
        except Exception as e:
            print(f"Error connecting to Snowflake: {e}")
            return None
    
    def execute_query(self, sql_query: str) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            
            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            # Fetch all rows
            rows = cur.fetchall()
            
            cur.close()
            
            return {
                'columns': columns,
                'rows': [list(row) for row in rows],
                'row_count': len(rows)
            }
        except Exception as e:
            print(f"Query error: {e}")
            return None
        finally:
            conn.close()
    
    def execute_update(self, sql_query: str) -> Optional[Dict[str, Any]]:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            conn.commit()
            
            affected_rows = cur.rowcount
            cur.close()
            
            return {
                'success': True,
                'affected_rows': affected_rows
            }
        except Exception as e:
            conn.rollback()
            print(f"Update error: {e}")
            return None
        finally:
            conn.close()
    
    def test_connection(self) -> bool:
        """Test if connection to Snowflake is successful"""
        try:
            conn = self.get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT CURRENT_VERSION()")
                version = cur.fetchone()
                cur.close()
                conn.close()
                print(f"Connected to Snowflake! Version: {version[0]}")
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
        return False


# Create global instance
db = SnowflakeDB()

# Convenience functions
def get_connection():
    """Get a Snowflake connection"""
    return db.get_connection()

def query(sql: str):
    """Execute a SELECT query"""
    return db.execute_query(sql)

def update(sql: str):
    """Execute an INSERT/UPDATE/DELETE query"""
    return db.execute_update(sql)

def test_db():
    """Test database connection"""
    return db.test_connection()
