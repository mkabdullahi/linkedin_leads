"""
Data model for LinkedIn Automation.

Handles data persistence for prospects, sent requests, failed requests,
and workflow summaries.
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class DataModel:
    """Data model for managing LinkedIn automation data."""
    
    def __init__(self):
        self.data_dir = Path(".data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.prospects_file = self.data_dir / "prospects.json"
        self.sent_requests_file = self.data_dir / "sent_requests.json"
        self.failed_requests_file = self.data_dir / "failed_requests.json"
        self.workflow_summary_file = self.data_dir / "workflow_summary.json"
    
    async def save_sent_request(self, result: Dict[str, Any]):
        """Save a successful connection request."""
        try:
            # Load existing data
            data = self._load_json_file(self.sent_requests_file, [])
            
            # Add new result
            result_with_timestamp = {
                **result,
                'timestamp': time.time()
            }
            data.append(result_with_timestamp)
            
            # Save updated data
            self._save_json_file(self.sent_requests_file, data)
            logger.info(f"Saved sent request for {result.get('profile_url', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to save sent request: {e}")
    
    async def save_failed_request(self, result: Dict[str, Any]):
        """Save a failed connection request."""
        try:
            # Load existing data
            data = self._load_json_file(self.failed_requests_file, [])
            
            # Add new result
            result_with_timestamp = {
                **result,
                'timestamp': time.time()
            }
            data.append(result_with_timestamp)
            
            # Save updated data
            self._save_json_file(self.failed_requests_file, data)
            logger.info(f"Saved failed request for {result.get('profile_url', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to save failed request: {e}")
    
    async def save_workflow_summary(self, summary: Dict[str, Any]):
        """Save workflow execution summary."""
        try:
            # Load existing data
            data = self._load_json_file(self.workflow_summary_file, [])
            
            # Add new summary
            data.append(summary)
            
            # Save updated data
            self._save_json_file(self.workflow_summary_file, data)
            logger.info("Saved workflow summary")
            
        except Exception as e:
            logger.error(f"Failed to save workflow summary: {e}")
    
    async def load_prospects(self) -> List[Dict[str, Any]]:
        """Load prospects from file."""
        try:
            if self.prospects_file.exists():
                return self._load_json_file(self.prospects_file, [])
            else:
                logger.warning("Prospects file not found")
                return []
        except Exception as e:
            logger.error(f"Failed to load prospects: {e}")
            return []
    
    async def validate_setup(self) -> bool:
        """Validate that the data model is properly set up."""
        try:
            # Check if data directory exists
            if not self.data_dir.exists():
                logger.error("Data directory does not exist")
                return False
            
            # Check if prospects file exists and has content
            if not self.prospects_file.exists():
                logger.warning("Prospects file not found")
                return False
            
            prospects = await self.load_prospects()
            if not prospects:
                logger.warning("No prospects found in prospects file")
                return False
            
            logger.info("Data model validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Data model validation failed: {e}")
            return False
    
    def _load_json_file(self, file_path: Path, default: Any) -> Any:
        """Load JSON data from file with default fallback."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return default
    
    def _save_json_file(self, file_path: Path, data: Any):
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")