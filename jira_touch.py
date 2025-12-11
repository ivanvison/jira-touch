"""
Jira Touch - Bulk Issue Reindexing Tool

Forces reindexing of Jira issues by logging minimal work time on each issue.
Useful after migrations when issues aren't visible in the new Jira instance.

Author: Ivan V.
License: MIT
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

# ============================================
# CONFIGURATION (from environment variables)
# ============================================
JIRA_BASE_URL = os.getenv('JIRA_BASE_URL')
USERNAME = os.getenv('JIRA_USERNAME')
PASSWORD = os.getenv('JIRA_PASSWORD')
KEYS_FILE = os.getenv('KEYS_FILE', 'keys.txt')


def validate_config():
    """Validate that all required environment variables are set"""
    missing = []
    if not JIRA_BASE_URL:
        missing.append('JIRA_BASE_URL')
    if not USERNAME:
        missing.append('JIRA_USERNAME')
    if not PASSWORD:
        missing.append('JIRA_PASSWORD')
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Create a .env file with your configuration. See .env.example for reference.")
        return False
    return True


def load_keys_from_file(filename):
    """Load keys from a text file (one key per line, ignoring comments and empty lines)"""
    try:
        with open(filename, 'r') as f:
            keys = [
                line.strip() for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        return keys
    except FileNotFoundError:
        print(f"❌ File '{filename}' not found!")
        return []


def save_keys_to_file(filename, keys):
    """Save keys to a text file (one key per line)"""
    with open(filename, 'w') as f:
        for key in keys:
            f.write(f"{key}\n")


def format_duration(seconds):
    """Format seconds into hours, minutes, seconds"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def touch_jira_issues():
    """Main function to touch all Jira issues listed in the keys file"""
    
    # Validate configuration
    if not validate_config():
        return
    
    # Load keys from file
    keys = load_keys_from_file(KEYS_FILE)
    
    if not keys:
        print(f"❌ No keys to process! Make sure '{KEYS_FILE}' exists and has keys.")
        return

    print(f"📋 Loaded {len(keys)} keys from {KEYS_FILE}")

    with sync_playwright() as p:
        print(f"🚀 Opening browser...")
        
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        page = context.new_page()

        try:
            # ============================================
            # STEP 1: LOGIN
            # ============================================
            print(f"\n📋 Logging in to Jira...")
            page.goto(f"{JIRA_BASE_URL}/browse/{keys[0]}", wait_until='domcontentloaded', timeout=30000)
            
            page.get_by_test_id("username").click()
            page.get_by_test_id("username").fill(USERNAME)
            page.get_by_test_id("login-submit-idf-testid").click()
            
            page.get_by_test_id("password").wait_for(state="visible", timeout=10000)
            page.get_by_test_id("password").fill(PASSWORD)
            page.get_by_test_id("login-submit-idf-testid").click()
            
            # ============================================
            # STEP 2: VERIFICATION CODE (manual entry)
            # ============================================
            print(f"\n🔐 Verification code required!")
            
            verification_field = page.get_by_label("-digit verification code")
            verification_field.wait_for(state="visible", timeout=30000)
            
            verification_code = input("   Enter your 6-digit verification code: ").strip()
            
            verification_field.fill(verification_code)
            
            print(f"   ⏳ Waiting for login to complete...")
            time.sleep(5)
            
            page.goto(f"{JIRA_BASE_URL}/browse/{keys[0]}", wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)
            
            # ============================================
            # STEP 3: PROCESS ALL KEYS IN SAME SESSION
            # ============================================
            print(f"\n✅ Logged in! Starting to process {len(keys)} issues...\n")
            successful = 0
            failed = 0
            failed_keys = []
            
            # Start timer
            start_time = datetime.now()

            for i, key in enumerate(keys, 1):
                try:
                    print(f'[{i}/{len(keys)}] {key}...', end=' ', flush=True)
                    
                    # Navigate to the issue
                    page.goto(f'{JIRA_BASE_URL}/browse/{key}', wait_until='domcontentloaded', timeout=30000)
                    
                    # Click the meatball menu with persistent retry
                    meatball_menu = page.get_by_test_id("issue-meatball-menu.ui.dropdown-trigger.button")
                    log_work_item = page.get_by_role("menuitem", name="Log work")
                    
                    # Keep clicking until the menu opens (max 10 attempts)
                    max_attempts = 10
                    for attempt in range(1, max_attempts + 1):
                        meatball_menu.wait_for(state="visible", timeout=30000)
                        meatball_menu.click()
                        time.sleep(1.5)
                        
                        if log_work_item.is_visible():
                            break
                        else:
                            # Press Escape to close any partial menu state
                            page.keyboard.press("Escape")
                            time.sleep(0.5)
                    else:
                        raise Exception(f"Menu didn't open after {max_attempts} attempts")
                    
                    # Click "Log work" menu item
                    log_work_item.click()
                    time.sleep(0.5)
                    
                    # Fill in time spent (1 minute)
                    time_input = page.get_by_test_id("timelog-textfield-Time spent")
                    time_input.wait_for(state="visible", timeout=10000)
                    time_input.fill("1m")
                    time.sleep(0.3)
                    
                    # Click save button
                    save_btn = page.get_by_test_id("issue.common.component.log-time-modal.modal.footer.save-button")
                    save_btn.wait_for(state="visible", timeout=10000)
                    save_btn.click()
                    time.sleep(1)
                    
                    print(f'✓')
                    successful += 1
                    
                except Exception as e:
                    print(f'✗ ({str(e)[:50]})')
                    failed += 1
                    failed_keys.append(key)
                    continue

            # End timer
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            # ============================================
            # SUMMARY
            # ============================================
            print(f'\n{"="*50}')
            print(f'✅ DONE!')
            print(f'   Total time: {format_duration(elapsed)}')
            print(f'   Successful: {successful}/{len(keys)}')
            if failed > 0:
                print(f'   Failed: {failed}/{len(keys)}')
                print(f'\n❌ FAILED KEYS:')
                for fk in failed_keys:
                    print(f'   - {fk}')
                # Save failed keys back to the file (so you can re-run for just those)
                save_keys_to_file(KEYS_FILE, failed_keys)
                print(f'\n💾 Failed keys saved to {KEYS_FILE} (re-run to retry)')
            else:
                # All successful - clear the file
                save_keys_to_file(KEYS_FILE, [])
                print(f'\n💾 All keys processed! {KEYS_FILE} is now empty.')
            print(f'{"="*50}')
            
            print(f'\n💡 Browser will close in 5 seconds...')
            time.sleep(5)

        except Exception as e:
            print(f'\n❌ Fatal error: {str(e)}')
            raise
        finally:
            print('\n🔒 Closing browser...')
            browser.close()


if __name__ == '__main__':
    touch_jira_issues()
