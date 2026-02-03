import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional
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
        logger.info(f"Attempting to load cookies from: {self.cookies_path.absolute()}")
        
        if not self.cookies_path.exists():
            raise FileNotFoundError(
                f"Cookie file not found: {self.cookies_path.absolute()}\n"
                f"Please export cookies from Cookie-Editor extension as JSON to: {self.cookies_path.absolute()}"
            )
        
        with open(self.cookies_path, 'r') as f:
            raw_cookies = json.load(f)
        
        logger.info(f"Loaded {len(raw_cookies)} raw cookies from {self.cookies_path}")
        
        # Convert to Playwright format
        self.cookies = self._convert_cookie_format(raw_cookies)
        logger.info(f"Converted {len(self.cookies)} valid LinkedIn cookies")
        return self.cookies
    
    async def verify_authentication(self, context) -> bool:
        """Verify that cookies provide valid LinkedIn authentication"""
        try:
            # Create a new page to test authentication
            page = await context.new_page()
            
            # Navigate to LinkedIn home page
            await page.goto("https://www.linkedin.com", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Check if we're authenticated by looking for logged-in indicators
            auth_indicators = [
                'a[href*="/messaging"]',  # Messaging link
                'a[href*="/profile"]',    # Profile link
                '.global-nav__me',        # Profile dropdown
                'button[aria-label="Home"]',  # Home button
                'img[alt*="profile"]',    # Profile picture
                '.global-nav__me-photo',  # Profile photo element
            ]
            
            is_authenticated = False
            for indicator in auth_indicators:
                try:
                    element = page.locator(indicator).first
                    if await element.is_visible(timeout=3000):
                        is_authenticated = True
                        break
                except:
                    continue
            
            # Also check for login indicators (signs we're NOT authenticated)
            login_indicators = [
                'input[name="session_key"]',  # Login form
                'input[name="session_password"]',  # Password field
                'button:has-text("Sign in")',  # Sign in button
                'button:has-text("Join now")',  # Join button (not logged in)
            ]
            
            has_login_form = False
            for indicator in login_indicators:
                try:
                    element = page.locator(indicator).first
                    if await element.is_visible(timeout=1000):
                        has_login_form = True
                        break
                except:
                    continue
            
            # Additional check: look for LinkedIn's authenticated state indicators
            try:
                # Check for presence of authenticated navigation elements
                nav_elements = await page.locator('.global-nav__primary-link').all()
                if nav_elements:
                    for nav_element in nav_elements:
                        nav_text = await nav_element.inner_text()
                        if 'messaging' in nav_text.lower() or 'network' in nav_text.lower():
                            is_authenticated = True
                            break
            except:
                pass
            
            # Check for CAPTCHA or security challenges
            try:
                captcha_indicators = [
                    'img[src*="captcha"]',
                    'div:has-text("CAPTCHA")',
                    'div:has-text("security check")',
                    'div:has-text("unusual activity")',
                    'input[name="captcha"]'
                ]
                
                has_captcha = False
                for indicator in captcha_indicators:
                    try:
                        element = page.locator(indicator).first
                        if await element.is_visible(timeout=1000):
                            has_captcha = True
                            break
                    except:
                        continue
            except:
                has_captcha = False
            
            # Take debug screenshot if authentication fails
            if not is_authenticated or has_login_form or has_captcha:
                try:
                    # Create debug_output directory if it doesn't exist
                    debug_dir = Path("debug_output")
                    debug_dir.mkdir(exist_ok=True)
                    
                    # Generate timestamp for unique filename
                    timestamp = int(asyncio.get_event_loop().time())
                    screenshot_path = debug_dir / f"auth_debug_{timestamp}.png"
                    
                    # Take screenshot
                    await page.screenshot(path=str(screenshot_path))
                    logger.info(f"Debug screenshot saved to {screenshot_path}")
                except Exception as e:
                    logger.warning(f"Failed to save debug screenshot: {e}")
            
            await page.close()
            
            if is_authenticated and not has_login_form and not has_captcha:
                logger.info("LinkedIn authentication verified successfully")
                return True
            else:
                # Check if cookies are expired
                if self.check_cookie_refresh_needed():
                    logger.warning("LinkedIn authentication failed - cookies are expired")
                else:
                    logger.warning("LinkedIn authentication failed - cookies are invalid")
                return False
                
        except Exception as e:
            logger.error(f"Authentication verification failed: {e}")
            return False
    
    def get_required_cookies(self) -> List[str]:
        """Get list of required cookies for LinkedIn authentication"""
        return ["li_at", "JSESSIONID", "bscookie"]
    
    def validate_required_cookies(self) -> bool:
        """Validate that all required cookies are present and valid"""
        if not self.cookies:
            logger.error("No cookies loaded - cannot validate")
            return False
        
        required_cookies = self.get_required_cookies()
        present_cookies = {cookie.get('name') for cookie in self.cookies}
        
        missing_cookies = [cookie for cookie in required_cookies if cookie not in present_cookies]
        
        if missing_cookies:
            logger.error(f"Missing required cookies: {missing_cookies}")
            return False
        
        # Validate cookie values are not empty
        for cookie in self.cookies:
            if cookie.get('name') in required_cookies and not cookie.get('value'):
                logger.error(f"Cookie {cookie.get('name')} has empty value")
                return False
        
        logger.info("All required cookies are present and valid")
        return True
    
    def check_cookie_refresh_needed(self) -> bool:
        """Check if cookies need to be refreshed based on expiration"""
        if not self.cookies:
            return True
        
        # Check for expired cookies
        current_time = asyncio.get_event_loop().time()
        expired_cookies = []
        
        for cookie in self.cookies:
            if 'expirationDate' in cookie:
                try:
                    if cookie['expirationDate'] < current_time:
                        expired_cookies.append(cookie['name'])
                except:
                    continue
        
        if expired_cookies:
            logger.warning(f"Expired cookies detected: {expired_cookies}")
            return True
        
        # Check if critical authentication cookies are present
        required_cookies = self.get_required_cookies()
        present_cookies = {cookie.get('name') for cookie in self.cookies}
        missing_cookies = [cookie for cookie in required_cookies if cookie not in present_cookies]
        
        if missing_cookies:
            logger.error(f"Missing required cookies: {missing_cookies}")
            return True
        
        return False
    
    def get_refresh_guidance(self) -> str:
        """Get guidance on how to refresh cookies"""
        return """
Cookie Refresh Required:

1. Open Chrome and navigate to https://www.linkedin.com
2. Log in to your LinkedIn account if not already logged in
3. Install the "Cookie-Editor" extension from Chrome Web Store
4. Click the Cookie-Editor icon in your browser toolbar
5. Click "Export" and select "JSON" format
6. Save the exported cookies to: {self.cookies_path.absolute()}
7. Restart the automation script

Important: Make sure you're logged into LinkedIn before exporting cookies.
        """.strip()
    
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
                
                # Standardize domain format for LinkedIn
                if 'domain' in cookie and cookie['domain']:
                    domain = cookie['domain']
                    logger.debug(f"Processing cookie {cookie_name} with domain: {domain}")
                    
                    # Normalize domain format
                    if domain.startswith('.'):
                        # Remove leading dot for Playwright compatibility
                        domain = domain[1:]
                        logger.debug(f"Removed leading dot, new domain: {domain}")
                    
                    # Ensure consistent domain format
                    if domain.startswith('www.'):
                        domain = domain[4:]  # Remove 'www.' prefix
                        logger.debug(f"Removed www prefix, new domain: {domain}")
                    
                    # Add leading dot for LinkedIn compatibility
                    final_domain = f".{domain}" if not domain.startswith('.') else domain
                    converted_cookie['domain'] = final_domain
                    logger.debug(f"Final domain for {cookie_name}: {final_domain}")
                # Only add url if no domain is present
                elif 'url' not in converted_cookie:
                    converted_cookie['url'] = "https://www.linkedin.com"
                
                # Preserve other cookie properties with defaults
                if 'path' in cookie:
                    converted_cookie['path'] = cookie['path']
                else:
                    converted_cookie['path'] = "/"
                
                if 'secure' in cookie:
                    converted_cookie['secure'] = cookie['secure']
                else:
                    converted_cookie['secure'] = True
                
                if 'httpOnly' in cookie:
                    converted_cookie['httpOnly'] = cookie['httpOnly']
                else:
                    converted_cookie['httpOnly'] = False
                
                if 'sameSite' in cookie:
                    converted_cookie['sameSite'] = cookie['sameSite']
                else:
                    converted_cookie['sameSite'] = "None"
                
                converted.append(converted_cookie)
                logger.debug(f"Converted cookie: {cookie_name} with domain: {converted_cookie.get('domain')}")
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