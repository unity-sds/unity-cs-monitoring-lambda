import requests
import os
import boto3
import json
# 
# Retrieve environment variables



cog_user = os.getenv('COG_USER')
cog_pass = os.getenv('COG_PASS')
cog_client_id = os.getenv('COG_CLIENT_ID')

# Create a Cognito client
client = boto3.client('cognito-idp')
response = client.initiate_auth(
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': cog_user,
        'PASSWORD': cog_pass,
    },
    ClientId=cog_client_id
)
token = response['AuthenticationResult']['AccessToken']
# print("Access Token:", token)  # Debug print to check the token format

headers = {'Authorization': f'Bearer {token}'}
# print("Headers being sent:", headers)  # Debug print to check the headers

url = 'https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections'
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    print("Success:", json.dumps(response.json(), indent=4))
else:
    print("Failed to fetch data:", response.status_code, response.text)



def main():




if __main__ == "__main__":
    main()
