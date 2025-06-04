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
    CreateAssetDto, 
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


def create_aasx_asset(edc_manager: EdcManager) -> dict:
    """
    Creates an AASX asset in the EDC using configuration from provider.env.
    
    Returns:
        Dictionary with asset creation results or error information.
    """
    logger.info(f"Creating AASX asset: {settings.ASSET_ID}")
    logger.info(f"Asset URL: {settings.ASSET_URL}")
    logger.info(f"Asset Description: {settings.ASSET_DESCRIPTION}")
    
    # Use the new createAASXAsset method instead of createAsset
    asset_response = edc_manager.createAASXAsset()
    
    if not asset_response:
        return {"error": "Failed to create asset", "asset_id": settings.ASSET_ID}
    
    if asset_response.get("status") == "conflict":
        logger.warning(f"Asset {settings.ASSET_ID} already exists")
        return {"status": "already_exists", "asset_id": settings.ASSET_ID}
    
    if asset_response.get("@id"):
        logger.info(f"Successfully created asset: {settings.ASSET_ID}")
        return {"status": "created", "asset_id": settings.ASSET_ID, "response": asset_response}
    
    return {"error": "Unexpected response", "asset_id": settings.ASSET_ID, "response": asset_response}


def create_policies_and_contract(edc_manager: EdcManager) -> dict:
    """
    Creates access policy, usage policy, and contract definition for the asset.
    
    Returns:
        Dictionary with policy and contract creation results.
    """
    if not settings.CONSUMER_BPN:
        logger.warning("CONSUMER_BPN not set - skipping policy and contract creation")
        return {"warning": "CONSUMER_BPN not configured"}
    
    # Generate unique IDs
    asset_prefix = settings.ASSET_ID[:18] if settings.ASSET_ID else "aasx"
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
            assetId=settings.ASSET_ID
        )
        contract_response = edc_manager.createContractDefinition(contract_dto)
        results["contract_definition_status"] = "success" if contract_response else "failed"
    else:
        results["contract_definition_status"] = "skipped_due_to_policy_failures"
    
    return results


def main(env_file: str = None):
    """
    Main entry point for AASX asset registration.
    
    Args:
        env_file: Optional path to environment file. Defaults to provider.env in script directory.
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
    
    # Validate required settings for AASX asset
    if not all([settings.ASSET_ID, settings.ASSET_URL, settings.ASSET_DESCRIPTION]):
        logger.error("Missing required asset configuration: ASSET_ID, ASSET_URL, or ASSET_DESCRIPTION")
        return False
    
    # Initialize EDC Manager
    try:
        edc_manager = EdcManager()
        logger.info("EDC Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize EDC Manager: {e}")
        return False
    
    # Create asset
    logger.info("=== Creating AASX Asset ===")
    asset_result = create_aasx_asset(edc_manager)
    
    if asset_result.get("error"):
        logger.error(f"Asset creation failed: {asset_result}")
        return False
    
    logger.info(f"Asset creation result: {asset_result}")
    
    # Create policies and contract definition
    logger.info("=== Creating Policies and Contract Definition ===")
    policy_result = create_policies_and_contract(edc_manager)
    logger.info(f"Policy and contract result: {policy_result}")
    
    logger.info("=== AASX Asset Registration Complete ===")
    logger.info(f"Asset ID: {settings.ASSET_ID}")
    logger.info(f"Asset URL: {settings.ASSET_URL}")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register AASX Asset in EDC Dataspace")
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to environment file (defaults to provider.env in script directory)"
    )
    
    args = parser.parse_args()
    success = main(env_file=args.env_file)
    
    if not success:
        exit(1) 