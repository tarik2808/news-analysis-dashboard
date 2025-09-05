#!/usr/bin/env python3
"""
Weekly Newsletter Scheduler
Automatically generates weekly snapshots and sends newsletter emails every Sunday
"""

import requests
import logging
from datetime import datetime
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_newsletter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def send_weekly_newsletter():
    """Generate weekly snapshot and send newsletter to all subscribers"""
    base_url = "http://localhost:8000"
    
    try:
        # Step 1: Generate weekly snapshot
        logging.info("Generating weekly snapshot...")
        response = requests.post(f"{base_url}/snapshots/generate_weekly")
        
        if response.status_code == 200:
            logging.info("Weekly snapshot generated successfully")
        else:
            logging.error(f"Failed to generate weekly snapshot: {response.status_code}")
            return False
        
        # Step 2: Send weekly newsletter
        logging.info("Sending weekly newsletter...")
        response = requests.post(f"{base_url}/newsletter/send_weekly")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Weekly newsletter sent: {result.get('message', 'Success')}")
            return True
        else:
            logging.error(f"Failed to send weekly newsletter: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logging.error("Cannot connect to the backend server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("Starting weekly newsletter scheduler...")
    success = send_weekly_newsletter()
    
    if success:
        logging.info("Weekly newsletter process completed successfully")
        sys.exit(0)
    else:
        logging.error("Weekly newsletter process failed")
        sys.exit(1) 