# Some Ideas for Realising Use Case 1

Story: An IDE user can onboard 3rd party assets like robot, camera etc. via the RoX ecosystem.

The Asset descriptions (here: ready-made aasx files which can be imported into any AAS management environment) should be provided federatedly into the dataspace/ecosystem by a standard, like the Asset Administration Shell (AAS). For the current prototype, we leave the issue of "discovery" (how do I find the business partner + edc connector of the provider) and simply assume that
the solution builder either already knows the provider or is able to contact all of them (see below comment about the federated catalogue).

We end by sketching an intermediate endpoint which operates similar to the federated catalog (with a restriction on ordering the results).

## Registering AASX files (file sources) as annotated EDC/Digital Twin Assets 

The idea is to describe the AASX file (a set of shells, submodels, ...) as individual digital twin EDC assets. If the AASX file contains several shells, we suggest to break it up into individual digital twins as EDC catalogue search over list substructures currently does not work very well (you would have to access the members by their indexes '0', '1', ...).

Here is an example of such an EDC asset description (pointing to a public, non-secured aasx file availble through HTTP) registered via the EDC management API. Notice that we introduce the "aas" namespace and use it to define the top-level of the shell (the part that maybe needed in a search).

```shell
curl --request PUT \
  --url http://localhost:8182/management/v3/assets \
  --header 'content-type: application/json' \
  --data '{
  "@context": {
    "edc": "https://w3id.org/edc/v0.0.1/ns/",
    "dcat": "https://www.w3.org/ns/dcat/",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "dspace": "https://w3id.org/dspace/v0.8/",
    "aas": "https://admin-shell.io/aas/3/0"
  },
  "@id": "ExampleV3",
  "@type": "edc:Asset",
  "edc:properties": {
    "edc:version": "3.0.0",
    "edc:contenttype": "application/asset-administration-shell-package",
    "edc:type": "data.core.digitalTwin",
    "edc:publisher": "IDTA",
    "aas:modelType": "AssetAdministrationShell",
    "aas:id": "https://example.com/ids/sm/2411_7160_0132_4523",
    "aas:iShort": "SecondAAS",
    "aas:assetInformation": {
      "aas:assetKind": "Instance",
      "aas:globalAssetId": "https://htw-berlin.de/ids/asset/1090_7160_0132_8069"
    }
  },
  "edc:dataAddress": {
    "@type": "DataAddress",
    "type": "HttpData",
    "baseUrl": "https://github.com/ShehriyarShariq-Fraunhofer/AAS_Defaults/raw/refs/heads/main/ExampleV3.aasx",
    "proxyQueryParams": "false",
    "proxyPath": "false",
    "proxyMethod": "false",
    "method":"GET"
  }
}'
```

## Searching for AASX resources via EDC

The following is an example call that looks for "compliant" AASX resources from a partner connector. A similar call could be made once several EDCs are federated into one catalogue (this requires an upcoming "federated catalogue" feature of the EDC).

In this example we are searching for the contenttype which determines AASX resources as well as some (nested) meta-data from the shell description. See how the usage of quotes and the dot operator is used to address a field in the aas top-level description associated to the AASX resource.

```shell
curl --request POST \
  --url http://localhost:8181/management/v2/catalog/request \
  --header 'content-type: application/json' \
  --data '{
    "@context": { 
    },
    "protocol": "dataspace-protocol-http",
    "counterPartyAddress": "{{PROVIDER_PROTOCOL_URL}}",
    "counterPartyId": "{{PROVIDER_ID}}",
    "querySpec": {
        "offset": 0,
        "limit": 500,
        "filterExpression": [
          {
           "operandLeft": "https://w3id.org/edc/v0.0.1/ns/contenttype",
           "operator":"=",
           "operandRight":"application/asset-administration-shell-package"
          },
          {
           "operandLeft": "'\''https://admin-shell.io/aas/3/0/assetInformation'\''.'\''https://admin-shell.io/aas/3/0/assetKind'\''",
           "operator":"=",
           "operandRight":"Instance"
          }     
        ]
    }
}'
```

