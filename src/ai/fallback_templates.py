"""
Fallback Templates for LinkedIn Automation.

Provides template-based message generation when AI fails or profile data is sparse.
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FallbackTemplates:
    """Template-based message generation for fallback scenarios."""
    
    def __init__(self):
        self.job_title_company_templates = [
            "Hi {name}, I'm impressed by your work as a {job_title} at {company}. I'm also in the {industry} space and would love to connect and exchange insights about our industry.",
            "Hello {name}, I noticed your role as {job_title} at {company}. Given our shared interest in {industry}, I'd appreciate connecting to discuss industry trends and best practices.",
            "Hi {name}, your experience as a {job_title} at {company} caught my attention. I'm exploring opportunities in {industry} and would value connecting with professionals like yourself.",
            "Hello {name}, I came across your profile and was impressed by your background in {industry} as a {job_title} at {company}. I'd be interested in connecting to learn from your experience.",
            "Hi {name}, as someone also working in {industry}, I'd love to connect. Your role as {job_title} at {company} aligns with my professional interests and network goals."
        ]
        
        self.job_title_templates = [
            "Hi {name}, I'm impressed by your work as a {job_title}. I'm also passionate about {industry} and would love to connect and exchange insights about our field.",
            "Hello {name}, I noticed your role as {job_title} and wanted to reach out. Given our shared interest in {industry}, I'd appreciate connecting to discuss industry developments.",
            "Hi {name}, your experience as a {job_title} caught my attention. I'm exploring the {industry} space and would value connecting with professionals in the field.",
            "Hello {name}, I came across your profile and was impressed by your background in {industry} as a {job_title}. I'd be interested in connecting to learn from your experience.",
            "Hi {name}, as someone also working in {industry}, I'd love to connect. Your role as {job_title} aligns with my professional interests and network goals."
        ]
        
        self.industry_templates = [
            "Hi {name}, I'm impressed by your work in the {industry} industry. I'm also passionate about this field and would love to connect and exchange insights about industry trends.",
            "Hello {name}, I noticed your involvement in the {industry} space and wanted to reach out. Given our shared interest, I'd appreciate connecting to discuss industry developments.",
            "Hi {name}, your experience in the {industry} industry caught my attention. I'm exploring opportunities in this field and would value connecting with professionals like yourself.",
            "Hello {name}, I came across your profile and was impressed by your background in {industry}. I'd be interested in connecting to learn from your experience.",
            "Hi {name}, as someone also working in {industry}, I'd love to connect. Your experience in this field aligns with my professional interests and network goals."
        ]
        
        self.generic_templates = [
            "Hi {name}, I came across your profile and was impressed by your professional background. I'm always looking to expand my network with accomplished professionals like yourself.",
            "Hello {name}, I noticed we share some professional interests and thought it would be valuable to connect. I'm always interested in connecting with professionals in our field.",
            "Hi {name}, I'm impressed by your professional journey. I'm actively building my network with accomplished individuals and would appreciate connecting with you.",
            "Hello {name}, I came across your profile and thought it would be valuable to connect. I'm always interested in expanding my professional network.",
            "Hi {name}, I'm looking to connect with professionals who are passionate about their work. Your profile caught my attention and I'd love to connect."
        ]
    
    def get_job_title_company_template(self, name: str, job_title: str, company: str) -> str:
        """Get a template for when we have name, job title, and company."""
        import random
        
        template = random.choice(self.job_title_company_templates)
        
        # Fill in the template
        message = template.format(
            name=name,
            job_title=job_title,
            company=company,
            industry=self._get_industry_from_company(company)
        )
        
        return self._optimize_message(message)
    
    def get_job_title_template(self, name: str, job_title: str) -> str:
        """Get a template for when we have name and job title."""
        import random
        
        template = random.choice(self.job_title_templates)
        
        # Fill in the template
        message = template.format(
            name=name,
            job_title=job_title,
            industry=self._get_industry_from_job_title(job_title)
        )
        
        return self._optimize_message(message)
    
    def get_industry_template(self, name: str, industry: str) -> str:
        """Get a template for when we have name and industry."""
        import random
        
        template = random.choice(self.industry_templates)
        
        # Fill in the template
        message = template.format(
            name=name,
            industry=industry
        )
        
        return self._optimize_message(message)
    
    def get_generic_template(self, name: str) -> str:
        """Get a generic template when we only have the name."""
        import random
        
        template = random.choice(self.generic_templates)
        
        # Fill in the template
        message = template.format(name=name)
        
        return self._optimize_message(message)
    
    def _get_industry_from_company(self, company: str) -> str:
        """Infer industry from company name (basic implementation)."""
        tech_companies = ['google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix', 'tesla', 'nvidia']
        finance_companies = ['jpmorgan', 'goldman', 'morgan', 'citigroup', 'bank', 'capital', 'credit']
        healthcare_companies = ['pfizer', 'novartis', 'roche', 'merck', 'johnson', 'medtronic', 'abbott']
        
        company_lower = company.lower()
        
        if any(c in company_lower for c in tech_companies):
            return "technology"
        elif any(c in company_lower for c in finance_companies):
            return "finance"
        elif any(c in company_lower for c in healthcare_companies):
            return "healthcare"
        else:
            return "professional"
    
    def _get_industry_from_job_title(self, job_title: str) -> str:
        """Infer industry from job title (basic implementation)."""
        tech_titles = ['developer', 'engineer', 'programmer', 'software', 'tech', 'data', 'ai', 'ml']
        finance_titles = ['analyst', 'manager', 'director', 'vp', 'cfo', 'finance', 'accounting', 'banking']
        marketing_titles = ['marketer', 'marketing', 'brand', 'content', 'social', 'digital', 'growth']
        
        title_lower = job_title.lower()
        
        if any(t in title_lower for t in tech_titles):
            return "technology"
        elif any(t in title_lower for t in finance_titles):
            return "finance"
        elif any(t in title_lower for t in marketing_titles):
            return "marketing"
        else:
            return "professional"
    
    def _optimize_message(self, message: str) -> str:
        """Optimize the message for LinkedIn requirements."""
        # Ensure proper greeting
        if not message.startswith(('Hi', 'Hello', 'Hey')):
            message = f"Hi there, {message}"
        
        # Ensure professional tone
        message = message.replace("u", "you").replace("r", "are")
        
        # Add call to action if missing
        if not any(phrase in message.lower() for phrase in [
            "connect", "network", "collaborate", "discuss", "chat", "exchange"
        ]):
            message += " I'd love to connect and exchange insights in our field."
        
        # Ensure it's under 300 characters
        if len(message) > 300:
            message = message[:297] + "..."
        
        return message
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about available templates."""
        return {
            'job_title_company_templates': len(self.job_title_company_templates),
            'job_title_templates': len(self.job_title_templates),
            'industry_templates': len(self.industry_templates),
            'generic_templates': len(self.generic_templates),
            'total_templates': (
                len(self.job_title_company_templates) +
                len(self.job_title_templates) +
                len(self.industry_templates) +
                len(self.generic_templates)
            )
        }
    
    def validate_template_coverage(self, profile_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that we have appropriate templates for the profile data."""
        coverage = {
            'has_name': bool(profile_context.get('name')),
            'has_job_title': bool(profile_context.get('job_title')),
            'has_company': bool(profile_context.get('company')),
            'has_industry': bool(profile_context.get('industry')),
        }
        
        # Determine which template type would be used
        if coverage['has_name'] and coverage['has_job_title'] and coverage['has_company']:
            template_type = 'job_title_company'
        elif coverage['has_name'] and coverage['has_job_title']:
            template_type = 'job_title'
        elif coverage['has_name'] and coverage['has_industry']:
            template_type = 'industry'
        elif coverage['has_name']:
            template_type = 'generic'
        else:
            template_type = 'none'
        
        return {
            'coverage': coverage,
            'template_type': template_type,
            'can_generate_message': template_type != 'none'
        }