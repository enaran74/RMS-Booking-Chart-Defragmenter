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

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


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
                
                # Get record count
                try:
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    record_count = count_result.scalar()
                except Exception as count_error:
                    logger.warning(f"Error counting records in {table_name}: {count_error}")
                    record_count = 0
                
                # Get sample records (first 5)
                sample_records = []
                if record_count > 0:
                    try:
                        sample_result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
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
        # Validate table name to prevent SQL injection
        table_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = :table_name
        """)
        table_result = db.execute(table_query, {"table_name": table_name})
        if not table_result.fetchone():
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found"
            )
        
        # Get total record count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
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
            
        query = text(f"SELECT * FROM {table_name} {order_clause} LIMIT :limit OFFSET :offset")
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
