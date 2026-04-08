import os
import sys
import logging
from dotenv import load_dotenv
from scheduler.tasks import start_scheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logging.info("Starting scheduler...")
    start_scheduler()
    
    # Держим процесс живым
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped")