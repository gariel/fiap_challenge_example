import os
import requests
import json
import time
import ast

def get_access_token(account_slug, client_id, client_key):
    url = f"https://idm.stackspot.com/{account_slug}/oidc/oauth/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': client_id,
        'grant_type': 'client_credentials',
        'client_secret': client_key
    }
    print("POST", url)
    response = requests.post(url, headers=headers, data=data)
    return response.json()['access_token']

def create_rqc_execution(qc_slug, access_token, input_data):
    url = f"https://genai-code-buddy-api.stackspot.com/v1/quick-commands/create-execution/{qc_slug}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    data = {'input_data': input_data}
    print("POST", url)
    response = requests.post(url, headers=headers, json=data)
    return response.content.decode('utf-8').strip('"')

def get_execution_status(execution_id, access_token):
    url = f"https://genai-code-buddy-api.stackspot.com/v1/quick-commands/callback/{execution_id}"
    headers = {'Authorization': f'Bearer {access_token}'}
    i = 0
    while True:
        print("GET", url)
        response = requests.get(url, headers=headers)
        response_data = response.json()
        status = response_data['progress']['status']
        if status in ['COMPLETED', 'FAILED']:
            return response_data
        i += 1
        time.sleep(5)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_KEY = os.getenv("CLIENT_KEY")
ACCOUNT_SLUG = os.getenv("CLIENT_REALM")
QC_SLUG = os.getenv("QC_SLUG")
CHANGED_FILES = os.getenv("CHANGED_FILES")

print(f'Files to analyze: {CHANGED_FILES}')
CHANGED_FILES = CHANGED_FILES.split(" ")

for file_path in CHANGED_FILES:
    print(f'File Path: {file_path}')

    with open(file_path, 'r') as file:
        file_content = file.read()

    access_token = get_access_token(ACCOUNT_SLUG, CLIENT_ID, CLIENT_KEY)
    execution_id = create_rqc_execution(QC_SLUG, access_token, file_content)
    execution_status = get_execution_status(execution_id, access_token)
    result = execution_status['result']

    if result.startswith("```"):
        result = result[7:-4].strip()

    try:
        result_data = json.loads(result)

        vulnerabilities_amount = len(result_data)
        print(f"{vulnerabilities_amount} item(s) have been found for file {file_path}:")

        for item in result_data:
            print(f"Title: {item['title']}")
            print(f"Severity: {item['severity']}")
            print(f"Correction: {item['correction']}")
            print(f"Lines: {item['lines']}")

    except Exception as e:
        print("Error loading data:", e)
        print("Returned raw values:", result)

