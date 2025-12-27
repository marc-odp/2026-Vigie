import logging
import os
from datetime import datetime

# Setup logging directory
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure Audit Logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# File handler
log_file = os.path.join(LOG_DIR, "audit.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)

audit_logger.addHandler(file_handler)

def log_action(user_name: str, action: str, details: str):
    """
    Log an action to the audit file.
    """
    msg = f"USER: {user_name} | ACTION: {action} | DETAILS: {details}"
    audit_logger.info(msg)
