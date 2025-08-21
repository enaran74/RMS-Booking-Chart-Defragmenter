#!/usr/bin/env python3
"""
Setup endpoints for administrative functions
Admin-only access to system configuration and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import logging
import re

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_table_name(table_name: str) -> bool:
    """
    Validate table name to prevent SQL injection.
    
    Security measures:
    - Only alphanumeric characters and underscores allowed
    - Must start with letter or underscore (SQL identifier rules)
    - Maximum length of 64 characters (PostgreSQL identifier limit)
    - Prevents special characters that could be used for injection
    
    Args:
        table_name: The table name to validate
        
    Returns:
        bool: True if table name is safe, False otherwise
    """
    # Strict regex pattern for SQL identifiers - prevents injection attacks
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$'
    return bool(re.match(pattern, table_name))


def get_valid_table_names(db: Session) -> List[str]:
    """Get list of valid table names from database to validate against."""
    try:
        table_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        table_result = db.execute(table_query)
        return [row[0] for row in table_result]
    except Exception as e:
        logger.error(f"Error getting table names: {e}")
        return []


def secure_table_operation(db: Session, table_name: str, operation: str) -> str:
    """
    Securely validate table name and return quoted identifier for SQL operations.
    
    This function provides multi-layer security against SQL injection:
    1. Regex validation (validate_table_name)
    2. Database whitelist validation (table must exist)
    3. Quoted identifier output (prevents injection in SQL construction)
    
    The returned quoted identifier is safe for use in SQL queries because:
    - Input is validated against strict regex pattern
    - Table existence is verified against database schema
    - Double quotes prevent any SQL injection attempts
    
    Args:
        db: Database session for validation
        table_name: Table name to validate and secure
        operation: Operation type (for logging)
        
    Returns:
        str: Quoted table identifier safe for SQL use
        
    Raises:
        HTTPException: If table name is invalid or doesn't exist
    """
    # Layer 1: Regex pattern validation
    if not validate_table_name(table_name):
        logger.warning(f"Invalid table name format attempted: {table_name}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name format: {table_name}"
        )
    
    # Layer 2: Database whitelist validation
    valid_tables = get_valid_table_names(db)
    if table_name not in valid_tables:
        logger.warning(f"Access attempted to non-existent table: {table_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Table '{table_name}' not found"
        )
    
    # Layer 3: Return quoted identifier to prevent injection
    # Double quotes make this safe for SQL construction
    return f'"{table_name}"'


@router.get("/database/tables")
async def get_database_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get database table information (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access database information"
        )
    
    try:
        logger.info("Starting database tables inspection")
        
        # Get table names using a simple query instead of inspector
        try:
            # Query to get all table names from PostgreSQL information_schema
            table_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            table_result = db.execute(table_query)
            table_names = [row[0] for row in table_result]
            logger.info(f"Found {len(table_names)} tables: {table_names}")
        except Exception as table_error:
            logger.error(f"Error getting table names: {table_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get table names: {str(table_error)}"
            )
        
        tables_info = []
        
        for table_name in table_names:
            try:
                # Validate table name for security
                if not validate_table_name(table_name):
                    logger.warning(f"Skipping invalid table name: {table_name}")
                    continue
                
                # Get column information using information_schema
                try:
                    column_query = text("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = :table_name
                        ORDER BY ordinal_position
                    """)
                    column_result = db.execute(column_query, {"table_name": table_name})
                    columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in column_result]
                    column_names = [col['name'] for col in columns]
                except Exception as col_error:
                    logger.warning(f"Error getting columns for {table_name}: {col_error}")
                    column_names = []
                    columns = []
                
                # Get record count using secure table identifier
                try:
                    secure_table = f'"{table_name}"'  # Quoted identifier for security
                    # nosec B608: table_name is validated by validate_table_name() regex and whitelist
                    count_query = text(f"SELECT COUNT(*) FROM {secure_table}")  # nosec B608
                    count_result = db.execute(count_query)
                    record_count = count_result.scalar()
                except Exception as count_error:
                    logger.warning(f"Error counting records in {table_name}: {count_error}")
                    record_count = 0
                
                # Get sample records (first 5)
                sample_records = []
                if record_count > 0:
                    try:
                        secure_table = f'"{table_name}"'  # Quoted identifier for security
                        # nosec B608: table_name is validated by validate_table_name() regex and whitelist
                        sample_query = text(f"SELECT * FROM {secure_table} LIMIT 5")  # nosec B608
                        sample_result = db.execute(sample_query)
                        # Convert to list of dicts more safely
                        sample_records = []
                        for row in sample_result:
                            try:
                                # Handle different row types
                                if hasattr(row, '_mapping'):
                                    sample_records.append(dict(row._mapping))
                                elif hasattr(row, '_asdict'):
                                    sample_records.append(row._asdict())
                                else:
                                    # Fallback for tuple-like rows
                                    sample_records.append(dict(zip(column_names, row)))
                            except Exception as row_error:
                                logger.warning(f"Error processing row from {table_name}: {row_error}")
                                continue
                    except Exception as sample_error:
                        logger.warning(f"Error getting sample records from {table_name}: {sample_error}")
                
                tables_info.append({
                    "name": table_name,
                    "columns": column_names,
                    "column_details": columns,
                    "record_count": record_count,
                    "sample_records": sample_records
                })
                
            except Exception as e:
                logger.warning(f"Error getting info for table {table_name}: {e}")
                # Add basic info even if we can't get details
                tables_info.append({
                    "name": table_name,
                    "columns": [],
                    "column_details": [],
                    "record_count": 0,
                    "sample_records": [],
                    "error": str(e)
                })
        
        logger.info(f"Successfully processed {len(tables_info)} tables")
        return tables_info
        
    except Exception as e:
        logger.error(f"Error getting database tables: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database information: {str(e)}"
        )


