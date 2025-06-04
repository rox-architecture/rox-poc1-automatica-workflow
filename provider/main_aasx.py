"""
AASX Asset Registration Script

Clean and lean script to register AAS assets in EDC dataspace without any S3 dependencies.
Uses asset configuration from provider.env file to create HTTP-based data assets.
"""

import sys
import os

# Add the parent directory to sys.path to enable absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now use absolute imports
from provider.edcmanager import (
    EdcManager, 
    CreateAccessPolicyDto, 
    CreateUsagePolicyDto,
    CreateContractDefinitionDto
)
from provider.config import settings
import argparse
import uuid
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def setup_logging():
    """Configures basic logging using LOG_LEVEL from settings."""
    log_level = settings.LOG_LEVEL
    
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.getLogger().setLevel(log_level)
    
    logger.info(f"Logging configured to level: {log_level}")


def create_aasx_asset(edc_manager: EdcManager, asset_id: str = None, asset_url: str = None, asset_description: str = None, asset_type: str = None) -> dict:
    """
    Creates an AASX asset in the EDC using configuration from provider.env or CLI parameters.
    
    Args:
        edc_manager: The EDC manager instance
        asset_id: Optional asset ID to override settings.ASSET_ID
        asset_url: Optional asset URL to override settings.ASSET_URL
        asset_description: Optional asset description to override settings.ASSET_DESCRIPTION
        asset_type: Optional asset type ("data", "model", or "service"), defaults to "data"
    
    Returns:
        Dictionary with asset creation results or error information.
    """
    # Use CLI parameters if provided, otherwise fall back to settings
    effective_asset_id = asset_id or settings.ASSET_ID
    effective_asset_url = asset_url or settings.ASSET_URL
    effective_asset_description = asset_description or settings.ASSET_DESCRIPTION
    effective_asset_type = asset_type or "data"  # Default to "data" if not specified
    
    # Validate asset type
    valid_asset_types = ["data", "model", "service"]
    if effective_asset_type not in valid_asset_types:
        logger.error(f"Invalid asset_type '{effective_asset_type}'. Must be one of: {valid_asset_types}")
        return {"error": f"Invalid asset_type '{effective_asset_type}'", "asset_id": effective_asset_id}
    
    logger.info(f"Creating AASX asset: {effective_asset_id}")
    logger.info(f"Asset URL: {effective_asset_url}")
    logger.info(f"Asset Description: {effective_asset_description}")
    logger.info(f"Asset Type: {effective_asset_type}")
    
    # Temporarily override settings for the asset creation
    original_asset_id = settings.ASSET_ID
    original_asset_url = settings.ASSET_URL
    original_asset_description = settings.ASSET_DESCRIPTION
    
    try:
        settings.ASSET_ID = effective_asset_id
        settings.ASSET_URL = effective_asset_url
        settings.ASSET_DESCRIPTION = effective_asset_description
        
        # Use the createAASXAsset method with asset type
        asset_response = edc_manager.createAASXAsset(asset_type=effective_asset_type)
        
        if not asset_response:
            return {"error": "Failed to create asset", "asset_id": effective_asset_id}
        
        if asset_response.get("status") == "conflict":
            logger.warning(f"Asset {effective_asset_id} already exists")
            return {"status": "already_exists", "asset_id": effective_asset_id}
        
        if asset_response.get("@id"):
            logger.info(f"Successfully created asset: {effective_asset_id}")
            return {"status": "created", "asset_id": effective_asset_id, "response": asset_response}
        
        return {"error": "Unexpected response", "asset_id": effective_asset_id, "response": asset_response}
    
    finally:
        # Restore original settings
        settings.ASSET_ID = original_asset_id
        settings.ASSET_URL = original_asset_url
        settings.ASSET_DESCRIPTION = original_asset_description


def create_policies_and_contract(edc_manager: EdcManager, asset_id: str = None) -> dict:
    """
    Creates access policy, usage policy, and contract definition for the asset.
    
    Args:
        edc_manager: The EDC manager instance
        asset_id: Optional asset ID to use for policy creation
    
    Returns:
        Dictionary with policy and contract creation results.
    """
    if not settings.CONSUMER_BPN:
        logger.warning("CONSUMER_BPN not set - skipping policy and contract creation")
        return {"warning": "CONSUMER_BPN not configured"}
    
    # Use provided asset_id or fall back to settings
    effective_asset_id = asset_id or settings.ASSET_ID
    
    # Generate unique IDs
    asset_prefix = effective_asset_id[:18] if effective_asset_id else "aasx"
    unique_suffix = str(uuid.uuid4())[:8]
    
    access_policy_id = f"ap-{asset_prefix}-{unique_suffix}"
    usage_policy_id = f"up-{asset_prefix}-{unique_suffix}"
    contract_definition_id = f"cd-{asset_prefix}-{unique_suffix}"
    
    results = {
        "access_policy_id": access_policy_id,
        "usage_policy_id": usage_policy_id,
        "contract_definition_id": contract_definition_id
    }
    
    # Create Access Policy
    logger.info(f"Creating access policy: {access_policy_id}")
    access_policy_dto = CreateAccessPolicyDto(
        accessPolicyId=access_policy_id,
        bpn=settings.CONSUMER_BPN
    )
    access_response = edc_manager.createAccessPolicy(access_policy_dto)
    results["access_policy_status"] = "success" if access_response else "failed"
    
    # Create Usage Policy
    logger.info(f"Creating usage policy: {usage_policy_id}")
    usage_policy_dto = CreateUsagePolicyDto(
        usagePolicyId=usage_policy_id,
        bpn=settings.CONSUMER_BPN
    )
    usage_response = edc_manager.createUsagePolicy(usage_policy_dto)
    results["usage_policy_status"] = "success" if usage_response else "failed"
    
    # Create Contract Definition
    if access_response and usage_response:
        logger.info(f"Creating contract definition: {contract_definition_id}")
        contract_dto = CreateContractDefinitionDto(
            contractDefinitionId=contract_definition_id,
            accessPolicyId=access_policy_id,
            usagePolicyId=usage_policy_id,
            assetId=effective_asset_id
        )
        contract_response = edc_manager.createContractDefinition(contract_dto)
        results["contract_definition_status"] = "success" if contract_response else "failed"
    else:
        results["contract_definition_status"] = "skipped_due_to_policy_failures"
    
    return results


