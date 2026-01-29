"""
Configuration management for LinkedIn Automation System.

This module handles environment variables, secrets, and application configuration
using dataclasses for simpler, more flexible configuration management.
"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LinkedInConfig:
    """LinkedIn-specific configuration"""
    max_requests_per_day: int = 9
    max_requests_per_run: int = 9
    session_timeout: int = 3600  # 1 hour
    login_timeout: int = 60      # 1 minute
    profile_scrape_timeout: int = 30  # 30 seconds
    li_cookies: Optional[str] = None
    target_search_urls: List[str] = field(default_factory=list)
    max_profiles: int = 5
    min_delay: float = 30.0
    max_delay: float = 120.0
    page_timeout: int = 30000
    debug_mode: bool = False

    def __post_init__(self):
        # Load from environment variables
        self.max_requests_per_day = int(os.getenv("MAX_REQUESTS", str(self.max_requests_per_day)))
        self.max_requests_per_run = int(os.getenv("MAX_REQUESTS", str(self.max_requests_per_run)))
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", str(self.session_timeout)))
        self.login_timeout = int(os.getenv("LOGIN_TIMEOUT", str(self.login_timeout)))
        self.profile_scrape_timeout = int(os.getenv("PROFILE_SCRAPE_TIMEOUT", str(self.profile_scrape_timeout)))
        
        # LinkedIn specific settings
        self.li_cookies = os.getenv("LI_COOKIES", self.li_cookies)
        self.max_profiles = int(os.getenv("MAX_PROFILES", str(self.max_profiles)))
        self.min_delay = float(os.getenv("MIN_DELAY", str(self.min_delay)))
        self.max_delay = float(os.getenv("MAX_DELAY", str(self.max_delay)))
        self.page_timeout = int(os.getenv("PAGE_TIMEOUT", str(self.page_timeout)))
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # Load search URLs
        if not self.target_search_urls:
            env_urls = os.getenv("TARGET_SEARCH_URLS")
            if env_urls:
                try:
                    self.target_search_urls = json.loads(env_urls)
                except json.JSONDecodeError:
                    self.target_search_urls = [env_urls]
            else:
                # Default LinkedIn search URLs
                self.target_search_urls = [
                    "https://www.linkedin.com/search/results/people/?keywords=python%20developer",
                    "https://www.linkedin.com/search/results/people/?keywords=software%20engineer",
                    "https://www.linkedin.com/search/results/people/?keywords=web%20developer"
                ]

    async def load_cookies_async(self) -> None:
        """Load cookies asynchronously."""
        if Path(".secrets/linkedin_cookies.json.enc").exists():
            try:
                cookies_data = await asyncio.to_thread(lambda: json.load(open(".secrets/linkedin_cookies.json.enc", "r")))
                self.li_cookies = json.dumps(cookies_data)
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")
                self.li_cookies = os.getenv("LI_COOKIES")
        else:
            self.li_cookies = os.getenv("LI_COOKIES")

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.li_cookies:
            raise ValueError("LI_COOKIES environment variable is required")


@dataclass
class AIConfig:
    """AI service configuration"""
    groq_api_key: Optional[str] = None
    primary_llm: str = "groq"
    fallback_mode: str = "auto"
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.2
    max_tokens: int = 300
    timeout: int = 30

    def __post_init__(self):
        # Load from environment variables
        self.groq_api_key = os.getenv("GROQ_API_KEY", self.groq_api_key)
        self.primary_llm = os.getenv("PRIMARY_LLM", self.primary_llm)
        self.fallback_mode = os.getenv("FALLBACK_MODE", self.fallback_mode)
        self.model = os.getenv("AI_MODEL", self.model)
        self.temperature = float(os.getenv("AI_TEMPERATURE", str(self.temperature)))
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", str(self.max_tokens)))
        self.timeout = int(os.getenv("AI_TIMEOUT", str(self.timeout)))

    def validate(self) -> None:
        """Validate AI configuration."""
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

    def get_llm_providers(self) -> List[Dict[str, Any]]:
        """Get configured LLM providers."""
        providers = []
        
        if self.groq_api_key:
            providers.append({
                "name": "groq-llama",
                "provider": "openai",
                "model": self.model,
                "api_key": self.groq_api_key,
                "base_url": "https://api.groq.com/openai/v1",
                "priority": 1,
                "enabled": True,
                "rate_limit": {"requests_per_minute": 30}
            })
        return providers


@dataclass
class BrowserConfig:
    """Browser automation configuration"""
    headless: bool = False
    viewport_width: int = 1366
    viewport_height: int = 768
    slow_mo: int = 100
    timeout: int = 30000
    user_agent: Optional[str] = None

    def __post_init__(self):
        # Load from environment variables
        self.headless = os.getenv("HEADLESS_BROWSER", "false").lower() == "true"
        self.viewport_width = int(os.getenv("VIEWPORT_WIDTH", str(self.viewport_width)))
        self.viewport_height = int(os.getenv("VIEWPORT_HEIGHT", str(self.viewport_height)))
        self.slow_mo = int(os.getenv("SLOW_MO", str(self.slow_mo)))
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", str(self.timeout)))
        
        # Set default user agent if none provided
        if self.user_agent is None:
            self.user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )


@dataclass
class SecurityConfig:
    """Security and encryption configuration"""
    encryption_key: Optional[str] = None
    secrets_file: str = ".secrets/encrypted_secrets.json"
    session_file: str = "data/session_state.json"
    max_session_age: int = 604800  # 7 days in seconds

    def __post_init__(self):
        # Load from environment variables
        self.encryption_key = os.getenv("ENCRYPTION_KEY", self.encryption_key)
        self.secrets_file = os.getenv("SECRETS_FILE", self.secrets_file)
        self.session_file = os.getenv("SESSION_FILE", self.session_file)
        self.max_session_age = int(os.getenv("MAX_SESSION_AGE", str(self.max_session_age)))


@dataclass
class AppConfig:
    """Main application configuration"""
    environment: str = "production"
    data_dir: str = "data"
    logs_dir: str = "logs"
    config_dir: str = "config"
    
    # Component configurations
    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    def __post_init__(self):
        # Load from environment variables
        self.environment = os.getenv("ENVIRONMENT", self.environment)
        self.data_dir = os.getenv("DATA_DIR", self.data_dir)
        self.logs_dir = os.getenv("LOGS_DIR", self.logs_dir)
        self.config_dir = os.getenv("CONFIG_DIR", self.config_dir)

    def validate_all(self) -> None:
        """Validate all configuration components."""
        self.linkedin.validate()
        self.ai.validate()


class UnifiedConfig:
    """Unified configuration manager"""
    
    def __init__(self):
        self.app = AppConfig()
    
    async def load_all(self) -> None:
        """Load all configuration components."""
        await self.app.linkedin.load_cookies_async()
    
    def validate_all(self) -> None:
        """Validate all configuration components."""
        self.app.validate_all()
    
    def get_env_summary(self) -> dict:
        """Get summary of current configuration (without sensitive data)"""
        return {
            "groq_api_configured": bool(self.app.ai.groq_api_key),
            "linkedin_cookies_configured": bool(self.app.linkedin.li_cookies),
            "min_delay": self.app.linkedin.min_delay,
            "max_delay": self.app.linkedin.max_delay,
            "page_timeout": self.app.linkedin.page_timeout,
            "debug_mode": self.app.linkedin.debug_mode,
            "max_profiles": self.app.linkedin.max_profiles,
            "environment": self.app.environment,
            "data_dir": self.app.data_dir,
            "logs_dir": self.app.logs_dir
        }


# Global configuration instance
config = UnifiedConfig()