@router.get("/database/table/{table_name}/records")
async def get_table_records(
    table_name: str,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated records for a specific table (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access database information"
        )
    
    try:
        # Validate and secure table name to prevent SQL injection
        secure_table = secure_table_operation(db, table_name, "query")
        
        # Get total record count
        # nosec B608: secure_table is validated by secure_table_operation() with regex and whitelist
        count_query = text(f"SELECT COUNT(*) FROM {secure_table}")  # nosec B608
        count_result = db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get column information
        column_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position
        """)
        column_result = db.execute(column_query, {"table_name": table_name})
        columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in column_result]
        column_names = [col['name'] for col in columns]
        
        # Get paginated records (newest first, assuming 'id' or 'created_at' column exists)
        # Try to order by 'created_at' first, then 'id' as fallback
        try:
            # Check if created_at column exists
            created_at_exists = any(col['name'] == 'created_at' for col in columns)
            if created_at_exists:
                order_clause = "ORDER BY created_at DESC"
            else:
                order_clause = "ORDER BY id DESC"
        except:
            order_clause = "ORDER BY id DESC"
        
        # Safety limit
        if limit > 1000:
            limit = 1000
        if offset < 0:
            offset = 0
            
        # nosec B608: secure_table is validated by secure_table_operation() with regex and whitelist
        query = text(f"SELECT * FROM {secure_table} {order_clause} LIMIT :limit OFFSET :offset")  # nosec B608
        result = db.execute(query, {"limit": limit, "offset": offset})
        
        # Convert to list of dicts safely
        records = []
        for row in result:
            try:
                if hasattr(row, '_mapping'):
                    records.append(dict(row._mapping))
                elif hasattr(row, '_asdict'):
                    records.append(row._asdict())
                else:
                    records.append(dict(zip(column_names, row)))
            except Exception as row_error:
                logger.warning(f"Error processing row from {table_name}: {row_error}")
                continue
        
        return {
            "table_name": table_name,
            "columns": column_names,
            "records": records,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting table records for {table_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get table records: {str(e)}"
        )
