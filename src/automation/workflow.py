"""
Main workflow orchestrator for LinkedIn Automation.

Coordinates all components to execute the complete automation workflow:
Session Management -> Profile Scraping -> Groq LLM Context Enrichment -> 
Personalized Message Generation -> Request Sent.
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from playwright.async_api import Browser, BrowserContext, Page


# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the current working directory to Python path for direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.session_manager import LinkedInSessionManager as SessionManager
from src.core.browser_manager import BrowserManager
from src.ai.message_generator import MessageGenerator
from src.automation.connection_manager import ConnectionManager
from src.utils.data_model import DataModel
from src.utils.logger import get_logger
from src.core.config import config

logger = get_logger(__name__)


class LinkedInAutomationWorkflow:
    """Main workflow orchestrator for LinkedIn automation."""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.browser_manager = BrowserManager()
        self.data_model = DataModel()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.connection_manager = None
        
    async def run_workflow(self, prospects: List[Dict[str, Any]], max_requests: int = 9) -> Dict[str, Any]:
        """Execute the complete LinkedIn automation workflow."""
        
        start_time = time.time()
        workflow_result = {
            'success': False,
            'total_prospects': len(prospects),
            'successful_requests': 0,
            'failed_requests': 0,
            'results': [],
            'execution_time': 0,
            'errors': []
        }
        
        try:
            logger.info("🚀 Starting LinkedIn automation workflow...")
            
            # Phase 1: Load cookies and initialize browser
            logger.info("Phase 1: Initializing LinkedIn session with cookies...")
            await self._initialize_authenticated_session()
            
            # Verify we're on LinkedIn (simple check)
            if self.page is None:
                raise Exception("Page not initialized")
            
            # Simple verification: check if we're on a LinkedIn page
            current_url = self.page.url
            if "linkedin.com" not in current_url:
                raise Exception(f"❌ Not on LinkedIn page. Current URL: {current_url}")
            
            logger.info(f"✅ Successfully navigated to LinkedIn: {current_url}")
            
            # Initialize connection manager with Groq API
            message_generator = MessageGenerator(self._get_groq_api_key())
            if self.page is None:
                raise Exception("Page not initialized")
            self.connection_manager = ConnectionManager(self.page, message_generator)
            
            # Phase 2: Profile Scraping & AI Integration
            logger.info("Phase 2: Processing prospects...")
            results = await self.connection_manager.send_bulk_requests(prospects, max_requests)
            
            # Phase 3: Process results
            logger.info("Phase 3: Processing results...")
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = len(results) - successful_requests
            
            workflow_result.update({
                'success': successful_requests > 0,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'results': results,
                'execution_time': time.time() - start_time
            })
            
            # Save results to data model
            await self._save_results(results, workflow_result)
            
            logger.info(f"✅ Workflow completed: {successful_requests}/{len(prospects)} successful")
            
        except Exception as e:
            error_msg = f"❌ Workflow failed: {str(e)}"
            logger.error(error_msg)
            workflow_result['errors'].append(error_msg)
            
        finally:
            # Cleanup
            await self._cleanup()
        
        return workflow_result
    
    async def _initialize_authenticated_session(self):
        """Initialize browser with cookie-based authentication."""
        # Launch browser
        self.browser = await self.browser_manager.initialize()
        self.context = await self.browser_manager.create_context()
        
        # Load and apply cookies
        await self.session_manager.load_cookies_from_json()
        await self.session_manager.apply_cookies_to_context(self.context)
        
        # Create page and navigate to LinkedIn
        self.page = await self.context.new_page()
        logger.info("Navigating to LinkedIn feed...")
        
        # Simple navigation with reasonable timeout
        try:
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
            logger.info("✅ Successfully navigated to LinkedIn feed")
        except Exception as e:
            logger.warning(f"❌ Navigation failed: {e}. Trying fallback...")
            try:
                await self.page.goto("https://www.linkedin.com/", wait_until="domcontentloaded", timeout=15000)
                logger.info("✅ Successfully navigated to LinkedIn homepage")
            except Exception as e2:
                logger.error(f"❌ All navigation attempts failed: {e2}")
                raise Exception(f"Failed to navigate to LinkedIn: {e2}")
    
    
    async def run_single_request(self, prospect: Dict[str, Any]) -> Dict[str, Any]:
        """Run automation for a single prospect."""
        try:
            # Ensure we have a session
            if not self.page or not self.connection_manager:
                await self._initialize_authenticated_session()
                message_generator = MessageGenerator(self._get_groq_api_key())
                if self.page is None:
                    raise Exception("Page not initialized")
                self.connection_manager = ConnectionManager(self.page, message_generator)
            
            # Send single request
            result = await self.connection_manager.send_connection_request(
                prospect['linkedin_url'], 
                prospect
            )
            
            # Save result
            await self.data_model.save_sent_request(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Single request failed: {e}")
            return {
                'success': False,
                'profile_url': prospect.get('linkedin_url', ''),
                'error': str(e)
            }
    
    async def check_prospect_status(self, prospect_url: str) -> str:
        """Check the connection status of a prospect."""
        try:
            if not self.page or not self.connection_manager:
                await self._initialize_authenticated_session()
                message_generator = MessageGenerator(self._get_groq_api_key())
                if self.page is None:
                    raise Exception("Page not initialized")
                self.connection_manager = ConnectionManager(self.page, message_generator)
            
            return await self.connection_manager.check_connection_status(prospect_url)
            
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return "error"
    
    async def _save_results(self, results: List[Dict[str, Any]], workflow_result: Dict[str, Any]):
        """Save workflow results to data model."""
        # Save individual results
        for result in results:
            if result['success']:
                await self.data_model.save_sent_request(result)
            else:
                await self.data_model.save_failed_request(result)
        
        # Save workflow summary
        summary = {
            'timestamp': time.time(),
            'total_prospects': workflow_result['total_prospects'],
            'successful_requests': workflow_result['successful_requests'],
            'failed_requests': workflow_result['failed_requests'],
            'execution_time': workflow_result['execution_time'],
            'errors': workflow_result['errors']
        }
        
        await self.data_model.save_workflow_summary(summary)
    
    def _get_groq_api_key(self) -> str:
        """Get Groq API key from environment or config."""
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            api_key = config.app.ai.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        return api_key.strip().strip('"')
    
    async def _cleanup(self):
        """Clean up resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            await self.browser_manager.cleanup()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    async def validate_setup(self) -> Dict[str, Any]:
        """Validate that all components are properly configured."""
        validation_result = {
            'cookies_file': False,
            'browser_manager': False,
            'groq_api': False,
            'data_model': False,
            'prospects_data': False,
            'overall_valid': False
        }
        
        try:
            # Test cookies file exists - use absolute path from project root
            cookies_path = Path(project_root) / "config" / "linkedin_cookies.json"
            logger.info(f"🔍 Looking for cookies at: {cookies_path}")
            
            if cookies_path.exists():
                with open(cookies_path) as f:
                    cookies = json.load(f)
                    validation_result['cookies_file'] = len(cookies) > 0
                    logger.info(f"✅ Found {len(cookies)} cookies in {cookies_path}")
            else:
                logger.error(f"❌ Cookie file not found: {cookies_path}")
                logger.info(f"📂 Expected location: {cookies_path.absolute()}")
            
            # Test browser manager
            await self.browser_manager.initialize()
            validation_result['browser_manager'] = True
            logger.info("✅ Browser manager initialized")
            
            # Test Groq API
            try:
                api_key = os.getenv('GROQ_API_KEY')
                if not api_key:
                    raise ValueError("GROQ_API_KEY not found in environment")
                validation_result['groq_api'] = True
                logger.info("✅ Groq API key configured")
            except Exception as e:
                logger.error(f"❌ Groq API validation failed: {e}")
                validation_result['groq_api'] = False
            
            # Test data model
            validation_result['data_model'] = await self.data_model.validate_setup()
            
            # Test prospects data
            prospects = await self.data_model.load_prospects()
            validation_result['prospects_data'] = len(prospects) > 0
            logger.info(f"✅ Found {len(prospects)} prospects")
            
            # Overall validation
            validation_result['overall_valid'] = all([
                validation_result['cookies_file'],
                validation_result['browser_manager'],
                validation_result['groq_api'],
                validation_result['data_model'],
                validation_result['prospects_data']
            ])
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
        
        return validation_result


