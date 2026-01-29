"""
Connection Manager for LinkedIn Automation.

Handles automated connection requests with retry mechanisms, human-like behavior,
and comprehensive error handling.
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from playwright.async_api import Page, Locator

from ..scraping.profile_scraper import ProfileScraper
from ..ai.message_generator import MessageGenerator
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages automated LinkedIn connection requests."""
    
    def __init__(self, page: Page, message_generator: MessageGenerator):
        self.page = page
        self.message_generator = message_generator
        self.profile_scraper = ProfileScraper(page)
        self.detector = None  # Will be set when needed
        
    async def send_connection_request(self, profile_url: str, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a connection request to a LinkedIn profile."""
        result = {
            'success': False,
            'profile_url': profile_url,
            'message_sent': '',
            'error': '',
            'retry_count': 0,
            'time_taken': 0
        }
        
        start_time = time.time()
        
        try:
            # Navigate to profile
            await self.page.goto(profile_url, wait_until="networkidle")
            await self._simulate_human_behavior("scroll")
            
            # Extract profile data
            profile_data = await self.profile_scraper.extract_profile_data(profile_url)
            
            # Validate profile data
            if not await self.profile_scraper.validate_profile_data():
                result['error'] = "Insufficient profile data for personalization"
                return result
            
            # Generate personalized message
            profile_context = await self.profile_scraper.get_profile_context()
            generated_message = await self.message_generator.generate_personalized_message(profile_context)
            
            if generated_message.fallback_used:
                logger.warning(f"Used fallback message for {profile_url}")
            
            # Find and click Connect button
            connect_button = await self._find_connect_button()
            if not connect_button:
                result['error'] = "Could not find Connect button"
                return result
            
            await connect_button.click()
            await self._simulate_human_behavior("typing")
            
            # Handle connection modal (if it appears)
            message_sent = await self._handle_connection_modal(generated_message.message)
            
            if message_sent:
                result['success'] = True
                result['message_sent'] = generated_message.message
                result['time_taken'] = time.time() - start_time
                
                logger.info(f"Successfully sent connection request to {profile_url}")
            else:
                result['error'] = "Failed to send message in connection modal"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Failed to send connection request to {profile_url}: {e}")
        
        return result
    
    async def _find_connect_button(self) -> Optional[Locator]:
        """Find the Connect button using multiple strategies."""
        from ..scraping.element_detector import ElementDetector
        self.detector = ElementDetector(self.page)
        
        # Try multiple strategies with retry
        for attempt in range(3):
            try:
                connect_button = await self.detector.find_connect_button()
                if connect_button and await connect_button.is_visible():
                    return connect_button
            except Exception as e:
                logger.debug(f"Connect button detection attempt {attempt + 1} failed: {e}")
                
            # Wait before retry
            await asyncio.sleep(random.uniform(1, 3))
        
        return None
    
    async def _handle_connection_modal(self, message: str) -> bool:
        """Handle the connection request modal with message input."""
        try:
            # Wait for modal to appear
            await self.page.wait_for_selector('div[aria-label="Send now"]', timeout=5000)
            
            # Find message input field
            message_input = await self.detector.find_message_input()
            if not message_input:
                logger.warning("Could not find message input field")
                return False
            
            # Clear any existing text and type our message
            await message_input.click()
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Delete")
            
            # Type message with human-like delays
            for char in message:
                await message_input.type(char, delay=random.uniform(50, 150))
            
            # Find and click Send button
            send_button = await self.detector.find_send_button()
            if send_button:
                await send_button.click()
                await self._simulate_human_behavior("typing")
                return True
            
        except Exception as e:
            logger.error(f"Failed to handle connection modal: {e}")
        
        return False
    
    async def _simulate_human_behavior(self, action: str = "general"):
        """Simulate human-like behavior to avoid detection."""
        if action == "scroll":
            # Simulate realistic scrolling
            scroll_amount = random.randint(200, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(1, 3))
            
        elif action == "typing":
            # Simulate human typing speed
            typing_delay = random.uniform(0.05, 0.2)
            await asyncio.sleep(typing_delay)
            
        else:
            # General human-like delays
            delay = random.uniform(2, 5)
            await asyncio.sleep(delay)
    
    async def check_connection_status(self, profile_url: str) -> str:
        """Check the connection status for a profile."""
        try:
            await self.page.goto(profile_url, wait_until="networkidle")
            
            # Check for different connection status indicators
            status_selectors = {
                'connected': [
                    'button:has-text("Connected")',
                    'button[aria-label*="Connected"]',
                    'span:has-text("1st")'
                ],
                'pending': [
                    'button:has-text("Pending")',
                    'button[aria-label*="Pending"]',
                    'span:has-text("Pending")'
                ],
                'connect': [
                    'button:has-text("Connect")',
                    'button[aria-label*="Connect"]'
                ]
            }
            
            for status, selectors in status_selectors.items():
                for selector in selectors:
                    try:
                        element = self.page.locator(selector).first
                        if await element.is_visible(timeout=1000):
                            return status
                    except:
                        continue
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Failed to check connection status for {profile_url}: {e}")
            return "error"
    
    async def send_bulk_requests(self, prospects: List[Dict[str, Any]], max_requests: int = 9) -> List[Dict[str, Any]]:
        """Send connection requests to multiple prospects."""
        results = []
        successful_requests = 0
        
        for i, prospect in enumerate(prospects[:max_requests]):
            if successful_requests >= max_requests:
                break
            
            logger.info(f"Processing prospect {i+1}/{len(prospects)}: {prospect.get('linkedin_url', 'Unknown')}")
            
            # Add delay between requests
            if i > 0:
                delay = random.uniform(30, 120)  # 30 seconds to 2 minutes
                logger.info(f"Waiting {delay:.1f} seconds before next request...")
                await asyncio.sleep(delay)
            
            # Send connection request
            result = await self.send_connection_request(
                prospect['linkedin_url'], 
                prospect
            )
            
            results.append(result)
            
            if result['success']:
                successful_requests += 1
                logger.info(f"Successfully sent request {successful_requests}/{max_requests}")
            else:
                logger.warning(f"Failed to send request: {result['error']}")
        
        logger.info(f"Completed bulk requests: {successful_requests}/{len(prospects)} successful")
        return results
    
    async def handle_rate_limiting(self, error_message: str) -> bool:
        """Handle LinkedIn rate limiting and temporary blocks."""
        rate_limit_indicators = [
            "rate limit", "too many requests", "temporarily blocked", 
            "unusual activity", "verify your identity"
        ]
        
        if any(indicator in error_message.lower() for indicator in rate_limit_indicators):
            logger.warning(f"Rate limiting detected: {error_message}")
            
            # Wait for a longer period
            wait_time = random.randint(300, 900)  # 5-15 minutes
            logger.info(f"Waiting {wait_time} seconds due to rate limiting...")
            await asyncio.sleep(wait_time)
            
            return True
        
        return False
    
    async def refresh_session(self):
        """Refresh the browser session to avoid detection."""
        logger.info("Refreshing browser session...")
        await self.page.close()
        # Note: Session refresh would need to be handled at a higher level
        # since we can't create a new page from here