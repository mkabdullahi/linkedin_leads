"""
Prospect discovery system for LinkedIn Automation.

Automatically discovers and validates prospects based on job titles,
locations, and company filters. Integrates with existing workflow.
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from playwright.async_api import Page
from rich.console import Console

from .search_strategies import SearchStrategies
from ..utils.data_model import DataModel
from ..utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class ProspectDiscoverer:
    """Main prospect discovery engine."""
    
    def __init__(self, page: Page):
        self.page = page
        self.data_model = DataModel()
        self.search_config = self._load_search_config()
        self.search_strategies = SearchStrategies(page, self.search_config)
        self.discovered_prospects: List[Dict[str, str]] = []
        self.duplicates_found = 0
        self.validation_errors = 0
    
    def _load_search_config(self) -> Dict[str, Any]:
        """Load search configuration from JSON file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "search_config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Search config not found at {config_path}")
            return self._get_default_search_config()
    
    def _get_default_search_config(self) -> Dict[str, Any]:
        """Get default search configuration."""
        return {
            "locations": ["United States", "Germany", "United Kingdom", "Belgium"],
            "job_titles": ["Hiring Manager", "Talent Acquisition", "Recruiter"],
            "search_filters": {
                "connection_level": "1st",
                "profile_language": ["English"],
                "current_company": True
            },
            "rate_limiting": {
                "delay_between_searches": 30,
                "delay_between_profiles": 5,
                "max_searches_per_session": 5
            }
        }
    
    async def discover_prospects(self, max_prospects: int = 50) -> List[Dict[str, str]]:
        """Discover prospects based on search configuration."""
        logger.info("🚀 Starting prospect discovery...")
        
        # Load existing prospects to avoid duplicates
        existing_prospects = await self.data_model.load_prospects()
        existing_urls = {p.get('linkedin_url', '') for p in existing_prospects}
        
        # Get search parameters
        locations = self.search_config.get('locations', [])
        job_titles = self.search_config.get('job_titles', [])
        companies = self.search_config.get('companies', [])
        
        rate_limits = self.search_config.get('rate_limiting', {})
        max_searches = rate_limits.get('max_searches_per_session', 10)
        delay_between_searches = rate_limits.get('delay_between_searches', 30)
        
        search_count = 0
        
        # Strategy 1: Job title + Location searches
        for location in locations:
            if search_count >= max_searches or len(self.discovered_prospects) >= max_prospects:
                break
                
            for job_title in job_titles:
                if search_count >= max_searches or len(self.discovered_prospects) >= max_prospects:
                    break
                
                logger.info(f"🔍 Searching for {job_title} in {location}")
                
                # Perform search
                profiles = await self.search_strategies.search_by_job_title_and_location(
                    job_title, location
                )
                
                # Process and validate profiles
                for profile in profiles:
                    if len(self.discovered_prospects) >= max_prospects:
                        break
                    
                    if await self._process_profile(profile, existing_urls):
                        self.discovered_prospects.append(profile)
                
                search_count += 1
                
                # Rate limiting - Use 3-10 minute delays to avoid LinkedIn detection
                if search_count < max_searches:
                    delay = random.uniform(180, 600)  # 3-10 minutes (180-600 seconds)
                    logger.info(f"⏳ Waiting {delay:.1f} seconds before next search...")
                    await asyncio.sleep(delay)
        
        # Strategy 2: Company + Job title searches (for top companies)
        if len(self.discovered_prospects) < max_prospects:
            for company in companies[:5]:  # Limit to top 5 companies
                if search_count >= max_searches or len(self.discovered_prospects) >= max_prospects:
                    break
                
                for job_title in job_titles[:3]:  # Limit to top 3 job titles
                    if search_count >= max_searches or len(self.discovered_prospects) >= max_prospects:
                        break
                    
                    logger.info(f"🏢 Searching for {job_title} at {company}")
                    
                    # Perform company search
                    profiles = await self.search_strategies.search_by_company_and_job_title(
                        company, job_title
                    )
                    
                    # Process and validate profiles
                    for profile in profiles:
                        if len(self.discovered_prospects) >= max_prospects:
                            break
                        
                        if await self._process_profile(profile, existing_urls):
                            self.discovered_prospects.append(profile)
                    
                    search_count += 1
                    
                    # Rate limiting - Use 3-10 minute delays to avoid LinkedIn detection
                    if search_count < max_searches:
                        delay = random.uniform(180, 600)  # 3-10 minutes (180-600 seconds)
                        logger.info(f"⏳ Waiting {delay:.1f} seconds before next search...")
                        await asyncio.sleep(delay)
        
        # Final validation and deduplication
        self.discovered_prospects = self._final_validation_and_deduplication(
            self.discovered_prospects
        )
        
        logger.info(f"✅ Prospect discovery completed: {len(self.discovered_prospects)} prospects found")
        logger.info(f"📊 Duplicates found: {self.duplicates_found}")
        logger.info(f"⚠️  Validation errors: {self.validation_errors}")
        
        return self.discovered_prospects
    
    async def _process_profile(self, profile: Dict[str, str], existing_urls: Set[str]) -> bool:
        """Process and validate a single profile."""
        try:
            # Check for duplicates
            if profile.get('linkedin_url') in existing_urls:
                self.duplicates_found += 1
                logger.debug(f"Duplicate profile found: {profile.get('linkedin_url')}")
                return False
            
            # Validate profile
            if not self._validate_profile(profile):
                self.validation_errors += 1
                logger.debug(f"Profile validation failed: {profile.get('linkedin_url')}")
                return False
            
            # Additional validation by visiting profile
            if not await self._validate_profile_by_visit(profile):
                self.validation_errors += 1
                logger.debug(f"Profile visit validation failed: {profile.get('linkedin_url')}")
                return False
            
            logger.info(f"✅ Validated profile: {profile.get('name')} - {profile.get('job_title')}")
            return True
            
        except Exception as e:
            logger.debug(f"Profile processing failed: {e}")
            return False
    
    def _validate_profile(self, profile: Dict[str, str]) -> bool:
        """Basic profile validation."""
        required_fields = ['linkedin_url', 'name', 'job_title', 'location']
        
        for field in required_fields:
            if not profile.get(field) or len(str(profile[field]).strip()) < 2:
                return False
        
        # Check if URL is valid LinkedIn profile
        url = profile.get('linkedin_url', '')
        if '/in/' not in url or not url.startswith('http'):
            return False
        
        # Check if job title contains relevant keywords
        job_title = profile.get('job_title', '').lower()
        relevant_keywords = ['hiring', 'talent', 'recruit', 'hr', 'people', 'human resources']
        has_relevant_keyword = any(keyword in job_title for keyword in relevant_keywords)
        
        return has_relevant_keyword
    
    async def _validate_profile_by_visit(self, profile: Dict[str, str]) -> bool:
        """Validate profile by visiting the actual LinkedIn page."""
        try:
            # Navigate to profile
            await self.page.goto(profile['linkedin_url'], wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Check if profile is valid (not blocked, not private)
            page_title = await self.page.title()
            if "LinkedIn" not in page_title:
                return False
            
            # Check for profile elements
            profile_indicators = [
                'h1[data-test-id="profile-name"]',
                'h2[data-test-id="profile-name"]',
                'button:has-text("Connect")',
                '.pv-top-card--list'
            ]
            
            has_profile_content = False
            for indicator in profile_indicators:
                try:
                    element = self.page.locator(indicator).first
                    if await element.is_visible(timeout=2000):
                        has_profile_content = True
                        break
                except:
                    continue
            
            if not has_profile_content:
                logger.debug(f"Profile appears to be private or blocked: {profile['linkedin_url']}")
                return False
            
            # Simulate human behavior
            await self._simulate_human_behavior("scroll")
            
            return True
            
        except Exception as e:
            logger.debug(f"Profile visit validation failed for {profile.get('linkedin_url')}: {e}")
            return False
    
    def _final_validation_and_deduplication(self, prospects: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Final validation and deduplication of prospects."""
        seen_urls = set()
        valid_prospects = []
        
        for prospect in prospects:
            url = prospect.get('linkedin_url', '')
            if url in seen_urls:
                continue
            
            seen_urls.add(url)
            
            # Final validation
            if self._validate_profile(prospect):
                valid_prospects.append(prospect)
        
        return valid_prospects
    
    async def save_prospects(self, prospects: List[Dict[str, str]]):
        """Save discovered prospects to data model."""
        try:
            # Load existing prospects
            existing_prospects = await self.data_model.load_prospects()
            
            # Combine and deduplicate
            all_prospects = existing_prospects + prospects
            seen_urls = set()
            unique_prospects = []
            
            for prospect in all_prospects:
                url = prospect.get('linkedin_url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_prospects.append(prospect)
            
            # Save to prospects.json
            prospects_file = self.data_model.data_dir / "prospects.json"
            with open(prospects_file, 'w') as f:
                json.dump(unique_prospects, f, indent=2)
            
            logger.info(f"💾 Saved {len(unique_prospects)} prospects to {prospects_file}")
            
        except Exception as e:
            logger.error(f"Failed to save prospects: {e}")
    
    async def _simulate_human_behavior(self, action: str = "scroll"):
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
    
    async def run_discovery_workflow(self, max_prospects: int = 50):
        """Run complete discovery workflow."""
        start_time = time.time()
        
        try:
            # Discover prospects
            prospects = await self.discover_prospects(max_prospects)
            
            # Save prospects
            await self.save_prospects(prospects)
            
            # Generate summary
            execution_time = time.time() - start_time
            summary = {
                'discovery_time': execution_time,
                'prospects_found': len(prospects),
                'duplicates_found': self.duplicates_found,
                'validation_errors': self.validation_errors,
                'timestamp': time.time()
            }
            
            logger.info("🎉 Prospect discovery workflow completed successfully!")
            logger.info(f"📊 Summary: {len(prospects)} prospects, {execution_time:.1f}s execution")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Prospect discovery workflow failed: {e}")
            return None