"""
Discovery workflow for LinkedIn Automation.

Integrates prospect discovery with the existing connection workflow.
Provides a complete automated pipeline from discovery to connection requests.
"""

import asyncio
import json
import time
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, TaskID

# Add the current working directory to Python path for direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.scraping.prospect_discoverer import ProspectDiscoverer
from src.core.browser_manager import BrowserManager
from src.core.session_manager import LinkedInSessionManager as SessionManager
from src.utils.data_model import DataModel
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class DiscoveryWorkflow:
    """Complete discovery and connection workflow."""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.session_manager = SessionManager()
        self.data_model = DataModel()
        self.prospect_discoverer: Optional[ProspectDiscoverer] = None
        self.page = None
        self.browser = None
    
    async def run_complete_workflow(
        self, 
        max_prospects: int = 50, 
        max_connections: int = 9
    ) -> Dict[str, Any]:
        """Run complete workflow: discovery + connection requests."""
        start_time = time.time()
        
        try:
            # Phase 1: Setup browser and session
            console.print("[bold blue]Starting LinkedIn Automation Workflow[/bold blue]")
            await self._setup_browser_and_session()
            
            # Phase 2: Discover prospects
            console.print("[bold yellow]Phase 1: Discovering prospects...[/bold yellow]")
            discovery_summary = await self._run_discovery_phase(max_prospects)
            
            # Phase 3: Send connection requests
            console.print("[bold green]Phase 2: Sending connection requests...[/bold green]")
            connection_summary = await self._run_connection_phase(max_connections)
            
            # Phase 4: Generate final report
            final_summary = await self._generate_final_report(
                discovery_summary, connection_summary, start_time
            )
            
            console.print("[bold green]Workflow completed successfully![/bold green]")
            return final_summary
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            console.print(f"[bold red]Workflow failed: {e}[/bold red]")
            return self._create_error_summary(str(e), start_time)
        
        finally:
            await self._cleanup()
    
    async def _setup_browser_and_session(self):
        """Setup browser and LinkedIn session."""
        console.print("Setting up browser and LinkedIn session...")
        
        # Launch browser
        await self.browser_manager.initialize()
        self.browser = await self.browser_manager._launch_browser()
        self.context = await self.browser_manager.create_context()
        self.page = await self.context.new_page()
        
        # Initialize prospect discoverer
        self.prospect_discoverer = ProspectDiscoverer(self.page)
        
        # Setup LinkedIn session
        cookies = await self.session_manager.load_cookies_from_json()
        await self.context.add_cookies(cookies)
        console.print("Browser and session setup completed")
    
    async def _run_discovery_phase(self, max_prospects: int) -> Dict[str, Any]:
        """Run the prospect discovery phase."""
        console.print(f"Discovering up to {max_prospects} prospects...")
        
        if not self.prospect_discoverer:
            return {"success": False, "error": "Prospect discoverer not initialized"}
        
        prospects = await self.prospect_discoverer.discover_prospects(max_prospects)
        
        # Save prospects to data model
        if prospects:
            self.data_model._save_json_file(self.data_model.prospects_file, prospects)
        
        discovery_summary = {
            'prospects_found': len(prospects),
            'duplicates_found': getattr(self.prospect_discoverer, 'duplicates_found', 0),
            'validation_errors': getattr(self.prospect_discoverer, 'validation_errors', 0),
            'timestamp': time.time()
        }
        
        if prospects:
            console.print(f"Discovery completed: {len(prospects)} prospects found")
        else:
            console.print("Discovery phase failed or returned no prospects")
        
        return discovery_summary
    
    async def _run_connection_phase(self, max_connections: int) -> Dict[str, Any]:
        """Run the connection request phase."""
        try:
            # Import connection manager
            from .connection_manager import ConnectionManager
            from ..ai.message_generator import MessageGenerator
            
            # Initialize components
            message_generator = MessageGenerator("dummy_api_key")
            if self.page:
                connection_manager = ConnectionManager(self.page, message_generator)
            else:
                return {"success": False, "error": "Page not initialized"}
            
            # Load prospects
            prospects = await self.data_model.load_prospects()
            
            if not prospects:
                console.print("No prospects found, skipping connection phase")
                return {"success": False, "message": "No prospects available"}
            
            console.print(f"Sending connection requests to {min(len(prospects), max_connections)} prospects...")
            
            # Send bulk requests
            results = await connection_manager.send_bulk_requests(prospects, max_connections)
            
            # Count successful requests
            successful_requests = sum(1 for result in results if result.get('success', False))
            
            connection_summary = {
                'total_requests': len(results),
                'successful_requests': successful_requests,
                'failed_requests': len(results) - successful_requests,
                'results': results
            }
            
            console.print(f"Connection phase completed: {successful_requests}/{len(results)} successful")
            return connection_summary
            
        except Exception as e:
            logger.error(f"Connection phase failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_final_report(
        self, 
        discovery_summary: Dict[str, Any], 
        connection_summary: Dict[str, Any], 
        start_time: float
    ) -> Dict[str, Any]:
        """Generate final workflow report."""
        execution_time = time.time() - start_time
        
        # Load final prospects data
        final_prospects = await self.data_model.load_prospects()
        
        final_summary = {
            'workflow_completed': True,
            'execution_time': execution_time,
            'discovery_phase': discovery_summary,
            'connection_phase': connection_summary,
            'final_prospects_count': len(final_prospects),
            'timestamp': time.time()
        }
        
        # Save summary
        await self.data_model.save_workflow_summary(final_summary)
        
        # Print summary report
        self._print_summary_report(final_summary)
        
        return final_summary
    
    def _print_summary_report(self, summary: Dict[str, Any]):
        """Print formatted summary report."""
        console.print("\n" + "="*60)
        console.print("[bold]WORKFLOW SUMMARY REPORT[/bold]")
        console.print("="*60)
        
        # Discovery results
        discovery = summary.get('discovery_phase', {})
        console.print(f"Discovery Results:")
        console.print(f"   Prospects found: {discovery.get('prospects_found', 0)}")
        console.print(f"   Duplicates found: {discovery.get('duplicates_found', 0)}")
        console.print(f"   Validation errors: {discovery.get('validation_errors', 0)}")
        
        # Connection results
        connection = summary.get('connection_phase', {})
        console.print(f"\nConnection Results:")
        console.print(f"   Total requests: {connection.get('total_requests', 0)}")
        console.print(f"   Successful: {connection.get('successful_requests', 0)}")
        console.print(f"   Failed: {connection.get('failed_requests', 0)}")
        
        # Final stats
        console.print(f"\nFinal Statistics:")
        console.print(f"   Total prospects in database: {summary.get('final_prospects_count', 0)}")
        console.print(f"   Execution time: {summary.get('execution_time', 0):.1f} seconds")
        
        console.print("="*60)
    
    def _create_error_summary(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Create error summary when workflow fails."""
        execution_time = time.time() - start_time
        
        error_summary = {
            'workflow_completed': False,
            'error_message': error_message,
            'execution_time': execution_time,
            'timestamp': time.time()
        }
        
        # Save error summary
        asyncio.create_task(self.data_model.save_workflow_summary(error_summary))
        
        return error_summary
    
    async def _cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'context') and self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
                console.print("Browser closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def discover_only(self, max_prospects: int = 50) -> Dict[str, Any]:
        """Run only the discovery phase."""
        start_time = time.time()
        
        try:
            console.print("[bold blue]Starting Prospect Discovery Only[/bold blue]")
            
            # Setup browser and session
            await self._setup_browser_and_session()
            
            # Run discovery
            discovery_summary = await self._run_discovery_phase(max_prospects)
            
            execution_time = time.time() - start_time
            
            console.print(f"Discovery completed in {execution_time:.1f} seconds")
            return discovery_summary
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            await self._cleanup()
    
    async def connect_only(self, max_connections: int = 9) -> Dict[str, Any]:
        """Run only the connection phase with existing prospects."""
        start_time = time.time()
        
        try:
            console.print("[bold blue]Starting Connection Requests Only[/bold blue]")
            
            # Setup browser and session
            await self._setup_browser_and_session()
            
            # Run connection phase
            connection_summary = await self._run_connection_phase(max_connections)
            
            execution_time = time.time() - start_time
            
            console.print(f"Connection phase completed in {execution_time:.1f} seconds")
            return connection_summary
            
        except Exception as e:
            logger.error(f"Connection phase failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            await self._cleanup()


async def main():
    """Main entry point for discovery workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Automation Discovery Workflow')
    parser.add_argument('--max-prospects', type=int, default=50, help='Maximum prospects to discover')
    parser.add_argument('--max-connections', type=int, default=9, help='Maximum connection requests to send')
    parser.add_argument('--discover-only', action='store_true', help='Run only discovery phase')
    parser.add_argument('--connect-only', action='store_true', help='Run only connection phase')
    
    args = parser.parse_args()
    
    workflow = DiscoveryWorkflow()
    
    if args.discover_only:
        result = await workflow.discover_only(args.max_prospects)
    elif args.connect_only:
        result = await workflow.connect_only(args.max_connections)
    else:
        result = await workflow.run_complete_workflow(args.max_prospects, args.max_connections)
    
    # Print final result
    if result.get('workflow_completed', False):
        console.print("[bold green]Workflow completed successfully![/bold green]")
    else:
        console.print("[bold red]Workflow failed[/bold red]")
        if 'error' in result:
            console.print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())