def main(env_file: str = None, asset_id: str = None, asset_url: str = None, asset_description: str = None, asset_type: str = None):
    """
    Main entry point for AASX asset registration.
    
    Args:
        env_file: Optional path to environment file. Defaults to provider.env in script directory.
        asset_id: Optional asset ID to override settings.ASSET_ID
        asset_url: Optional asset URL to override settings.ASSET_URL
        asset_description: Optional asset description to override settings.ASSET_DESCRIPTION
        asset_type: Optional asset type ("data", "model", or "service"), defaults to "data"
    """
    
    # Handle environment file
    if env_file is None:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "provider.env")
    
    env_file_path = os.path.abspath(env_file)
    
    # Load environment
    if os.path.exists(env_file_path):
        print(f"INFO: Loading environment from: {env_file_path}")
        load_dotenv(env_file_path, override=True)
    else:
        print(f"CRITICAL: Environment file not found at {env_file_path}. Exiting.")
        return False
    
    # Load settings
    try:
        settings.load_from_env()
    except ValueError as e:
        print(f"CRITICAL: Configuration error: {e}")
        return False
    
    # Setup logging
    setup_logging()
    logger.info(f"Successfully loaded environment from: {env_file_path}")
    
    # Determine effective values (CLI parameters override settings)
    effective_asset_id = asset_id or settings.ASSET_ID
    effective_asset_url = asset_url or settings.ASSET_URL
    effective_asset_description = asset_description or settings.ASSET_DESCRIPTION
    effective_asset_type = asset_type or "data"
    
    # Validate required settings for AASX asset
    if not all([effective_asset_id, effective_asset_url, effective_asset_description]):
        logger.error("Missing required asset configuration: ASSET_ID, ASSET_URL, or ASSET_DESCRIPTION")
        logger.error("Please provide these via CLI arguments or in the environment file")
        return False
    
    # Log what values are being used
    if asset_id:
        logger.info(f"Using ASSET_ID from CLI: {effective_asset_id}")
    if asset_url:
        logger.info(f"Using ASSET_URL from CLI: {effective_asset_url}")
    if asset_description:
        logger.info(f"Using ASSET_DESCRIPTION from CLI: {effective_asset_description}")
    if asset_type:
        logger.info(f"Using ASSET_TYPE from CLI: {effective_asset_type}")
    else:
        logger.info(f"Using default ASSET_TYPE: {effective_asset_type}")
    
    # Initialize EDC Manager
    try:
        edc_manager = EdcManager()
        logger.info("EDC Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize EDC Manager: {e}")
        return False
    
    # Create asset
    logger.info("=== Creating AASX Asset ===")
    asset_result = create_aasx_asset(edc_manager, effective_asset_id, effective_asset_url, effective_asset_description, effective_asset_type)
    
    if asset_result.get("error"):
        logger.error(f"Asset creation failed: {asset_result}")
        return False
    
    logger.info(f"Asset creation result: {asset_result}")
    
    # Create policies and contract definition
    logger.info("=== Creating Policies and Contract Definition ===")
    policy_result = create_policies_and_contract(edc_manager, effective_asset_id)
    logger.info(f"Policy and contract result: {policy_result}")
    
    logger.info("=== AASX Asset Registration Complete ===")
    logger.info(f"Asset ID: {effective_asset_id}")
    logger.info(f"Asset URL: {effective_asset_url}")
    logger.info(f"Asset Type: {effective_asset_type}")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register AASX Asset in EDC Dataspace")
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to environment file (defaults to provider.env in script directory)"
    )
    parser.add_argument(
        "--asset-id",
        type=str,
        help="Asset ID (overrides ASSET_ID from env file)"
    )
    parser.add_argument(
        "--asset-url",
        type=str,
        help="Asset URL (overrides ASSET_URL from env file)"
    )
    parser.add_argument(
        "--asset-description",
        type=str,
        help="Asset description (overrides ASSET_DESCRIPTION from env file)"
    )
    parser.add_argument(
        "--asset-type",
        type=str,
        choices=["data", "model", "service"],
        default="data",
        help="Asset type: data, model, or service (default: data)"
    )
    
    args = parser.parse_args()
    success = main(
        env_file=args.env_file,
        asset_id=args.asset_id,
        asset_url=args.asset_url,
        asset_description=args.asset_description,
        asset_type=args.asset_type
    )
    
    if not success:
        exit(1) 