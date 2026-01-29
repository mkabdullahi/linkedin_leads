import json
import os
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LinkedInSessionManager:
    def __init__(self, cookies_path: Optional[str] = None):
        if cookies_path is None:
            # Calculate path from project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # Up 3 levels
            cookies_path = str(project_root / "config" / "linkedin_cookies.json")
        
        self.cookies_path = Path(cookies_path)
        self.cookies = None
    
    async def load_cookies_from_json(self):
        """Load cookies exported from Cookie-Editor extension"""
        logger.info(f"🔍 Attempting to load cookies from: {self.cookies_path.absolute()}")
        
        if not self.cookies_path.exists():
            raise FileNotFoundError(
                f"Cookie file not found: {self.cookies_path.absolute()}\n"
                f"Please export cookies from Cookie-Editor extension as JSON to: {self.cookies_path.absolute()}"
            )
        
        with open(self.cookies_path, 'r') as f:
            raw_cookies = json.load(f)
        
        logger.info(f"📋 Loaded {len(raw_cookies)} raw cookies from {self.cookies_path}")
        
        # Convert to Playwright format
        self.cookies = self._convert_cookie_format(raw_cookies)
        logger.info(f"✅ Converted {len(self.cookies)} valid LinkedIn cookies")
        return self.cookies
    
    def _convert_cookie_format(self, cookie_array: list) -> list:
        """Convert Cookie-Editor format to Playwright format"""
        converted = []
        
        for cookie in cookie_array:
            cookie_name = cookie.get('name')
            cookie_value = cookie.get('value', '')
            
            if not cookie_name or not cookie_value:
                logger.debug(f"Skipping cookie with missing name or value")
                continue
            
            try:
                # Build cookie with proper Playwright format
                # Playwright requires either url OR domain, not both
                converted_cookie = {
                    "name": cookie_name,
                    "value": cookie_value,
                }
                
                # Add domain if present in original cookie (preferred for LinkedIn)
                if 'domain' in cookie and cookie['domain']:
                    converted_cookie['domain'] = cookie['domain']
                # Only add url if no domain is present
                elif 'url' not in converted_cookie:
                    converted_cookie['url'] = "https://www.linkedin.com"
                
                # Preserve other cookie properties
                if 'path' in cookie:
                    converted_cookie['path'] = cookie['path']
                if 'secure' in cookie:
                    converted_cookie['secure'] = cookie['secure']
                if 'httpOnly' in cookie:
                    converted_cookie['httpOnly'] = cookie['httpOnly']
                if 'sameSite' in cookie:
                    converted_cookie['sameSite'] = cookie['sameSite']
                
                converted.append(converted_cookie)
                logger.debug(f"Converted cookie: {cookie_name}")
            except Exception as e:
                logger.warning(f"Failed to convert cookie {cookie_name}: {e}")
                continue
    
        logger.info(f"Successfully converted {len(converted)} cookies")
        return converted
    
    async def apply_cookies_to_context(self, context):
        """Apply loaded cookies to browser context"""
        if not self.cookies:
            await self.load_cookies_from_json()
        
        if not self.cookies:
            raise Exception("No cookies loaded - cannot apply to context")
        # Validate and clean cookies before applying
        valid_cookies = []
        for cookie in self.cookies:
            try:
                # Ensure required fields exist
                if 'name' not in cookie or 'value' not in cookie:
                    logger.warning(f"Skipping invalid cookie: missing name or value")
                    continue
                
                # Ensure either url or domain exists
                if 'url' not in cookie and 'domain' not in cookie:
                    logger.warning(f"Skipping cookie {cookie.get('name')}: missing url or domain")
                    continue
                
                valid_cookies.append(cookie)
            except Exception as e:
                logger.warning(f"Skipping malformed cookie: {e}")
                continue
        
        if not valid_cookies:
            raise Exception("No valid cookies to apply")
        
        logger.info(f"Applying {len(valid_cookies)} valid cookies to context")
        await context.add_cookies(valid_cookies)
        logger.info(f"Successfully applied cookies to browser context")