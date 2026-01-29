"""
Session management for LinkedIn Automation System.

Handles LinkedIn authentication, cookie persistence, and browser state management
between GitHub Action runs to avoid daily logins.
"""

import json
import os
import time
import asyncio
from typing import Dict, Optional, Any
from pathlib import Path
from playwright.async_api import BrowserContext, Page, async_playwright

from .config import config
from .browser_manager import BrowserManager

# Import logger directly
import logging
from rich.console import Console

console = Console()

# Configure logger
logger = logging.getLogger(__name__)


class SessionManager:
    """Manages LinkedIn session persistence and authentication."""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.session_file = Path(config.app.security.session_file)
        self.cookies_file = Path("cookies.json")  # Use simple cookies.json file
        
        # Ensure directories exist
        self.cookies_file.parent.mkdir(exist_ok=True)
        
    
    async def get_authenticated_context(self) -> BrowserContext:
        """Get an authenticated browser context with LinkedIn session."""
        console.print("[bold blue]Initializing LinkedIn session...[/bold blue]")
        
        # Try to load existing session
        context = await self._load_existing_session()
        if context:
            console.print("[bold green]✓ Loaded existing LinkedIn session[/bold green]")
            return context
        
        # Create new session
        console.print("[bold yellow]Creating new LinkedIn session...[/bold yellow]")
        context = await self._create_new_session()
        return context
    
    async def _load_existing_session(self) -> Optional[BrowserContext]:
        """Load existing LinkedIn session from cookies.json."""
        try:
            if not self.cookies_file.exists():
                return None
            
            # Read cookies from simple JSON file
            with open(self.cookies_file, 'r') as f:
                cookies_data = json.load(f)
            
            # Check session age
            if time.time() - cookies_data.get('timestamp', 0) > config.app.security.max_session_age:
                logger.warning("Session too old, creating new session")
                return None
            
            # Create browser context
            context = await self.browser_manager.create_context()
            
            # Set cookies
            await context.add_cookies(cookies_data['cookies'])
            
            # Navigate to LinkedIn to validate session
            page = await context.new_page()
            await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")
            
            # Check if still logged in
            if await self._is_logged_in(page):
                logger.info("Successfully loaded existing session")
                await page.close()
                return context
            else:
                logger.warning("Existing session invalid, will create new one")
                await context.close()
                return None
                
        except Exception as e:
            logger.error(f"Failed to load existing session: {e}")
            return None
    
    async def _create_new_session(self) -> BrowserContext:
        """Create a new LinkedIn session with manual login."""
        console.print("[bold yellow]Please complete LinkedIn login in the browser window...[/bold yellow]")
        
        context = await self.browser_manager.create_context()
        page = await context.new_page()
        
        try:
            # Navigate to LinkedIn
            await page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            # Wait for user to complete login
            console.print("[bold cyan]Waiting for manual login completion...[/bold cyan]")
            
            # Poll for successful login
            for _ in range(60):  # Wait up to 10 minutes
                await asyncio.sleep(10)
                
                if await self._is_logged_in(page):
                    console.print("[bold green]✓ LinkedIn login detected![/bold green]")
                    break
            else:
                raise TimeoutError("Login timeout - please complete login within 10 minutes")
            
            # Save session cookies
            await self._save_session_cookies(context)
            
            return context
            
        except Exception as e:
            await context.close()
            raise e
    
    async def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged into LinkedIn."""
        try:
            # Check for common logged-in indicators
            logged_in_indicators = [
                'a[href*="/messaging"]',
                'a[href*="/profile"]',
                '[data-test-id="profile-nav-item"]',
                'button[aria-label*="Profile"]'
            ]
            
            for indicator in logged_in_indicators:
                if await page.locator(indicator).is_visible(timeout=1000):
                    return True
            
            # Check URL - should not be on login page
            current_url = page.url
            if "login" not in current_url and "feed" in current_url:
                return True
                
            return False
            
        except Exception:
            return False
    
    async def _save_session_cookies(self, context: BrowserContext):
        """Save session cookies to simple JSON file."""
        try:
            cookies = await context.cookies("https://www.linkedin.com")
            
            session_data = {
                'cookies': cookies,
                'timestamp': time.time(),
                'user_agent': await context.new_page().evaluate("() => navigator.userAgent")
            }
            
            # Save as simple JSON
            with open(self.cookies_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info("Session cookies saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save session cookies: {e}")
            raise
    
    async def refresh_session(self, context: BrowserContext):
        """Refresh the session by creating a new one."""
        logger.info("Refreshing LinkedIn session")
        
        # Close current context
        await context.close()
        
        # Create new session
        return await self._create_new_session()
    
    async def cleanup(self):
        """Clean up resources."""
        await self.browser_manager.cleanup()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        session_info = {
            'session_file_exists': self.session_file.exists(),
            'cookies_file_exists': self.cookies_file.exists(),
            'max_session_age': config.app.security.max_session_age
        }
        
        if self.cookies_file.exists():
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies_data = json.load(f)
                session_info['session_age'] = time.time() - cookies_data.get('timestamp', 0)
                session_info['session_valid'] = session_info['session_age'] < config.app.security.max_session_age
            except Exception as e:
                session_info['session_valid'] = False
                session_info['session_error'] = str(e)
        
        return session_info
