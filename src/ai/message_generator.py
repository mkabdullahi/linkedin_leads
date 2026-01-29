"""
AI Message Generator for LinkedIn Automation.

Handles Groq API integration with llama-3.1-8b-instant model for generating
personalized LinkedIn connection request messages.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
from rich.console import Console

from .prompt_engineering import PromptEngineer
from .fallback_templates import FallbackTemplates
from ..utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@dataclass
class GeneratedMessage:
    """Data structure for generated messages."""
    message: str
    prompt_used: str
    model: str
    temperature: float
    tokens_used: int
    generation_time: float
    fallback_used: bool = False


class MessageGenerator:
    """AI-powered message generator with Groq API integration."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.prompt_engineer = PromptEngineer()
        self.fallback_templates = FallbackTemplates()
        self.model = "llama-3.1-8b-instant"
        self.temperature = 0.2
        self.max_tokens = 300
        self.timeout = 30
    
    async def generate_personalized_message(self, profile_context: Dict[str, Any]) -> GeneratedMessage:
        """Generate a personalized LinkedIn connection message."""
        start_time = time.time()
        
        try:
            # Build context from profile data
            context = self._build_context(profile_context)
            
            # Create prompt with structured data
            prompt = self.prompt_engineer.create_personalized_prompt(context)
            
            # Call Groq API with optimized parameters
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=1.0,
                timeout=self.timeout
            )
            
            # Extract response with defensive programming
            # Check if response has the expected structure
            if not response.choices or len(response.choices) == 0:
                logger.warning("Groq API response has no choices")
                raise ValueError("Empty response choices")
            
            choice = response.choices[0]
            if not choice.message:
                logger.warning("Groq API response has no message")
                raise ValueError("Missing message in response")
            
            # Check if content exists before accessing it
            if choice.message.content is None:
                logger.warning("Groq API response has null content")
                raise ValueError("Null content in message")
            
            message = choice.message.content.strip()
            
            # Check if usage exists before accessing total_tokens
            if response.usage is None:
                logger.warning("Groq API response has no usage information")
                tokens_used = 0
            else:
                tokens_used = response.usage.total_tokens if response.usage.total_tokens is not None else 0
            
            generation_time = time.time() - start_time
            
            logger.info(f"Generated personalized message in {generation_time:.2f}s")
            
            return GeneratedMessage(
                message=message,
                prompt_used=prompt,
                model=self.model,
                temperature=self.temperature,
                tokens_used=tokens_used,
                generation_time=generation_time,
                fallback_used=False
            )
            
        except Exception as e:
            logger.error(f"Groq API failed: {e}")
            
            # Fallback to template-based messages
            fallback_message = self.generate_fallback_message(profile_context)
            generation_time = time.time() - start_time
            
            return GeneratedMessage(
                message=fallback_message,
                prompt_used="",
                model="fallback",
                temperature=0.0,
                tokens_used=0,
                generation_time=generation_time,
                fallback_used=True
            )
    
    def generate_fallback_message(self, profile_context: Dict[str, Any]) -> str:
        """Generate fallback message using templates when AI fails."""
        name = profile_context.get('name', '')
        job_title = profile_context.get('job_title', '')
        company = profile_context.get('company', '')
        industry = profile_context.get('industry', '')
        
        # Determine which template to use based on available data
        if name and job_title and company:
            return self.fallback_templates.get_job_title_company_template(name, job_title, company)
        elif name and job_title:
            return self.fallback_templates.get_job_title_template(name, job_title)
        elif name and industry:
            return self.fallback_templates.get_industry_template(name, industry)
        elif name:
            return self.fallback_templates.get_generic_template(name)
        else:
            return self.fallback_templates.get_generic_template("there")
    
    def _build_context(self, profile_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build structured context for prompt engineering."""
        return {
            'name': profile_context.get('name', ''),
            'job_title': profile_context.get('job_title', ''),
            'company': profile_context.get('company', ''),
            'industry': profile_context.get('industry', ''),
            'location': profile_context.get('location', ''),
            'summary': profile_context.get('summary', ''),
            'skills': profile_context.get('skills', []),
            'experience': profile_context.get('experience', []),
            'education': profile_context.get('education', []),
            'recent_posts': profile_context.get('recent_posts', [])
        }
    
    def validate_message(self, message: str, profile_context: Dict[str, Any]) -> bool:
        """Validate that the generated message meets LinkedIn requirements."""
        # Check length (LinkedIn has 300 character limit for connection notes)
        if len(message) > 300:
            logger.warning(f"Message too long: {len(message)} characters")
            return False
        
        # Check for spam-like patterns
        spam_patterns = [
            r'\b(?:buy|sale|discount|offer|promotion)\b',
            r'[!]{3,}',
            r'[?]{3,}',
            r'[.]{3,}',
            r'\$\d+',
            r'\b(?:free|cheap|easy|quick)\b'
        ]
        
        import re
        for pattern in spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logger.warning(f"Message contains spam-like pattern: {pattern}")
                return False
        
        # Check for personalization
        job_title = profile_context.get('job_title')
        company = profile_context.get('company')
        industry = profile_context.get('industry')
        
        if not any([
            '{name}' in message,
            job_title is not None and job_title in message,
            company is not None and company in message,
            industry is not None and industry in message
        ]):
            logger.warning("Message lacks personalization")
            return False
        
        return True
    
    def optimize_message(self, message: str, profile_context: Dict[str, Any]) -> str:
        """Optimize message for better engagement."""
        # Ensure proper greeting
        if not message.startswith(('Hi', 'Hello', 'Hey', 'Hi there')):
            name = profile_context.get('name', '')
            greeting = f"Hi {name}," if name else "Hi there,"
            message = f"{greeting} {message}"
        
        # Ensure professional tone
        message = message.replace("u", "you").replace("r", "are")
        
        # Add call to action if missing
        if not any(phrase in message.lower() for phrase in [
            "connect", "network", "collaborate", "discuss", "chat"
        ]):
            message += " I'd love to connect and exchange insights in our field."
        
        # Ensure it's under 300 characters
        if len(message) > 300:
            message = message[:297] + "..."
        
        return message
    
    async def generate_batch_messages(self, profiles: List[Dict[str, Any]]) -> List[GeneratedMessage]:
        """Generate messages for multiple profiles efficiently."""
        messages = []
        
        for i, profile in enumerate(profiles):
            # Add delay between requests to avoid rate limiting
            if i > 0:
                time.sleep(1)
            
            message = await self.generate_personalized_message(profile)
            messages.append(message)
            
            logger.info(f"Generated message {i+1}/{len(profiles)}: {message.fallback_used}")
        
        return messages


class LinkedInMessageValidator:
    """Validates LinkedIn messages for quality and compliance."""
    
    @staticmethod
    def check_compliance(message: str) -> Dict[str, Any]:
        """Check if message complies with LinkedIn guidelines."""
        issues = []
        
        # Length check
        if len(message) > 300:
            issues.append(f"Message too long: {len(message)} > 300 characters")
        
        # Spam detection
        spam_keywords = [
            'buy', 'sale', 'discount', 'promotion', 'marketing', 
            'business opportunity', 'work from home', 'earn money'
        ]
        
        for keyword in spam_keywords:
            if keyword.lower() in message.lower():
                issues.append(f"Contains spam keyword: {keyword}")
        
        # Personalization check
        personalization_indicators = ['name', 'job', 'company', 'industry', 'experience']
        has_personalization = any(indicator in message.lower() for indicator in personalization_indicators)
        
        if not has_personalization:
            issues.append("Lacks personalization")
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues,
            'score': max(0, 100 - (len(issues) * 20))
        }
    
    @staticmethod
    def suggest_improvements(message: str, profile_context: Dict[str, Any]) -> List[str]:
        """Suggest improvements for the message."""
        suggestions = []
        
        name = profile_context.get('name', '')
        job_title = profile_context.get('job_title', '')
        company = profile_context.get('company', '')
        
        if name and name.lower() not in message.lower():
            suggestions.append(f"Include the person's name: {name}")
        
        if job_title and job_title.lower() not in message.lower():
            suggestions.append(f"Reference their role: {job_title}")
        
        if company and company.lower() not in message.lower():
            suggestions.append(f"Mention their company: {company}")
        
        if len(message) < 50:
            suggestions.append("Consider adding more context or personalization")
        
        return suggestions