## Policies, Contracts and Transfers

For publishing AASX assets, the usual constraints can be used in usage and access policies. It is best to create these Policies using the Connect & integrate UI, because then it is possible to negotiate and download the aasx files also directly via the frontend.

## A (Simulated) Federated Catalog

Here is an example code for implementing a kind of federated catalog using Python's Flask framework until the connector itself has the ability (comes with C&I 4.0)

It has the restriction that the ordering of the results may not work properly, as we interleave the individual catalogs. For searching a handful of
assets over a range of connectors, this code will serve its purpose.

```python
from flask import Flask, jsonify, request, send_file
import json
import logging
import uuid
import os
import base64
import pathlib
import requests
from datetime import datetime

# Endpoint that behaves as a federated catalog
@app.route('/federated-catalog/query', methods=['POST'])
def query_catalog():
    try:
        query = None
        if 'Content-Type' in request.headers and request.headers['Content-Type']=='application/json':
            query = request.json

        consumer_connector = os.environ['MY_CONNECTOR']
        consumer_bpn = os.environ['MY_BPN']
        consumer_key = os.environ['MY_API_KEY']

        federated_connectors = json.loads(os.environ['FEDERATED_CONNECTORS'])
       
        datasets = []
        offset = query["offset"] if "offset" in query else 0
        limit = query["limit"] if "limit" in query else 50

        query["offset"] = 0
        query["limit"] = offset + limit  # Set a higher limit for the federated query, since we start at 0 
        
        for provider_bpn in federated_connectors:
            provider_connector = federated_connectors[provider_bpn]
            headers = {"content-type": "application/json", "x-api-key": consumer_key}
            catalog_url = f"{consumer_connector}/v2/catalog/request"
            catalog_payload = {
                "@context": { "edc": "https://w3id.org/edc/v0.0.1/ns/" },
                "@type": "CatalogRequest",
                "counterPartyAddress": f"{provider_connector}",
                "counterPartyId": f"{provider_bpn}",
                "protocol": "dataspace-protocol-http",
                "querySpec": query
            }
            try:
                app.logger.info(f"About to fetch catalog from {provider_bpn} at {provider_connector}")
                response = requests.post(catalog_url, json=catalog_payload, headers=headers)
                if response.status_code == 200:
                    datasets.extend(response.json()["dcat:dataset"])
                else:
                    app.logger.warning(f"Failed to fetch catalog from {provider_bpn} at {provider_connector}: {response.status_code} {response.text}")

            except Exception as e:
                app.logger.warn(f"Failed to fetch catalog from {provider_bpn} at {provider_connector}: {str(e)}")

        return jsonify(datasets[offset:offset+limit]), 200

    except Exception as e:
        return jsonify({"error": "Unable to fetch federated catalogues", "message": str(e)}), 500


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=80)
```

This code can be built using below Dockerfile

```Dockerfile
# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the Python dependencies
RUN pip install Flask
RUN pip install requests

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the app
CMD ["python", "app.py"]
```

The code can be deployed using a docker compose file like this

```DockerCompose
services:
  # A web service which plays the role of anything you like
  web-server:
    build: ./resources/web-server
    container_name: web-server
    environment:
      MY_CONNECTOR: http://bob-cp:8181/management
      MY_API_KEY: ApiDefaultKey
      MY_BPN: BPNL000000000002
      FEDERATED_CONNECTORS: '{ "BPNL000000000002":"http://bob-cp:8282/api/v1/dsp", "BPNL000000000001":"http://alice-cp:8282/api/v1/dsp" }'
    ports:
      - "5001:80"
```

Afterwards you may query the new endpoint like this

```shell
curl --request POST \
  --url 'http://web-server/federated-catalog/query' \
  --header 'content-type: application/json' \
  --data '{
    "@context": {
        "edc": "https://w3id.org/edc/v0.0.1/ns/"
    },
    "offset": 0,
    "limit": 50,
    "filterExpression": [
            {
            "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
            "operator": "like",
            "operandRight": "alice%"
        }
    ]
   }'
```


