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