"""
Search strategies for LinkedIn prospect discovery.

Implements different search patterns and strategies for finding
prospects based on job titles, locations, and companies.
"""

import asyncio
import random
import re
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import Page, Locator

from ..utils.logger import get_logger

logger = get_logger(__name__)


class SearchStrategies:
    """Collection of search strategies for LinkedIn prospect discovery."""
    
    def __init__(self, page: Page, config: Dict[str, Any]):
        self.page = page
        self.config = config
        self.search_strategies = config.get('search_strategies', {})
    
    async def search_by_job_title_and_location(self, job_title: str, location: str) -> List[Dict[str, str]]:
        """Search for profiles using job title and location filters."""
        if not self.search_strategies.get('job_title_search', {}).get('enabled', True):
            return []
        
        logger.info(f"Searching for {job_title} in {location}")
        
        try:
            # Pre-search human behavior simulation
            await self._simulate_human_behavior("before_search")
            
            # Navigate to LinkedIn search with retry logic
            search_url = self._build_job_title_search_url(job_title, location)
            await self._navigate_with_retry(search_url)
            
            # Validate search results loaded
            if not await self._validate_search_results():
                logger.warning(f"Search results not loaded properly for {job_title} in {location}")
                return []
            
            # Extract profiles from search results
            profiles = await self._extract_profiles_from_search_results()
            
            logger.info(f"Found {len(profiles)} profiles for {job_title} in {location}")
            return profiles
            
        except Exception as e:
            logger.error(f"Job title search failed for {job_title} in {location}: {e}")
            return []
    
    async def search_by_keyword_and_location(self, keyword: str, location: str) -> List[Dict[str, str]]:
        """Search for profiles using keyword and location filters."""
        if not self.search_strategies.get('keyword_search', {}).get('enabled', True):
            return []
        
        logger.info(f"Searching for keyword '{keyword}' in {location}")
        
        try:
            # Pre-search human behavior simulation
            await self._simulate_human_behavior("before_search")
            
            # Navigate to LinkedIn search with retry logic
            search_url = self._build_keyword_search_url(keyword, location)
            await self._navigate_with_retry(search_url)
            
            # Validate search results loaded
            if not await self._validate_search_results():
                logger.warning(f"Search results not loaded properly for keyword '{keyword}' in {location}")
                return []
            
            # Extract profiles from search results
            profiles = await self._extract_profiles_from_search_results()
            
            logger.info(f"Found {len(profiles)} profiles for keyword '{keyword}' in {location}")
            return profiles
            
        except Exception as e:
            logger.error(f"Keyword search failed for '{keyword}' in {location}: {e}")
            return []
    
    async def search_by_company_and_job_title(self, company: str, job_title: str) -> List[Dict[str, str]]:
        """Search for profiles using company and job title filters."""
        if not self.search_strategies.get('company_search', {}).get('enabled', True):
            return []
        
        logger.info(f"Searching for {job_title} at {company}")
        
        try:
            # Pre-search human behavior simulation
            await self._simulate_human_behavior("before_search")
            
            # Navigate to LinkedIn search with retry logic
            search_url = self._build_company_search_url(company, job_title)
            await self._navigate_with_retry(search_url)
            
            # Validate search results loaded
            if not await self._validate_search_results():
                logger.warning(f"Search results not loaded properly for {job_title} at {company}")
                return []
            
            # Extract profiles from search results
            profiles = await self._extract_profiles_from_search_results()
            
            logger.info(f"Found {len(profiles)} profiles for {job_title} at {company}")
            return profiles
            
        except Exception as e:
            logger.error(f"Company search failed for {job_title} at {company}: {e}")
            return []
    
    def _build_job_title_search_url(self, job_title: str, location: str) -> str:
        """Build LinkedIn search URL for job title and location."""
        # URL encode the search parameters
        encoded_title = job_title.replace(' ', '%20').replace('&', '%26')
        encoded_location = location.replace(' ', '%20')
        
        return (
            f"https://www.linkedin.com/search/results/people/"
            f"?keywords={encoded_title}&location={encoded_location}"
            f"&origin=GLOBAL_SEARCH_HEADER&sid=Z%2Cv"
        )
    
    def _build_keyword_search_url(self, keyword: str, location: str) -> str:
        """Build LinkedIn search URL for keyword and location."""
        # URL encode the search parameters
        encoded_keyword = keyword.replace(' ', '%20').replace('&', '%26')
        encoded_location = location.replace(' ', '%20')
        
        return (
            f"https://www.linkedin.com/search/results/people/"
            f"?keywords={encoded_keyword}&location={encoded_location}"
            f"&origin=GLOBAL_SEARCH_HEADER&sid=Z%2Cv"
        )
    
    def _build_company_search_url(self, company: str, job_title: str) -> str:
        """Build LinkedIn search URL for company and job title."""
        # URL encode the search parameters
        encoded_company = company.replace(' ', '%20').replace('&', '%26')
        encoded_title = job_title.replace(' ', '%20').replace('&', '%26')
        
        return (
            f"https://www.linkedin.com/search/results/people/"
            f"?company={encoded_company}&keywords={encoded_title}"
            f"&origin=GLOBAL_SEARCH_HEADER&sid=Z%2Cv"
        )
    
    async def _extract_profiles_from_search_results(self) -> List[Dict[str, str]]:
        """Extract profile information from LinkedIn search results."""
        profiles = []
        
        try:
            # Wait for search results to load
            await self.page.wait_for_selector('ul.reusable-search__entity-result-list', timeout=10000)
            
            # Find all profile result items
            profile_items = await self.page.locator('li.reusable-search__result-container').all()
            
            for item in profile_items:
                try:
                    profile_data = await self._extract_profile_data_from_item(item)
                    if profile_data:
                        profiles.append(profile_data)
                except Exception as e:
                    logger.debug(f"Failed to extract profile data from item: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to extract profiles from search results: {e}")
        
        return profiles
    
    async def _extract_profile_data_from_item(self, item: Locator) -> Optional[Dict[str, str]]:
        """Extract profile data from a single search result item."""
        try:
            # Extract profile URL
            profile_link =  item.locator('a[href*="/in/"]').first
            if not profile_link:
                return None
            
            profile_url = await profile_link.get_attribute('href')
            if not profile_url or '/in/' not in profile_url:
                return None
            
            # Extract name
            name_element = item.locator('span[aria-hidden="true"]').first
            name = await name_element.inner_text() if await name_element.is_visible() else ""
            
            # Extract job title
            job_title_element = item.locator('.entity-result__primary-subtitle').first
            job_title = await job_title_element.inner_text() if await job_title_element.is_visible() else ""
            
            # Extract location
            location_element = item.locator('.entity-result__secondary-subtitle').first
            location = await location_element.inner_text() if await location_element.is_visible() else ""
            
            # Extract current company (if available)
            company_element = item.locator('.entity-result__summary .t-14').nth(1)
            company = await company_element.inner_text() if await company_element.is_visible() else ""
            
            # Validate profile
            if self._validate_profile_data(name, job_title, location):
                return {
                    'linkedin_url': profile_url,
                    'name': name.strip(),
                    'job_title': job_title.strip(),
                    'location': location.strip(),
                    'company': company.strip(),
                    'search_source': 'linkedin_search'
                }
            
        except Exception as e:
            logger.debug(f"Failed to extract profile data: {e}")
        
        return None
    
    def _validate_profile_data(self, name: str, job_title: str, location: str) -> bool:
        """Validate that profile data meets minimum requirements."""
        # Check if we have essential information
        if not name or len(name.strip()) < 2:
            return False
        
        if not job_title or len(job_title.strip()) < 3:
            return False
        
        if not location or len(location.strip()) < 2:
            return False
        
        # Check if job title contains relevant keywords
        relevant_keywords = ['hiring', 'talent', 'recruit', 'hr', 'people', 'human resources']
        job_title_lower = job_title.lower()
        has_relevant_keyword = any(keyword in job_title_lower for keyword in relevant_keywords)
        
        return has_relevant_keyword
    
    async def _simulate_human_behavior(self, action: str = "scroll"):
        """Simulate human-like behavior to avoid detection."""
        if action == "scroll":
            # Simulate realistic scrolling with mouse movement
            await self._simulate_mouse_movement()
            scroll_amount = random.randint(200, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(1, 3))
            
        elif action == "typing":
            # Simulate human typing speed with pauses
            typing_delay = random.uniform(0.05, 0.2)
            await asyncio.sleep(typing_delay)
            
        elif action == "before_search":
            # Pre-search human behavior simulation
            await self._simulate_mouse_movement()
            await self._simulate_page_interaction()
            await asyncio.sleep(random.uniform(2, 5))
            
        else:
            # General human-like delays
            delay = random.uniform(3, 8)  # Increased delays
            await asyncio.sleep(delay)
    
    async def _simulate_mouse_movement(self):
        """Simulate realistic mouse movements."""
        try:
            # Get viewport dimensions
            viewport = self.page.viewport_size
            if viewport:
                width = viewport.get('width', 1920)
                height = viewport.get('height', 1080)
            else:
                width = 1920
                height = 1080
            
            # Make multiple small mouse movements
            for _ in range(random.randint(3, 7)):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                
                # Move mouse to random position
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                # Small jitter movements
                for _ in range(random.randint(2, 4)):
                    jitter_x = x + random.randint(-20, 20)
                    jitter_y = y + random.randint(-20, 20)
                    await self.page.mouse.move(jitter_x, jitter_y)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
        except:
            pass
    
    async def _simulate_page_interaction(self):
        """Simulate page interaction before search."""
        try:
            # Click on random elements to simulate browsing
            clickable_elements = await self.page.locator('a, button, input, textarea').all()
            if clickable_elements:
                # Randomly click on a few elements
                for _ in range(random.randint(1, 3)):
                    element = random.choice(clickable_elements)
                    try:
                        if await element.is_visible():
                            await element.click(delay=random.uniform(50, 200))
                            await asyncio.sleep(random.uniform(0.5, 2))
                    except:
                        continue
        except:
            pass
    
    async def apply_search_filters(self):
        """Apply LinkedIn search filters based on configuration."""
        try:
            # Wait for filters to load
            await self.page.wait_for_selector('button[aria-label="All filters"]', timeout=5000)
            
            # Click on filters button
            filters_button = self.page.locator('button[aria-label="All filters"]').first
            await filters_button.click()
            await asyncio.sleep(1)
            
            # Apply connection level filter
            connection_filter = self.config.get('search_filters', {}).get('connection_level')
            if connection_filter:
                await self._apply_connection_filter(connection_filter)
            
            # Apply profile language filter
            language_filter = self.config.get('search_filters', {}).get('profile_language', [])
            if language_filter:
                await self._apply_language_filter(language_filter)
            
            # Apply current company filter
            current_company_filter = self.config.get('search_filters', {}).get('current_company')
            if current_company_filter:
                await self._apply_current_company_filter()
            
            # Apply profile completeness filter
            completeness_filter = self.config.get('search_filters', {}).get('profile_completeness')
            if completeness_filter:
                await self._apply_profile_completeness_filter(completeness_filter)
            
            # Apply filters
            apply_button = self.page.locator('button:has-text("Show results")').first
            if await apply_button.is_visible():
                await apply_button.click()
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"Failed to apply search filters: {e}")
    
    async def _apply_connection_filter(self, connection_level: str):
        """Apply connection level filter."""
        try:
            connection_selector = f'input[aria-label="{connection_level}"]'
            connection_checkbox = self.page.locator(connection_selector).first
            if await connection_checkbox.is_visible():
                await connection_checkbox.check()
        except:
            pass
    
    async def _apply_language_filter(self, languages: List[str]):
        """Apply profile language filter."""
        try:
            for language in languages:
                language_selector = f'input[aria-label="{language}"]'
                language_checkbox = self.page.locator(language_selector).first
                if await language_checkbox.is_visible():
                    await language_checkbox.check()
        except:
            pass
    
    async def _apply_current_company_filter(self):
        """Apply current company filter."""
        try:
            current_company_selector = 'input[aria-label="Current company"]'
            current_company_checkbox = self.page.locator(current_company_selector).first
            if await current_company_checkbox.is_visible():
                await current_company_checkbox.check()
        except:
            pass
    
    async def _apply_profile_completeness_filter(self, completeness: str):
        """Apply profile completeness filter."""
        try:
            completeness_selector = f'input[aria-label="{completeness}"]'
            completeness_checkbox = self.page.locator(completeness_selector).first
            if await completeness_checkbox.is_visible():
                await completeness_checkbox.check()
        except:
            pass
    
    async def _navigate_with_retry(self, url: str, max_retries: int = 3):
        """Navigate to URL with retry logic to handle temporary blocks."""
        for attempt in range(max_retries):
            try:
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # Additional wait for page to stabilize
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Navigation failed after {max_retries} attempts: {e}")
                    raise
                else:
                    logger.warning(f"Navigation attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(random.uniform(5, 10))  # Wait before retry
    
    async def _validate_search_results(self) -> bool:
        """Validate that search results actually loaded and are not blocked."""
        try:
            # Check for common LinkedIn search result indicators
            search_indicators = [
                'ul.reusable-search__entity-result-list',
                'li.reusable-search__result-container',
                'button[aria-label="All filters"]',
                '.search-results-container'
            ]
            
            for indicator in search_indicators:
                try:
                    element = self.page.locator(indicator).first
                    if await element.is_visible(timeout=5000):
                        return True
                except:
                    continue
            
            # Check for error indicators (blocked, captcha, etc.)
            error_indicators = [
                'h1:has-text("Oops")',
                'h1:has-text("Error")',
                'h1:has-text("Captcha")',
                'h1:has-text("Access denied")',
                'h1:has-text("Please verify you are a human")'
            ]
            
            for error_indicator in error_indicators:
                try:
                    element = self.page.locator(error_indicator).first
                    if await element.is_visible(timeout=2000):
                        logger.warning(f"Search blocked by LinkedIn: {error_indicator}")
                        return False
                except:
                    continue
            
            # Check page title for LinkedIn
            page_title = await self.page.title()
            if "LinkedIn" not in page_title:
                logger.warning(f"Page title doesn't contain LinkedIn: {page_title}")
                return False
            
            return False  # No valid indicators found
            
        except Exception as e:
            logger.error(f"Search validation failed: {e}")
            return False
