#!/usr/bin/env python3
"""
Simplified Utility Functions for Web App RMS Integration
Provides minimal compatibility layer for RMS client components
"""

import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance compatible with RMS components"""
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # Ensure the logger has at least basic configuration
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Prevent duplicate propagation
    logger.propagate = False
    
    # Add custom methods that the RMS components expect (only if not already attached)
    if not hasattr(logger, 'log_email_operation'):
        def log_function_entry(func_name, **kwargs):
            logger.debug(f"Entering {func_name} with args: {kwargs}")
        
        def log_function_exit(func_name, result=None):
            logger.debug(f"Exiting {func_name} with result: {result}")
        
        def log_performance_metric(operation, duration, context=""):
            logger.info(f"Performance: {operation} took {duration:.2f}s {context}")
        
        def log_data_summary(data_type, count, context=""):
            logger.info(f"Data: {data_type} count: {count} {context}")
        
        def log_api_call(endpoint, method, status_code, content_length):
            logger.debug(f"API: {method} {endpoint} -> {status_code} ({content_length} bytes)")
        
        def log_error_with_context(error, context=""):
            logger.error(f"Error in {context}: {error}")
        
        def log_property_analysis_start(property_code, property_id, property_name):
            logger.info(f"Starting analysis for {property_name} (Code: {property_code}, ID: {property_id})")
        
        def log_move_analysis(category_name, move_count, context=""):
            logger.info(f"Move analysis: {category_name} - {move_count} moves {context}")
        
        def log_excel_generation(filename, move_count, context=""):
            logger.info(f"Excel generation: {filename} with {move_count} moves {context}")
        
        def log_property_analysis_complete(property_name, move_count, duration):
            logger.info(f"Completed analysis for {property_name}: {move_count} moves in {duration:.2f}s")
        
        def log_email_operation(operation, recipient, success):
            status = "✅ Sent" if success else "❌ Failed"
            logger.info(f"Email {operation}: {status} to {recipient}")
        
        # Attach custom methods to logger
        logger.log_function_entry = log_function_entry
        logger.log_function_exit = log_function_exit
        logger.log_performance_metric = log_performance_metric
        logger.log_data_summary = log_data_summary
        logger.log_api_call = log_api_call
        logger.log_error_with_context = log_error_with_context
        logger.log_property_analysis_start = log_property_analysis_start
        logger.log_move_analysis = log_move_analysis
        logger.log_excel_generation = log_excel_generation
        logger.log_property_analysis_complete = log_property_analysis_complete
        logger.log_email_operation = log_email_operation
    
    return logger

def setup_logging():
    """Setup basic logging configuration"""
    # Only configure basic logging if it hasn't been configured yet
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    return get_logger()