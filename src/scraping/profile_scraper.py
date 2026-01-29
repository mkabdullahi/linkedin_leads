"""
Profile scraping system for LinkedIn Automation.

Handles multi-strategy profile data extraction with context-aware detection
to handle LinkedIn's dynamic DOM and random class names.
"""

import asyncio
import re
import time
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass
from playwright.async_api import Page, Locator

from .element_detector import ElementDetector
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileData:
    """Data structure for extracted profile information."""
    name: str = ""
    job_title: str = ""
    company: str = ""
    industry: str = ""
    location: str = ""
    summary: str = ""
    skills: List[str] = None
    education: List[str] = None
    experience: List[Dict[str, str]] = None
    recent_posts: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.education is None:
            self.education = []
        if self.experience is None:
            self.experience = []
        if self.recent_posts is None:
            self.recent_posts = []


class ProfileScraper:
    """Advanced profile scraper with multiple extraction strategies."""
    
    def __init__(self, page: Page):
        self.page = page
        self.detector = ElementDetector(page)
        self.profile_data = ProfileData()
    
    async def extract_profile_data(self, profile_url: str) -> ProfileData:
        """Extract comprehensive profile data from LinkedIn profile."""
        logger.info(f"Starting profile data extraction for: {profile_url}")
        
        try:
            # Navigate to profile
            await self.page.goto(profile_url, wait_until="networkidle")
            await self.detector.simulate_human_behavior(self.page, "scroll")
            
            # Extract data using multiple strategies
            await self._extract_basic_info()
            await self._extract_professional_info()
            await self._extract_additional_info()
            
            logger.info("Profile data extraction completed successfully")
            return self.profile_data
            
        except Exception as e:
            logger.error(f"Failed to extract profile data: {e}")
            return self.profile_data
    
    async def _extract_basic_info(self):
        """Extract basic profile information (name, job title, company)."""
        # Extract name with multiple strategies
        name_selectors = [
            'h1[data-test-id="profile-name"]',
            'h2[data-test-id="profile-name"]',
            '[data-test-id="profile-name"]',
            'h1 span',
            'h2 span',
            'h1',
            'h2'
        ]
        
        for selector in name_selectors:
            try:
                name_element = self.page.locator(selector).first
                if await name_element.is_visible():
                    name = await name_element.inner_text()
                    if name and len(name.strip()) > 1:
                        self.profile_data.name = name.strip()
                        logger.info(f"Extracted name: {self.profile_data.name}")
                        break
            except Exception as e:
                logger.debug(f"Name extraction failed for selector {selector}: {e}")
                continue
        
        # Extract job title and company with context awareness
        job_selectors = [
            '[data-test-id="job-title"]',
            '[data-field="job-title"]',
            '[data-test-id="headline"]',
            'h2:has-text(" at ")',
            'h3:has-text(" at ")',
            'span:has-text(" at ")',
            'div:has-text(" at ")'
        ]
        
        for selector in job_selectors:
            try:
                job_element = self.page.locator(selector).first
                if await job_element.is_visible():
                    job_text = await job_element.inner_text()
                    if job_text and ' at ' in job_text:
                        # Parse job title and company
                        parts = job_text.split(' at ', 1)
                        if len(parts) == 2:
                            self.profile_data.job_title = parts[0].strip()
                            self.profile_data.company = parts[1].strip()
                            logger.info(f"Extracted job: {self.profile_data.job_title} at {self.profile_data.company}")
                            break
            except Exception as e:
                logger.debug(f"Job extraction failed for selector {selector}: {e}")
                continue
        
        # Extract location
        location_selectors = [
            '[data-test-id="location"]',
            '[data-field="location"]',
            'span:has-text(",")',
            'div:has-text(",")'
        ]
        
        for selector in location_selectors:
            try:
                location_element = self.page.locator(selector).first
                if await location_element.is_visible():
                    location = await location_element.inner_text()
                    if location and ',' in location:
                        self.profile_data.location = location.strip()
                        logger.info(f"Extracted location: {self.profile_data.location}")
                        break
            except Exception as e:
                logger.debug(f"Location extraction failed for selector {selector}: {e}")
                continue
    
    async def _extract_professional_info(self):
        """Extract professional information (summary, skills, experience)."""
        # Extract summary
        summary_selectors = [
            '[data-test-id="summary"]',
            '[data-field="summary"]',
            'section:has-text("About")',
            'div:has-text("About")'
        ]
        
        for selector in summary_selectors:
            try:
                summary_element = self.page.locator(selector).first
                if await summary_element.is_visible():
                    summary = await summary_element.inner_text()
                    if summary and len(summary) > 50:
                        self.profile_data.summary = summary.strip()
                        logger.info("Extracted summary")
                        break
            except Exception as e:
                logger.debug(f"Summary extraction failed for selector {selector}: {e}")
                continue
        
        # Extract skills
        skills_selectors = [
            '[data-test-id="skills"]',
            '[data-field="skills"]',
            'section:has-text("Skills")',
            'div:has-text("Skills")'
        ]
        
        for selector in skills_selectors:
            try:
                skills_section = self.page.locator(selector).first
                if await skills_section.is_visible():
                    # Look for skill items within the section
                    skill_items = await skills_section.locator('span, div, li').all()
                    for item in skill_items:
                        try:
                            skill_text = await item.inner_text()
                            if skill_text and len(skill_text) > 2 and skill_text not in self.profile_data.skills:
                                self.profile_data.skills.append(skill_text.strip())
                        except:
                            continue
                    
                    if self.profile_data.skills:
                        logger.info(f"Extracted {len(self.profile_data.skills)} skills")
                        break
            except Exception as e:
                logger.debug(f"Skills extraction failed for selector {selector}: {e}")
                continue
        
        # Extract experience
        experience_selectors = [
            '[data-test-id="experience"]',
            '[data-field="experience"]',
            'section:has-text("Experience")',
            'div:has-text("Experience")'
        ]
        
        for selector in experience_selectors:
            try:
                experience_section = self.page.locator(selector).first
                if await experience_section.is_visible():
                    # Look for experience items
                    exp_items = await experience_section.locator('li, div[data-test-id="experience-item"]').all()
                    for item in exp_items[:3]:  # Limit to top 3 experiences
                        try:
                            exp_text = await item.inner_text()
                            if exp_text and len(exp_text) > 20:
                                # Parse experience into structured format
                                exp_data = self._parse_experience(exp_text)
                                if exp_data:
                                    self.profile_data.experience.append(exp_data)
                        except:
                            continue
                    
                    if self.profile_data.experience:
                        logger.info(f"Extracted {len(self.profile_data.experience)} experiences")
                        break
            except Exception as e:
                logger.debug(f"Experience extraction failed for selector {selector}: {e}")
                continue
    
    async def _extract_additional_info(self):
        """Extract additional profile information."""
        # Extract education
        education_selectors = [
            '[data-test-id="education"]',
            '[data-field="education"]',
            'section:has-text("Education")',
            'div:has-text("Education")'
        ]
        
        for selector in education_selectors:
            try:
                education_section = self.page.locator(selector).first
                if await education_section.is_visible():
                    edu_items = await education_section.locator('li, div[data-test-id="education-item"]').all()
                    for item in edu_items[:2]:  # Limit to top 2 educations
                        try:
                            edu_text = await item.inner_text()
                            if edu_text and len(edu_text) > 10:
                                self.profile_data.education.append(edu_text.strip())
                        except:
                            continue
                    
                    if self.profile_data.education:
                        logger.info(f"Extracted {len(self.profile_data.education)} educations")
                        break
            except Exception as e:
                logger.debug(f"Education extraction failed for selector {selector}: {e}")
                continue
        
        # Extract recent posts/articles (if available)
        try:
            # Look for recent activity
            post_selectors = [
                '[data-test-id="post"]',
                '[data-field="post"]',
                'article:has-text("•")',
                'div:has-text("•")'
            ]
            
            for selector in post_selectors:
                try:
                    posts = await self.page.locator(selector).all()
                    for post in posts[:3]:  # Limit to top 3 posts
                        try:
                            post_text = await post.inner_text()
                            if post_text and len(post_text) > 30:
                                self.profile_data.recent_posts.append(post_text.strip())
                        except:
                            continue
                    
                    if self.profile_data.recent_posts:
                        logger.info(f"Extracted {len(self.profile_data.recent_posts)} recent posts")
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Recent posts extraction failed: {e}")
    
    def _parse_experience(self, exp_text: str) -> Optional[Dict[str, str]]:
        """Parse experience text into structured format."""
        try:
            # Simple parsing - look for common patterns
            lines = exp_text.split('\n')
            if len(lines) >= 2:
                title = lines[0].strip()
                company = lines[1].strip()
                
                # Clean up common patterns
                title = re.sub(r'\s*\d{1,2}\s*[a-zA-Z]{3}\s*-\s*\d{1,2}\s*[a-zA-Z]{3}\s*\d{4}', '', title)
                company = re.sub(r'\s*\d{1,2}\s*[a-zA-Z]{3}\s*-\s*\d{1,2}\s*[a-zA-Z]{3}\s*\d{4}', '', company)
                
                if title and company:
                    return {
                        'title': title,
                        'company': company,
                        'description': exp_text[:200]  # Truncate long descriptions
                    }
        except:
            pass
        
        return None
    
    async def validate_profile_data(self) -> bool:
        """Validate that we have sufficient profile data for personalization."""
        required_fields = ['name', 'job_title', 'company']
        missing_fields = [field for field in required_fields if not getattr(self.profile_data, field)]
        
        if missing_fields:
            logger.warning(f"Missing required profile fields: {missing_fields}")
            return False
        
        # Check if we have enough context for personalization
        context_score = 0
        if self.profile_data.summary:
            context_score += 2
        if self.profile_data.skills:
            context_score += 1
        if self.profile_data.experience:
            context_score += 2
        if self.profile_data.education:
            context_score += 1
        if self.profile_data.recent_posts:
            context_score += 2
        
        if context_score >= 3:
            logger.info(f"Profile data validation passed with score: {context_score}")
            return True
        else:
            logger.warning(f"Profile data validation failed with score: {context_score}")
            return False
    
    async def get_profile_context(self) -> Dict[str, Any]:
        """Get structured context for AI message generation."""
        return {
            'name': self.profile_data.name,
            'job_title': self.profile_data.job_title,
            'company': self.profile_data.company,
            'industry': self.profile_data.industry,
            'location': self.profile_data.location,
            'summary': self.profile_data.summary[:500] if self.profile_data.summary else "",
            'skills': self.profile_data.skills[:5],  # Limit to top 5 skills
            'experience': self.profile_data.experience[:2],  # Limit to top 2 experiences
            'education': self.profile_data.education[:2],  # Limit to top 2 educations
            'recent_posts': self.profile_data.recent_posts[:2]  # Limit to top 2 posts
        }