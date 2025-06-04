#!/usr/bin/env python3
"""
AASX Asset Consumer Script

Clean and lean script for consuming AASX assets from EDC dataspace.
Handles discovery, negotiation, and retrieval of HTTP-based assets without S3 dependencies.
"""

import argparse
import os
import logging
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from consumer.dataspace_client import DataspaceClient
from consumer.uc_controller import UcController
from consumer.config import settings

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_aasx_consumer(asset_id: str = None, env_file: str = None):
    """
    Runs the AASX consumer workflow to discover, negotiate, and retrieve assets.
    
    Args:
        asset_id: ID of the specific asset to retrieve. If None, lists available assets.
        env_file: Path to environment file. Defaults to consumer.env in script directory.
        
    Returns:
        Path to downloaded file if successful, None otherwise.
    """
    logger.info(f"Starting AASX consumer for asset: {asset_id or 'ANY (will list)'}")
    
    # Handle environment file
    if env_file is None:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consumer.env")
    
    env_file_path = os.path.abspath(env_file)
    
    # Load environment
    if os.path.exists(env_file_path):
        logger.info(f"Loading environment from: {env_file_path}")
        load_dotenv(env_file_path, override=True)
    else:
        logger.warning(f"Environment file {env_file_path} not found. Using system environment.")
    
    # Load settings
    try:
        settings.load_from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return None
    
    # Update logging level from settings
    logging.getLogger().setLevel(settings.LOG_LEVEL)
    logger.info(f"Logging configured to level: {settings.LOG_LEVEL}")
    
    # Ensure artifact download directory exists
    os.makedirs(settings.ARTIFACT_DOWNLOAD_PATH, exist_ok=True)
    logger.info(f"Artifact download path: {settings.ARTIFACT_DOWNLOAD_PATH}")
    
    # Initialize client and controller
    try:
        client = DataspaceClient()
        controller = UcController(client=client)
        logger.info("AASX consumer components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize consumer components: {e}")
        return None
    
    # Run the consumer workflow
    logger.info("=== Starting AASX Asset Retrieval Workflow ===")
    
    try:
        retrieved_file_path = controller.run_consumer_workflow(target_asset_id=asset_id)
        
        if retrieved_file_path:
            logger.info(f"✅ AASX asset retrieval successful!")
            logger.info(f"Asset '{asset_id or 'selected'}' downloaded to: {retrieved_file_path}")
            return retrieved_file_path
        else:
            logger.error(f"❌ AASX asset retrieval failed for asset: {asset_id or 'selected'}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error during AASX asset retrieval: {e}")
        return None


def main(asset_id: str = None, env_file: str = None):
    """
    Main entry point for AASX asset consumption.
    
    Args:
        asset_id: Optional asset ID to retrieve. If not provided, lists available assets.
        env_file: Optional path to environment file.
    """
    return run_aasx_consumer(asset_id=asset_id, env_file=env_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consume AASX Assets from EDC Dataspace")
    parser.add_argument(
        "asset_id",
        nargs="?",
        default=None,
        help="Asset ID to retrieve. If not provided, available assets will be listed for selection."
    )
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to environment file (defaults to consumer.env in script directory)"
    )
    
    args = parser.parse_args()
    
    result = main(asset_id=args.asset_id, env_file=args.env_file)
    
    if not result:
        exit(1) 