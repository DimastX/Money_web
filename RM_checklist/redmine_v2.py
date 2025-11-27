import requests
import logging
import os
from dotenv import load_dotenv
import time
from redmine_service import RedmineService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

REDMINE_URL = os.getenv('REDMINE_URL', 'https://redmine.starline.ru').rstrip('/')
API_KEY = os.getenv('REDMINE_API_KEY')

class RedmineSorterV2(RedmineService):
    def sort_checklists_v2(self, issue_id):
        """
        Strategy: Find the item with the largest ID (last created) and move it to the last position.
        """
        
        items = self.get_issue_checklists(issue_id)
        if not items:
            return "No items found."
            
        sorted_items = self._sort_logic(items)
        if not sorted_items:
             return "No items to sort."

        # Get the item that should be LAST (largest ID)
        last_item = sorted_items[-1]
        total_count = len(items)
        
        logger.info(f"--- Single Move Strategy ---")
        logger.info(f"Target Item (Largest ID): {last_item['id']} ({last_item.get('subject')[:30]}...)")
        logger.info(f"Target Position: {total_count}")
        
        if self._move_to_position_v2(last_item['id'], total_count):
             return f"Moved Item {last_item['id']} to Position {total_count} successfully."
        else:
             return f"Failed to move Item {last_item['id']}."

    def _move_to_position_v2(self, item_id, position):
        # Logic exactly from single_move_test.py which worked
        url = f"{self.url}/checklists/{item_id}.json"
        payload = {
            "checklist": {
                "position": position
            }
        }
        try:
            response = requests.put(url, json=payload, headers=self.headers)
            if response.status_code in [200, 204]:
                return True
            else:
                logger.error(f"Failed to move {item_id}. Status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Exception moving {item_id}: {e}")
            return False

if __name__ == "__main__":
    # Allow direct running for testing
    issue_id = input("Enter Issue ID: ")
    if issue_id:
        sorter = RedmineSorterV2(REDMINE_URL, API_KEY)
        print(sorter.sort_checklists_v2(issue_id))

