#!/usr/bin/env python3
"""
Local Run Script for LinkedIn Automation

Usage: python run_local.py [prospects_file] [max_requests]
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "automation"))

from workflow import LinkedInAutomationWorkflow


async def main():
    # Parse arguments
    prospects_file = sys.argv[1] if len(sys.argv) > 1 else "prospects_example.json"
    max_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    
    # Load prospects
    if not Path(prospects_file).exists():
        print(f"Prospects file not found: {prospects_file}")
        print("Use: python run_local.py prospects_example.json")
        return
    
    with open(prospects_file, 'r') as f:
        prospects = json.load(f)
    
    print(f"Starting LinkedIn automation with {len(prospects)} prospects")
    print(f"Max requests per session: {max_requests}")
    
    # Run workflow
    workflow = LinkedInAutomationWorkflow()
    result = await workflow.run_workflow(prospects, max_requests)
    
    # Print results
    print(f"\nResults:")
    print(f"   Successful: {result['successful_requests']}/{len(prospects)}")
    print(f"   Failed: {result['failed_requests']}")
    print(f"   Execution time: {result['execution_time']:.2f}s")
    
    if result['errors']:
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"   - {error}")


if __name__ == "__main__":
    asyncio.run(main())
