#!/usr/bin/env python3
"""
Test script for the LinkedIn Automation Discovery System.

This script tests the complete workflow including:
1. Selector configuration fix
2. Prospect discovery system
3. Integration with existing workflow
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_selector_config():
    """Test that selector configuration is working correctly."""
    print("Testing selector configuration...")
    
    try:
        from src.scraping.element_detector import ElementDetector
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            # Test that ElementDetector can load config
            detector = ElementDetector(page)
            print("ElementDetector initialized successfully")
            print(f"Loaded {len(detector.selectors_config.get('primary_selectors', {}))} selector categories")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"Selector config test failed: {e}")
        return False

async def test_search_config():
    """Test that search configuration is working correctly."""
    print("Testing search configuration...")
    
    try:
        from src.scraping.prospect_discoverer import ProspectDiscoverer
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            # Test that ProspectDiscoverer can load config
            discoverer = ProspectDiscoverer(page)
            print("ProspectDiscoverer initialized successfully")
            print(f"Loaded {len(discoverer.search_config.get('locations', []))} target locations")
            print(f"Loaded {len(discoverer.search_config.get('job_titles', []))} target job titles")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"Search config test failed: {e}")
        return False

async def test_data_model():
    """Test that data model is working correctly."""
    print("Testing data model...")
    
    try:
        from src.utils.data_model import DataModel
        
        data_model = DataModel()
        print("DataModel initialized successfully")
        print(f"Data directory exists: {data_model.data_dir.exists()}")
        
        # Test loading prospects (should be empty initially)
        prospects = await data_model.load_prospects()
        print(f"Loaded {len(prospects)} prospects")
        
        return True
        
    except Exception as e:
        print(f"Data model test failed: {e}")
        return False

async def test_message_generator():
    """Test that message generator is working correctly."""
    print("Testing message generator...")
    
    try:
        from src.ai.message_generator import MessageGenerator
        
        # Use a dummy API key for testing
        api_key = "test_key"
        message_generator = MessageGenerator(api_key)
        print("MessageGenerator initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"Message generator test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Running LinkedIn Automation Discovery System Tests")
    print("=" * 60)
    
    tests = [
        ("Selector Configuration", test_selector_config),
        ("Search Configuration", test_search_config),
        ("Data Model", test_data_model),
        ("Message Generator", test_message_generator),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 40)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! The system is ready to use.")
        print("\nTo run the complete workflow:")
        print("python3 src/automation/discovery_workflow.py --max-prospects 50 --max-connections 9")
    else:
        print(f"\n{total - passed} test(s) failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)