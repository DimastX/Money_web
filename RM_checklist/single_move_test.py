import requests
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

REDMINE_URL = os.getenv('REDMINE_URL', 'https://redmine.starline.ru').rstrip('/')
API_KEY = os.getenv('REDMINE_API_KEY')

def move_item_test(item_id, new_position):
    headers = {
        'X-Redmine-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    url = f"{REDMINE_URL}/checklists/{item_id}.json"
    
    # Payload strictly as per documentation
    payload = {
        "checklist": {
            "position": new_position
        }
    }
    
    logger.info(f"Attempting to move Item {item_id} to Position {new_position}")
    logger.info(f"URL: {url}")
    logger.info(f"Payload: {payload}")
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        if response.status_code in [200, 204]:
            logger.info("Success!")
        else:
            logger.error("Failed!")
            
    except Exception as e:
        logger.error(f"Exception: {e}")

if __name__ == "__main__":
    # User requested to move item 158767 to position 48
    move_item_test(158767, 48)

