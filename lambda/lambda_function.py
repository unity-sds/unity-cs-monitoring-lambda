import boto3
import os
import botocore
import sys
import requests
import datetime
import json

def get_ssm_parameters(parameter_names, shared=False):
    """
    Retrieve multiple SSM parameters using Boto3, with optional account prefixing for shared parameters.
    
    Parameters:
    - parameter_names (list of str): Names of the parameters to retrieve.
    - shared (bool): Indicates whether the parameters are shared across accounts.
    """
    ssm = boto3.client('ssm')

    if shared:
        # Get the account ID parameter
        try:
            account_response = ssm.get_parameter(Name='/unity/shared-services/aws/account')
            account_id = account_response['Parameter']['Value']
        except Exception as e:
            print(f"Error retrieving AWS account ID: {e}", file=sys.stderr)
            return {}

        # Prepend the account ID to each parameter name
        parameter_names = [
            # TODO: Variables - region 
            f'arn:aws:ssm:us-west-2:{account_id}:parameter{name}' for name in parameter_names
        ]

    try:
        # Get multiple parameters
        response = ssm.get_parameters(
            Names=parameter_names,
            WithDecryption=True
        )

        if response['InvalidParameters']:
            print(f"Invalid parameters: {response['InvalidParameters']}", file=sys.stderr)

        # Extract parameter values into a dictionary
        parameter_values = {param['Name']: param['Value'] for param in response['Parameters']}
        return parameter_values
    except Exception as e:
        print(f"Error retrieving parameters: {e}", file=sys.stderr)
        return {}

def fetch_health_status_ssm(shared_ssm):
    """
    Fetches health status related SSM parameters based on shared or local setting.

    Parameters:
    - shared_ssm (bool): If True, fetch shared parameters; otherwise, fetch local parameters.
    """
    # Create an SSM client
    ssm_client = boto3.client('ssm')
    
    # Determine the prefix based on the local_only flag
    if shared_ssm:
        prefix = '/unity/healthCheck/shared-services/'
    else:
        prefix = '/unity/healthCheck/'
        # TODO:
        # prefix = '/unity/PROJECT/VENUE/healthCheck/
    
    # Initialize the list to store specific parameter names
    parameter_names = []
    
    # Using a paginator to handle potential large number of parameters
    paginator = ssm_client.get_paginator('describe_parameters')
    # Fetch parameters with a specific prefix
    page_iterator = paginator.paginate(
        ParameterFilters=[
            {
                'Key': 'Name',
                'Option': 'BeginsWith',
                'Values': [prefix]
            }
        ],
        MaxResults=50,
        Shared = shared_ssm
    )

    # Iterate through each page of results
    for page in page_iterator:
        for param in page.get('Parameters', []):
            # Check if the parameter name starts with the specific prefix
            if param['Name'].startswith(prefix):
                # Add parameter name to the list
                parameter_names.append(param['Name'])
    
    return parameter_names


def create_cognito_client(cognito_info):
    """
    Create a Cognito client and initiate authentication to get an access token.

    Parameters:
    - cognito_info (dict): Dictionary containing Cognito credentials and client ID.
    """
    client = boto3.client('cognito-idp')
    response = client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': cognito_info['/unity/shared-services/cognito/monitoring-username'],
            'PASSWORD': cognito_info['/unity/shared-services/cognito/monitoring-password'],
        },
        ClientId=cognito_info['/unity/shared-services/dapa/client-id']
    )
    return response['AuthenticationResult']['AccessToken']

def check_service_health(service_urls, access_token):
    """
    Check the health status of each service by making HTTP requests with the appropriate authorization headers.

    Parameters:
    - service_urls (dict): Dictionary mapping service names to their health check URLs.
    - access_token (str): Access token for authentication.
    """
    health_status = {"services": []}
    headers = {'Authorization': f'Bearer {access_token}'}

    for service_name, url in service_urls.items():
        try:
            response = requests.get(url, headers=headers)
            status = "HEALTHY" if response.status_code == 200 else "UNHEALTHY"
        except Exception as e:
            status = "UNHEALTHY"
            print(f"Error accessing {url}: {e}", file=sys.stderr)

        health_status["services"].append({
            "service": service_name,
            "landingPage": "N/A",
            "healthChecks": [{"status": status, "date": datetime.datetime.now().isoformat()}]
        })
    return health_status


def upload_json_to_s3(json_data, bucket_name, object_name):
    """
    Upload JSON data to an S3 bucket.

    Parameters:
    - json_data (dict): JSON data to upload.
    - bucket_name (str): Bucket to upload to.
    - object_name (str): S3 object name.
    """
    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Convert the JSON data to a formatted string with indentation
        json_string = json.dumps(json_data, indent=4)

        # Upload the JSON string to S3
        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=object_name,
            Body=json_string,
            ContentType='application/json'
        )
        return True, "JSON uploaded successfully."
    except Exception as e:
        # The upload failed; return False and the error
        return False, str(e)

def lambda_handler(event, context):
    """AWS Lambda function handler with print statements for debugging."""
    project = os.environ.get('PROJECT')
    venue = os.environ.get('VENUE')
    print("PROJECT:", project)
    print("VENUE:", venue)
    
    bucket_name = f'unity-{project}-{venue}-bucket'
    print("BUCKET_NAME")
    print("BUCKET_NAME", bucket_name)
    
    print(f"boto3 version: {boto3.__version__}")
    print(f"botocore version: {botocore.__version__}")

    shared_parameters_cognito = [
        '/unity/shared-services/cognito/monitoring-username',
        '/unity/shared-services/cognito/monitoring-password',
        '/unity/shared-services/dapa/client-id',
    ]
    
    # Fetch shared parameters
    cognito_info = get_ssm_parameters(shared_parameters_cognito, shared=True)
    print("COGNITO INFO:", cognito_info)

    shared_services_health_ssm = fetch_health_status_ssm(True)
    print("SHARED SERVICED SSM:", shared_services_health_ssm)

    local_health_ssm = fetch_health_status_ssm(False)
    print("LOCAL HEALTH SSM:", local_health_ssm)

    token = create_cognito_client(cognito_info)
    print("Access Token:", token)

    shared_services_health_info = get_ssm_parameters(shared_services_health_ssm, shared=True)
    local_health_info = get_ssm_parameters(local_health_ssm, shared=False)

    print("SHARED SERVICES INFO:", shared_services_health_info)
    print("LOCAL HEALTH INFO:", local_health_info)

    # Combine shared and local health information
    combined_health_info = {**shared_services_health_info, **local_health_info}
    print("COMBINED HEALTH INFO:", combined_health_info)

    # Check the health status using the combined health information
    health_status = check_service_health(combined_health_info, token)
    
    # health_status = check_service_health(shared_services_health_info, token)
    print("Health Status:", health_status)

    now = datetime.datetime.now()
    filename = now.strftime("health_check_%Y-%m-%d_%H-%M-%S.json")

    # Upload the JSON data to S3
    upload_status, upload_message = upload_json_to_s3(health_status, bucket_name, filename)
    print("Upload Status:", upload_message) 


    # Output the result as JSON
    return {
        'statusCode': 200,
        'body': json.dumps(health_status, indent=4),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

# For local testing
def main():
    test_event = {
    }
    test_context = {}  # Empty context, not used in local testing

    # Call the Lambda handler function
    response = lambda_handler(test_event, test_context)
    print("Lambda Response:", response)

#if __name__ == '__main__':
    # main()
