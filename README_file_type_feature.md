# File Type Feature Implementation

## Overview

This document describes the implementation of the file type feature that allows users to specify and automatically handle different file formats when working with assets in the EDC dataspace.

## Changes Made

### Provider Side (edcmanager.py)

1. **Modified `createAASXAsset` method signature:**
   - Added `file_type: str = "aasx"` parameter
   - Added validation for the file_type parameter
   - Added `"rox:assetFileType": file_type` to the asset properties

2. **Example of asset properties with file type:**
   ```json
   "edc:properties": {
       "edc:version": "3.0.0",
       "edc:contenttype": "application/asset-administration-shell-package",
       "edc:type": "data.core.digitalTwin",
       "edc:publisher": "IDTA",
       "edc:description": "Asset description",
       "rox:assetType": "data",
       "rox:assetFileType": "aasx",
       ...
   }
   ```

### Consumer Side (dataspace_client.py)

1. **Modified `access_data` method signature:**
   - Added `asset_file_type: str = None` parameter
   - Updated filename generation logic to use the file type

2. **Enhanced filename generation:**
   - If no filename from Content-Disposition and `asset_file_type` is provided, uses it for extension
   - Fallback filename generation also uses the file type: `download_{timestamp}.{file_type}`
   - Cleans file type by removing leading dots and converting to lowercase

### Consumer Side (uc_controller.py)

1. **Modified `_extract_asset_and_policy_from_dataset` method:**
   - Now returns `(asset_id, full_policy_object, file_type)` tuple
   - Extracts `rox:assetFileType` from `edc:properties`
   - Logs file type extraction for debugging

2. **Updated `run_consumer_workflow` method:**
   - Handles the additional file_type return value
   - Passes file_type to `access_data` method

### Provider Main Script (main_aasx.py)

1. **Updated functions to support file_type:**
   - `create_aasx_asset` function now accepts `file_type` parameter
   - `main` function updated with file_type support
   - Added `--file-type` command line argument

### Test Script (test_asset_explore.py)

1. **Added file_type prompts:**
   - Users can now specify file type when using custom parameters
   - Passes file_type to the provider registration functions

## Usage Examples

### Provider - Creating an Asset with File Type

```python
from provider.edcmanager import EdcManager

edc_manager = EdcManager()

# Create an AASX asset with specific file type
response = edc_manager.createAASXAsset(
    asset_type="data", 
    file_type="aasx"
)

# Create a JSON asset
response = edc_manager.createAASXAsset(
    asset_type="data", 
    file_type="json"
)
```

### Provider - Command Line Usage

```bash
python provider/main_aasx.py \
    --asset-id my-asset-123 \
    --asset-url https://example.com/my-asset.json \
    --asset-description "My JSON Asset" \
    --asset-type data \
    --file-type json
```

### Consumer - Automatic File Type Detection

The consumer automatically extracts the file type from the asset properties and uses it when downloading:

```python
from consumer.dataspace_client import DataspaceClient
from consumer.uc_controller import UcController

client = DataspaceClient()
controller = UcController(client)

# The workflow automatically detects file type and downloads with correct extension
file_path = controller.run_consumer_workflow("my-asset-123")
# Results in: downloaded_data.json (instead of downloaded_data.dat)
```

## File Type Handling Logic

1. **Provider stores file type** in asset properties as `rox:assetFileType`
2. **Consumer extracts file type** from catalog response
3. **Download filename determination** (in order of priority):
   - Filename from HTTP Content-Disposition header
   - `downloaded_data.{file_type}` if file_type is available
   - `downloaded_data.dat` as fallback

4. **File type cleaning:**
   - Converts to lowercase
   - Removes leading dots
   - Uses for file extension

## Supported File Types

The system supports any string as a file type, but common examples include:
- `aasx` (Asset Administration Shell Package)
- `json` (JSON files)
- `xml` (XML files)
- `csv` (CSV files)
- `pdf` (PDF documents)
- `zip` (ZIP archives)

## Backward Compatibility

- Default file type is `"aasx"` to maintain compatibility
- Existing assets without `rox:assetFileType` will use default behavior
- Consumer gracefully handles missing file type information

## Error Handling

- Provider validates file_type is a non-empty string
- Consumer handles missing file type gracefully with debug logging
- File type extraction failures don't break the workflow 