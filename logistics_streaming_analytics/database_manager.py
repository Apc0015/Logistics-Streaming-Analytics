import psycopg2
import pandas as pd
import streamlit as st
import logging

class DatabaseManager:
    """Database connection and query management for Azure PostgreSQL"""
    
    def __init__(self):
        self.db_config = {
            "host": "bigdata15.postgres.database.azure.com",
            "database": "postgres",
            "user": "Apc",
            "password": "Azure@@0099",
            "port": "5432",
            "sslmode": "require"
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_connection(self):
        """Create connection to Azure PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def test_connection(self):
        """Test database connection"""
        try:
            conn = self.create_connection()
            if conn:
                conn.close()
                return True
            return False
        except:
            return False
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute SQL query with optional parameters"""
        try:
            conn = self.create_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
            else:
                result = True
                
            conn.commit()
            cursor.close()
            conn.close()
            
            return result
            
        except psycopg2.Error as e:
            self.logger.error(f"Query execution failed: {e}")
            return None
    
    def get_data_as_df(self, query, params=None):
        """Execute query and return results as pandas DataFrame"""
        try:
            conn = self.create_connection()
            if not conn:
                return pd.DataFrame()
                
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"Error creating DataFrame: {e}")
            return pd.DataFrame()
    
    def get_table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """
            result = self.execute_query(query, (table_name,), fetch=True)
            return result[0][0] if result else False
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False
    
    def get_table_count(self, table_name):
        """Get record count for a table"""
        if not self.get_table_exists(table_name):
            return 0
        
        query = f"SELECT COUNT(*) FROM {table_name}"
        try:
            result = self.execute_query(query, fetch=True)
            return result[0][0] if result else 0
        except:
            return 0