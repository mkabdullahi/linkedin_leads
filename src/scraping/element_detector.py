"""
Element detection system for LinkedIn Automation.

Handles AI-powered element detection with multiple fallback strategies to handle
LinkedIn's dynamic DOM and random class names.
"""

import asyncio
import json
import random
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from playwright.async_api import Page, Locator
from rich.console import Console

from ..utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class ElementDetector:
    """Advanced element detection with multiple fallback strategies."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selectors_config = self._load_selectors_config()
    
    def _load_selectors_config(self) -> Dict[str, Any]:
        """Load selectors configuration from JSON file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "selectors_config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Selectors config not found at {config_path}, using defaults")
            return self._get_default_selectors()
    
    def _get_default_selectors(self) -> Dict[str, Any]:
        """Get default selectors if config file is missing."""
        return {
            "primary_selectors": {
                "connect_button": [
                    "button:has-text(\"Connect\")",
                    "button[data-test-id=\"connect-button\"]",
                    "button[aria-label*=\"Connect\"]"
                ],
                "message_input": [
                    "textarea[placeholder*=\"Add a note\"]",
                    "textarea[aria-label*=\"message\"]",
                    "input[role=\"textbox\"]"
                ],
                "send_button": [
                    "button:has-text(\"Send\")",
                    "button[data-test-id=\"send-button\"]",
                    "button[aria-label*=\"Send\"]"
                ]
            },
            "xpath_selectors": {
                "connect_button": [
                    "//button[contains(text(), \"Connect\")]",
                    "//button[contains(@data-control-name, \"connect\")]"
                ],
                "message_input": [
                    "//textarea[contains(@placeholder, \"Add a note\")]",
                    "//input[@role=\"textbox\"]"
                ],
                "send_button": [
                    "//button[contains(text(), \"Send\")]"
                ]
            },
            "retry_config": {
                "max_retries": 3,
                "base_delay": 1000,
                "backoff_factor": 2
            }
        }
    
    async def find_connect_button(self) -> Optional[Locator]:
        """Find the Connect button using multiple detection strategies."""
        strategies = [
            self._find_by_text,
            self._find_by_attributes,
            self._find_by_xpath,
            self._find_by_visual_pattern
        ]
        
        for strategy in strategies:
            try:
                button = await strategy('Connect')
                if button and await button.is_visible():
                    logger.info("Found Connect button using strategy: " + strategy.__name__)
                    return button
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        logger.warning("Could not find Connect button with any strategy")
        return None
    
    async def find_message_input(self) -> Optional[Locator]:
        """Find the message input field using multiple detection strategies."""
        strategies = [
            self._find_by_placeholder,
            self._find_by_attributes,
            self._find_by_xpath,
            self._find_by_contenteditable
        ]
        
        for strategy in strategies:
            try:
                input_field = await strategy('message')
                if input_field and await input_field.is_visible():
                    logger.info("Found message input using strategy: " + strategy.__name__)
                    return input_field
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        logger.warning("Could not find message input field")
        return None
    
    async def find_send_button(self) -> Optional[Locator]:
        """Find the Send button using multiple detection strategies."""
        strategies = [
            self._find_by_text,
            self._find_by_attributes,
            self._find_by_xpath
        ]
        
        for strategy in strategies:
            try:
                button = await strategy('Send')
                if button and await button.is_visible():
                    logger.info("Found Send button using strategy: " + strategy.__name__)
                    return button
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        logger.warning("Could not find Send button")
        return None
    
    async def _find_by_text(self, text: str) -> Optional[Locator]:
        """Find element by visible text content."""
        selectors = [
            f'button:has-text("{text}")',
            f'a:has-text("{text}")',
            f'span:has-text("{text}")',
            f'div:has-text("{text}")'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    return element
            except:
                continue
        
        return None
    
    async def _find_by_attributes(self, text: str) -> Optional[Locator]:
        """Find element by data attributes."""
        attribute_selectors = {
            'Connect': [
                'button[data-test-id="connect-button"]',
                'button[aria-label*="Connect"]',
                'button[data-control-name*="connect"]',
                'button[data-action="connect"]'
            ],
            'Send': [
                'button[data-test-id="send-button"]',
                'button[aria-label*="Send"]',
                'button[data-action="send"]'
            ],
            'message': [
                'textarea[aria-label*="message"]',
                'input[aria-label*="message"]',
                'div[role="textbox"]'
            ]
        }
        
        selectors = attribute_selectors.get(text, [])
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    return element
            except:
                continue
        
        return None
    
    async def _find_by_xpath(self, text: str) -> Optional[Locator]:
        """Find element using XPath expressions."""
        xpath_selectors = {
            'Connect': [
                f'//button[contains(text(), "{text}")]',
                f'//button[contains(@data-control-name, "{text.lower()}")]',
                f'//button[contains(@aria-label, "{text}")]'
            ],
            'Send': [
                f'//button[contains(text(), "{text}")]',
                f'//button[contains(@data-test-id, "{text.lower()}")]',
                f'//button[contains(@aria-label, "{text}")]'
            ],
            'message': [
                '//textarea[contains(@placeholder, "Add a note")]',
                '//input[@role="textbox"]',
                '//div[@contenteditable="true"]'
            ]
        }
        
        selectors = xpath_selectors.get(text, [])
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    return element
            except:
                continue
        
        return None
    
    async def _find_by_placeholder(self, text: str) -> Optional[Locator]:
        """Find input field by placeholder text."""
        selectors = [
            'textarea[placeholder*="Add a note"]',
            'textarea[placeholder*="message"]',
            'input[placeholder*="message"]',
            'input[placeholder*="note"]'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    return element
            except:
                continue
        
        return None
    
    async def _find_by_contenteditable(self, text: str) -> Optional[Locator]:
        """Find contenteditable elements."""
        selectors = [
            'div[contenteditable="true"]',
            'div[contenteditable="plaintext-only"]',
            '[contenteditable="true"]'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    # Verify it's actually a text input
                    await element.click()
                    await self.page.keyboard.type("test", delay=100)
                    await self.page.keyboard.press("Backspace")
                    return element
            except:
                continue
        
        return None
    
    async def _find_by_visual_pattern(self, text: str) -> Optional[Locator]:
        """Find elements using visual pattern matching (fallback)."""
        # Look for elements near other known elements
        if text == 'Connect':
            # Look for buttons near profile header
            try:
                profile_header =  self.page.locator('h1, h2').first
                if await profile_header.is_visible():
                    # Look for buttons in the same container
                    container = await profile_header.evaluate('el => el.closest("div, section")')
                    if container:
                        buttons = await self.page.locator('button').all()
                        for button in buttons:
                            button_text = await button.inner_text()
                            if 'Connect' in button_text:
                                return button
            except:
                pass
        
        return None
    
    async def wait_for_element_with_retry(self, locator: Locator, timeout: int = 10000) -> bool:
        """Wait for element with retry logic and exponential backoff."""
        retry_config = self.selectors_config.get('retry_config', {})
        max_retries = retry_config.get('max_retries', 3)
        base_delay = retry_config.get('base_delay', 1000)
        backoff_factor = retry_config.get('backoff_factor', 2)
        
        for attempt in range(max_retries):
            try:
                await locator.wait_for(timeout=timeout)
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Element not found after {max_retries} attempts: {e}")
                    return False
                
                delay = base_delay * (backoff_factor ** attempt)
                await asyncio.sleep(delay / 1000)
                continue
        
        return False
    
    async def detect_page_type(self) -> str:
        """Detect what type of LinkedIn page we're on."""
        try:
            # Check for profile page indicators
            profile_indicators = [
                'h1[data-test-id="profile-name"]',
                'h2[data-test-id="profile-name"]',
                '[data-test-id="profile-name"]',
                'button:has-text("Connect")'
            ]
            
            for indicator in profile_indicators:
                if await self.page.locator(indicator).is_visible(timeout=1000):
                    return "profile"
            
            # Check for feed page indicators
            feed_indicators = [
                '[data-test-id="feed"]',
                '[data-test-id="feed-content"]',
                'button:has-text("Post")'
            ]
            
            for indicator in feed_indicators:
                if await self.page.locator(indicator).is_visible(timeout=1000):
                    return "feed"
            
            # Check for search results
            search_indicators = [
                '[data-test-id="search-results"]',
                '[data-test-id="search-filters"]',
                'input[placeholder*="Search"]'
            ]
            
            for indicator in search_indicators:
                if await self.page.locator(indicator).is_visible(timeout=1000):
                    return "search"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Failed to detect page type: {e}")
            return "unknown"