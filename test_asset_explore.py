import sys
import os
import time

# Add project root to sys.path to allow for absolute-like imports from subdirectories
# if __init__.py files are present in them.
# This assumes test_both.py is in the project root.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Updated imports to use __init__.py entrypoints
from provider import run_provider_main, run_aasx_main
from consumer import run_consumer_main, run_aasx_consumer

if __name__ == "__main__":

    print("\n--- Starting Test ---")
    
    # Ask user which test to run
    print("Choose test type:")
    print("1. Provider with S3 (PoC 3)")
    print("2. AASX Asset Registration (no S3)")
    print("3. AASX End-to-End (Provider + Consumer)")
    print("4. All tests")
    
    choice = input("Enter choice (1/2/3/4): ").strip()
    
    # S3-based provider test
    if choice in ["1", "4"]:
        asset_id_input = input("Define asset_id for UC3 (e.g., test-asset-123): ")
        print(f"Running Provider UC3 with asset_id: {asset_id_input}")
        run_provider_main(asset_id=asset_id_input, env_file="provider/provider.env")
    
    # AASX provider registration only
    if choice == "2":
        print("\n=== AASX Asset Registration (Provider Only) ===")
        
        # Ask if user wants to use environment file values or provide custom ones
        use_custom = input("Use custom asset parameters? (y/n, default: n): ").strip().lower()
        
        asset_id = None
        asset_url = None
        asset_description = None
        asset_type = None
        
        if use_custom == 'y':
            print("Enter custom asset parameters (press Enter to use default value):")
            
            asset_id_input = input("Asset ID: ").strip()
            if asset_id_input:
                asset_id = asset_id_input
            
            asset_url_input = input("Asset URL: ").strip()
            if asset_url_input:
                asset_url = asset_url_input
            
            asset_description_input = input("Asset Description: ").strip()
            if asset_description_input:
                asset_description = asset_description_input
            
            print("Asset Type options: data, model, service")
            asset_type_input = input("Asset Type (default: data): ").strip().lower()
            if asset_type_input and asset_type_input in ["data", "model", "service"]:
                asset_type = asset_type_input
            elif asset_type_input and asset_type_input not in ["data", "model", "service"]:
                print(f"Invalid asset type '{asset_type_input}'. Using default 'data'.")
                asset_type = "data"
        
        print("Running AASX Asset Registration...")
        success = run_aasx_main(
            env_file="provider/provider.env",
            asset_id=asset_id,
            asset_url=asset_url,
            asset_description=asset_description,
            asset_type=asset_type
        )
        
        if success:
            print("✅ AASX Asset Registration completed successfully")
        else:
            print("❌ AASX Asset Registration failed")
    
    # AASX end-to-end test (provider + consumer)
    if choice in ["3", "4"]:
        print("\n=== AASX End-to-End Test (Provider + Consumer) ===")
        
        # Get asset configuration
        use_custom = input("Use custom asset parameters? (y/n, default: n): ").strip().lower()
        
        asset_id = None
        asset_url = None
        asset_description = None
        asset_type = None
        
        if use_custom == 'y':
            print("Enter custom asset parameters (press Enter to use default value):")
            
            asset_id_input = input("Asset ID: ").strip()
            if asset_id_input:
                asset_id = asset_id_input
            
            asset_url_input = input("Asset URL: ").strip()
            if asset_url_input:
                asset_url = asset_url_input
            
            asset_description_input = input("Asset Description: ").strip()
            if asset_description_input:
                asset_description = asset_description_input
            
            print("Asset Type options: data, model, service")
            asset_type_input = input("Asset Type (default: data): ").strip().lower()
            if asset_type_input and asset_type_input in ["data", "model", "service"]:
                asset_type = asset_type_input
            elif asset_type_input and asset_type_input not in ["data", "model", "service"]:
                print(f"Invalid asset type '{asset_type_input}'. Using default 'data'.")
                asset_type = "data"
        
        # Step 1: Register AASX asset
        print("\n--- Step 1: Registering AASX Asset ---")
        provider_success = run_aasx_main(
            env_file="provider/provider.env",
            asset_id=asset_id,
            asset_url=asset_url,
            asset_description=asset_description,
            asset_type=asset_type
        )
        
        if not provider_success:
            print("❌ AASX Asset Registration failed. Skipping consumer test.")
        else:
            print("✅ AASX Asset Registration completed successfully")
            
            # Determine the asset ID for consumer
            consumer_asset_id = asset_id
            if not consumer_asset_id:
                # Ask user for asset ID if not provided
                consumer_asset_id = input("\nEnter the asset ID to consume (or press Enter to browse): ").strip()
                if not consumer_asset_id:
                    consumer_asset_id = None  # Will trigger asset listing in consumer
            
            # Step 2: Consume the asset
            print(f"\n--- Step 2: Consuming AASX Asset '{consumer_asset_id or 'to be selected'}' ---")
            print("Waiting 3 seconds for asset to be available...")
            time.sleep(3)
            
            consumer_result = run_aasx_consumer(
                asset_id=consumer_asset_id,
                env_file="consumer/consumer.env"
            )
            
            if consumer_result:
                print(f"✅ AASX End-to-End test completed successfully!")
                print(f"Asset downloaded to: {consumer_result}")
            else:
                print("❌ AASX Asset consumption failed")
    
    if choice not in ["1", "2", "3", "4"]:
        print("Invalid choice. Please run again and select 1, 2, 3, or 4.")
    
    print("--- Test Finished ---")



