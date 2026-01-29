"""
Prompt Engineering for LinkedIn Automation.

Handles structured prompt creation for Groq API with context-aware message generation.
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PromptEngineer:
    """Advanced prompt engineering for LinkedIn message generation."""
    
    def create_personalized_prompt(self, context: Dict[str, Any]) -> str:
        """Create a structured prompt for personalized message generation."""
        
        # Build context summary
        context_summary = self._build_context_summary(context)
        
        # Create structured prompt
        prompt = f"""You are a professional networking expert. Generate a LinkedIn connection request message (max 300 characters) for {context.get('name', 'this professional')}, a {context.get('job_title', 'professional')} at {context.get('company', 'their company')} in the {context.get('industry', 'industry')} industry.

Context:
{context_summary}

Requirements:
- Professional but personable tone
- Reference specific profile elements from the context above
- Keep under 300 characters (LinkedIn limit)
- Avoid generic phrases like "I came across your profile"
- Focus on {context.get('industry', 'industry')}-relevant common ground
- Include a clear, professional reason for connecting
- Do not use emojis or excessive punctuation
- Make it sound natural and human-written

Generate the message text only, without any explanations or additional text."""
        
        return prompt
    
    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a structured context summary for the prompt."""
        summary_parts = []
        
        # Basic info
        if context.get('job_title') and context.get('company'):
            summary_parts.append(f"- Current Role: {context['job_title']} at {context['company']}")
        
        if context.get('industry'):
            summary_parts.append(f"- Industry: {context['industry']}")
        
        if context.get('location'):
            summary_parts.append(f"- Location: {context['location']}")
        
        # Professional background
        if context.get('summary'):
            summary = context['summary'][:200]  # Truncate long summaries
            summary_parts.append(f"- Professional Summary: {summary}")
        
        if context.get('skills'):
            skills = ', '.join(context['skills'][:3])  # Top 3 skills
            summary_parts.append(f"- Key Skills: {skills}")
        
        # Experience highlights
        if context.get('experience'):
            exp = context['experience'][0]  # Most recent experience
            summary_parts.append(f"- Recent Experience: {exp.get('title', '')} at {exp.get('company', '')}")
        
        # Education
        if context.get('education'):
            edu = context['education'][0]  # Highest education
            summary_parts.append(f"- Education: {edu}")
        
        # Recent activity (if available)
        if context.get('recent_posts'):
            posts = context['recent_posts'][0][:100]  # First post, truncated
            summary_parts.append(f"- Recent Post: {posts}")
        
        return '\n'.join(summary_parts)
    
    def create_followup_prompt(self, context: Dict[str, Any], previous_message: str) -> str:
        """Create a prompt for generating follow-up messages."""
        
        context_summary = self._build_context_summary(context)
        
        prompt = f"""You are a professional networking expert. Generate a LinkedIn follow-up message (max 300 characters) for {context.get('name', 'this professional')}.

Previous message: "{previous_message}"

Context:
{context_summary}

Requirements:
- Reference the previous message naturally
- Add new value or insight
- Keep under 300 characters
- Professional and non-pushy tone
- Provide a reason for continued conversation
- Avoid repeating the same request

Generate the message text only."""
        
        return prompt
    
    def create_industry_specific_prompt(self, context: Dict[str, Any], industry_focus: str) -> str:
        """Create an industry-specific prompt for specialized messaging."""
        
        context_summary = self._build_context_summary(context)
        
        industry_prompts = {
            'technology': "Focus on tech trends, innovation, and digital transformation",
            'finance': "Emphasize financial expertise, market insights, and investment strategies", 
            'healthcare': "Highlight healthcare innovation, patient care, and medical advancements",
            'education': "Focus on learning, professional development, and educational technology",
            'marketing': "Emphasize branding, digital marketing, and customer engagement",
            'sales': "Focus on relationship building, sales strategies, and customer success"
        }
        
        industry_focus_text = industry_prompts.get(industry_focus.lower(), 
                                                  f"Focus on {industry_focus} industry insights and best practices")
        
        prompt = f"""You are a professional networking expert. Generate a LinkedIn connection request message (max 300 characters) for {context.get('name', 'this professional')} in the {industry_focus} industry.

Context:
{context_summary}

Industry Focus:
{industry_focus_text}

Requirements:
- Industry-specific language and references
- Demonstrate knowledge of {industry_focus} trends
- Professional but personable tone
- Keep under 300 characters
- Avoid generic networking phrases
- Show genuine interest in {industry_focus} discussions

Generate the message text only."""
        
        return prompt
    
    def validate_prompt_quality(self, prompt: str) -> Dict[str, Any]:
        """Validate the quality of a generated prompt."""
        issues = []
        
        # Check length
        if len(prompt) < 100:
            issues.append("Prompt too short - may not provide enough context")
        
        if len(prompt) > 1000:
            issues.append("Prompt too long - may cause token limitations")
        
        # Check for required elements
        required_elements = ['professional', 'LinkedIn', 'connection', '300 characters']
        missing_elements = [elem for elem in required_elements if elem not in prompt.lower()]
        
        if missing_elements:
            issues.append(f"Missing required elements: {', '.join(missing_elements)}")
        
        # Check for personalization
        if '{name}' not in prompt and 'professional' not in prompt:
            issues.append("Prompt lacks personalization placeholders")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'length': len(prompt),
            'score': max(0, 100 - (len(issues) * 25))
        }