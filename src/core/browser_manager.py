"""
Browser management for LinkedIn Automation System.

Handles Playwright browser setup with anti-detection measures, human-like behavior simulation,
and browser fingerprinting to handle LinkedIn's dynamic DOM and anti-bot measures.
"""

import asyncio
import random
import time
from typing import Optional, Dict, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from rich.console import Console

from .config import config

console = Console()


class BrowserManager:
    """Manages Playwright browser instances with anti-detection measures."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    async def initialize(self):
        """Initialize Playwright."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
    
    async def create_context(self) -> BrowserContext:
        """Create a new browser context with anti-detection measures."""
        await self.initialize()
        
        if self.browser is None:
            self.browser = await self._launch_browser()
        
        # Create new context with randomized settings
        context = await self.browser.new_context(
            viewport={
                'width': config.app.browser.viewport_width,
                'height': config.app.browser.viewport_height
            },
            user_agent=self._get_random_user_agent(),
            java_script_enabled=True,
            ignore_https_errors=True,
            # Anti-detection settings
            bypass_csp=True,
            reduced_motion="no-preference"
        )
        
        # Configure context with anti-detection measures
        await self._configure_context(context)
        
        return context
    
    async def _launch_browser(self) -> Browser:
        """Launch browser with anti-detection configuration."""
        await self.initialize()
        # Use more conservative browser launch arguments
        return await self.playwright.firefox.launch(
            headless=config.app.browser.headless,
            slow_mo=config.app.browser.slow_mo,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Optional: speed up loading
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-features=AudioServiceOutOfProcess'
            ]
        )
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self._user_agents)
    
    async def _configure_context(self, context: BrowserContext):
        """Configure browser context with anti-detection measures."""
        page = await context.new_page()
        
        # Set realistic viewport and device metrics
        await page.set_viewport_size({
            'width': config.app.browser.viewport_width,
            'height': config.app.browser.viewport_height
        })
        
        # Configure navigator properties to appear more human-like
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Override plugins and mimeTypes
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Configure media devices to appear more realistic
        await page.add_init_script("""
            // Mock media devices
            const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = (constraints) => {
                return new Promise((resolve, reject) => {
                    if (constraints.audio && !constraints.video) {
                        resolve(new MediaStream());
                    } else {
                        originalGetUserMedia(constraints).catch(reject);
                    }
                });
            };
        """)
        
        await page.close()
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def simulate_human_behavior(self, page: Page, action: str = "general"):
        """Simulate human-like behavior to avoid detection."""
        if action == "scroll":
            # Simulate realistic scrolling
            scroll_amount = random.randint(200, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(1, 3))
            
        elif action == "mouse_move":
            # Simulate mouse movements
            x = random.randint(100, config.app.browser.viewport_width - 100)
            y = random.randint(100, config.app.browser.viewport_height - 100)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.5, 2))
            
        elif action == "typing":
            # Simulate human typing speed
            typing_delay = random.uniform(0.05, 0.2)
            return typing_delay
            
        else:
            # General human-like delays
            delay = random.uniform(1, 5)
            await asyncio.sleep(delay)