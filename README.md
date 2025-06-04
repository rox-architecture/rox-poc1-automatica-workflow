# Dataspace EDC Asset Exchange: A Practical Demonstration

This project provides a hands-on example of a secure and sovereign data exchange using **Eclipse Dataspace Connector (EDC)** components. It showcases a complete end-to-end workflow where a **Provider** makes a data asset available, and a **Consumer** discovers, negotiates access, and retrieves that asset. This is a fundamental pattern in building data spaces where organizations can share data under their own terms and control.

## The Big Picture: What is this Repository For?

Imagine two organizations that want to exchange data without losing control over it. This repository demonstrates how they can achieve this:

1.  **Provider's Role**:
    *   **Owns Data**: The Provider has a piece of data (e.g., a file in an S3 bucket or an HTTP-accessible resource) they are willing to share.
    *   **Defines Access Rules**: They don't want to give it away freely. Using their EDC, the Provider creates:
        *   An **Asset**: A digital representation of the data (e.g., "My Cool Dataset" or "AI Model").
        *   A **Policy**: Rules that govern how the asset can be used (e.g., "Can only be used for non-commercial purposes," or "Access granted only to BPN XYZ").
        *   A **Contract Definition**: Links the asset to the policy, making it offerable to potential consumers.
    *   **Registers with EDC**: All these definitions are registered with the Provider's EDC instance, making the asset discoverable.

2.  **Consumer's Role**:
    *   **Needs Data**: The Consumer is interested in the data asset offered by the Provider.
    *   **Discovers the Asset**: The Consumer's EDC queries the Provider's EDC (via its public catalog) to find available assets.
    *   **Negotiates Access**: Once the desired asset is found, the Consumer's EDC initiates a contract negotiation with the Provider's EDC. This involves:
        *   The Consumer presenting its identity (e.g., its Business Partner Number - BPN).
        *   The Provider's EDC evaluating if the Consumer meets the policy requirements.
    *   **Receives an Endpoint Data Reference (EDR)**: If the negotiation is successful, the Provider's EDC issues an EDR. This EDR is a secure token that contains the actual information on how to access the data (e.g., temporary credentials for the S3 bucket or HTTP endpoint).
    *   **Accesses Data**: The Consumer uses the EDR to directly access the data from its source (e.g., downloads the file from S3 or HTTP endpoint). The data transfer happens directly between the Consumer and the data source, not necessarily through the EDCs themselves after the EDR is issued.

3.  **EDC's Magic**:
    *   The EDC connectors on both sides handle the complex interactions of asset advertisement, policy enforcement, contract negotiation, and secure EDR exchange.
    *   This ensures that data is shared only according to the Provider's terms and that both parties have a trusted mechanism for interaction.

This repository provides Python scripts that automate these roles, allowing you to simulate this entire process locally or in a test environment.

## Core Concepts Explained

- **Provider (`provider/`)**:
    - Manages the creation and registration of data assets within its EDC.
    - Defines usage policies and contract definitions that govern access to these assets.
    - Supports two types of asset creation:
        - **S3-based assets**: Interacts with Object Storage systems (like S3) where the actual data resides.
        - **HTTP-based AASX assets**: Registers assets that point to HTTP-accessible resources (like AAS files).
- **Consumer (`consumer/`)**:
    - Queries the Provider's EDC catalog to discover available data assets.
    - Initiates and manages contract negotiations for desired assets.
    - Once a contract is agreed and an EDR is received, it uses the EDR to fetch the data from the Provider's storage.
