import sys
import os

# Add project root to sys.path to allow for absolute-like imports from subdirectories
# if __init__.py files are present in them.
# This assumes test_both.py is in the project root.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Updated imports to use __init__.py entrypoints
from provider import run_provider_main, run_aasx_main
# from consumer import run_consumer_main

if __name__ == "__main__":

    print("\n--- Starting Test ---")
    
    # Ask user which test to run
    print("Choose test type:")
    print("1. Provider with S3 (PoC 3)")
    print("2. AASX Asset Registration (no S3)")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice in ["1", "3"]:
        asset_id_input = input("Define asset_id for UC3 (e.g., test-asset-123): ")
        print(f"Running Provider UC3 with asset_id: {asset_id_input}")
        run_provider_main(asset_id=asset_id_input, env_file="provider/provider.env")
    
    if choice in ["2", "3"]:
        print("\n=== AASX Asset Configuration ===")
        
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
    
    if choice not in ["1", "2", "3"]:
        print("Invalid choice. Please run again and select 1, 2, or 3.")
    
    print("--- Test Finished ---")