async def main():
    """Main entry point for the LinkedIn automation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Automation Workflow')
    parser.add_argument('--prospects', type=str, help='Path to prospects JSON file')
    parser.add_argument('--max-requests', type=int, default=9, help='Maximum requests per run')
    parser.add_argument('--validate', action='store_true', help='Validate setup only')
    parser.add_argument('--single', type=str, help='Single prospect URL to process')
    
    args = parser.parse_args()
    
    workflow = LinkedInAutomationWorkflow()
    
    if args.validate:
        # Run validation only
        logger.info("🔍 Running setup validation...")
        validation = await workflow.validate_setup()
        print(f"\n{'='*60}")
        print(f"Setup validation: {'✅ PASSED' if validation['overall_valid'] else '❌ FAILED'}")
        print(f"{'='*60}")
        print(json.dumps(validation, indent=2))
        return
    
    if args.single:
        # Process single prospect
        prospect = {'linkedin_url': args.single}
        result = await workflow.run_single_request(prospect)
        print(f"Single request result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        print(json.dumps(result, indent=2))
        return
    
    # Load prospects and run workflow
    if args.prospects:
        with open(args.prospects, 'r') as f:
            prospects = json.load(f)
    else:
        # Load from data model
        prospects = await workflow.data_model.load_prospects()
    
    if not prospects:
        logger.error("❌ No prospects found. Please provide a prospects file or add prospects to the data model.")
        return
    
    # Run workflow
    result = await workflow.run_workflow(prospects, args.max_requests)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Workflow completed: {result['successful_requests']}/{result['total_prospects']} successful")
    print(f"Execution time: {result['execution_time']:.2f} seconds")
    print(f"{'='*60}")
    
    if result['errors']:
        print("\n❌ Errors:")
        for error in result['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())