- **EDC Connector (Implicit)**:
    - While not explicitly part of this codebase (you'd run separate EDC instances), these scripts interact with the Management APIs of both the Provider's and Consumer's EDC connectors.
    - These connectors are the backbone, enabling sovereign data sharing through standardized dataspace protocols (e.g., IDS, Dataspace Protocol).
- **`.env` Files**:
    - Crucial for configuring the applications. They store:
        - EDC Management API endpoints (e.g., `http://localhost:19193/management`).
        - API keys for authenticating with the EDC Management APIs.
        - Business Partner Numbers (BPNs) for identifying the Provider and Consumer.
        - Details for connecting to object storage (e.g., S3 bucket names, regions, credentials).
        - Asset configuration (ID, URL, description) for AASX assets.
        - Other environment-specific settings.
- **Endpoint Data Reference (EDR)**:
    - A key piece of information securely transferred from the Provider's EDC to the Consumer's EDC after a successful contract negotiation.
    - Contains the necessary details (e.g., endpoint URL, authorization token) for the Consumer to access the actual data asset directly from its storage location. The EDR is typically short-lived.

## Prerequisites

- Python 3.8+
- `pip` (Python package installer) or `uv` (recommended for faster dependency management)
- `venv` (Python virtual environment tool, usually included with Python)
- **Two running EDC instances**: One configured as the Provider and one as the Consumer. This project *does not* include the EDC setup itself. You are expected to have these running and accessible.
    - You will need their respective Management API endpoints and API keys.

## Setup & Configuration

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url> rox-edc-asset-exchange
    cd rox-edc-asset-exchange
    ```

2.  **Create and Activate a Virtual Environment** (if not using uv):
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    (On Windows, activation is typically `venv\\Scripts\\activate`)

3.  **Install Dependencies**:
    With uv (recommended):
    ```bash
    uv sync
    ```
    Or with pip:
    ```bash
    pip install -r combined_requirements.txt
    ```

4.  **Configure Environment Files (`.env`)**:
    Template environment files (`provider.env.example` and `consumer.env.example`) are provided. **You must copy these and fill in your specific details.**

    *   **For the Provider**:
        ```bash
        cp provider/provider.env.example provider/provider.env
        ```
        Now, edit `provider/provider.env`. Key settings include:
        - `BASE_URL`: Management API of the Provider's EDC (without `/data` suffix).
        - `API_KEY`: API key for the Provider's EDC.
        - `PROVIDER_BPN`: Business Partner Number of the Provider.
        - `CONSUMER_BPN`: Business Partner Number of the Consumer (for policy creation).
        - `ASSET_ID`, `ASSET_URL`, `ASSET_DESCRIPTION`: Configuration for AASX assets.
        - `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `DEFAULT_BUCKET_NAME`, `S3_REGION`: Details for S3-based assets (optional for AASX-only usage).

    *   **For the Consumer**:
        ```bash
        cp consumer/consumer.env.example consumer/consumer.env
        ```
        Edit `consumer/consumer.env`. Key settings include:
        - `CONSUMER_EDC_BASE_URL`: Management API of the Consumer's EDC.
        - `CONSUMER_EDC_API_KEY`: API key for the Consumer's EDC.
        - `CONSUMER_BPN`: Business Partner Number of the Consumer.
        - `PROVIDER_IDS_ENDPOINT`: IDS/DSP protocol endpoint of the Provider's EDC (used for discovery and negotiation).

    **Important Security Note**:
    Do **NOT** commit your actual `.env` files (containing sensitive credentials) to version control. The `.gitignore` file is configured to ignore `*.env` files, but always double-check.

## How to Run

### Provider Component

The Provider offers two main scripts for different asset types:

#### S3-Based Assets (`provider/main.py`)

For creating assets that point to S3 storage:

```bash
# Ensure your virtual environment is active and provider.env is correctly configured
cd provider

# Example: Create an asset with ID "my-test-asset-1"
python3 main.py my-test-asset-1

# With uv:
uv run python main.py my-test-asset-1

# To use a specific .env file:
# python3 main.py my-test-asset-1 --env-file /path/to/your/custom_provider.env
cd ..
```

#### AASX Assets (`provider/main_aasx.py`) - **New!**

For creating HTTP-based assets (like AAS files) without S3 dependencies:

```bash
# Use default configuration from provider.env
uv run provider/main_aasx.py

# Use default type (data) with custom parameters
uv run provider/main_aasx.py --asset-id "my-asset" --asset-url "https://example.com/asset.aasx"

# Specify asset type as model
uv run provider/main_aasx.py \
  --asset-id "my-model-asset" \
  --asset-url "https://example.com/model.aasx" \
  --asset-description "My AI Model" \
  --asset-type "model"

# Service type asset
uv run provider/main_aasx.py \
  --asset-id "my-service" \
  --asset-type "service" \
  --asset-description "My Service Endpoint"

# Batch asset creation - you can run multiple commands to register different assets:
uv run provider/main_aasx.py --asset-id "dataset-1" --asset-type "data" --asset-url "https://data.example.com/dataset1.aasx"
uv run provider/main_aasx.py --asset-id "ai-model-v2" --asset-type "model" --asset-url "https://models.example.com/v2.aasx"
uv run provider/main_aasx.py --asset-id "inference-api" --asset-type "service" --asset-url "https://api.example.com/inference"
```

**AASX Asset Types:**
- `data`: For datasets and data assets (default)
- `model`: For AI/ML models and computational assets
- `service`: For service endpoints and APIs

**AASX CLI Parameters:**
- `--asset-id`: Unique identifier for the asset
- `--asset-url`: HTTP URL where the asset can be accessed
- `--asset-description`: Human-readable description of the asset
- `--asset-type`: Type of asset (data/model/service)
- `--env-file`: Custom environment file path

The AASX script will interact with your Provider EDC's Management API to:
1.  Create an Asset entity with HTTP data address.
2.  Create Policy Definitions for the specified consumer BPN.
3.  Create a Contract Definition, linking the Asset to the Policies.

### Consumer Component

The Consumer script (`consumer/main.py`) attempts to discover the asset from the provider, negotiate a contract, and then (if successful) use the EDR to fetch data.

```bash
# Ensure your virtual environment is active and consumer.env is correctly configured
cd consumer

# Example: Consume the asset with ID "my-test-asset-1" from the configured Provider
python3 main.py my-test-asset-1

# With uv:
uv run python main.py my-test-asset-1

# To use a specific .env file:
# python3 main.py my-test-asset-1 --env-file /path/to/your/custom_consumer.env
cd ..
```

The script will:
1.  Query the Provider's IDS/DSP endpoint to get its catalog of assets.
2.  Find the specified `asset_id`.
3.  Initiate a contract negotiation process.
4.  Poll for the EDR (Endpoint Data Reference).
5.  If an EDR is obtained, it will attempt to use it to fetch the data.

## End-to-End Test (`test_both.py`)

A script `test_both.py` is provided in the project root to demonstrate the full flow with multiple options:

```bash
# Ensure your virtual environment is active and BOTH .env files are configured
uv run test_both.py
```

This script will:
1.  Prompt you to choose between:
    - **Option 1**: S3-based asset creation (traditional UC3)
    - **Option 2**: AASX asset registration (HTTP-based, no S3)
    - **Option 3**: Both options
2.  For AASX assets, offer the choice to use custom parameters or environment file values.
3.  Run the appropriate Provider script to create and register assets.
4.  Optionally run the Consumer script to discover, negotiate, and retrieve assets.

This is the best way to quickly test if your EDC setup and environment configurations are working correctly for different types of data exchange.

## Key Files and Directory Structure

```