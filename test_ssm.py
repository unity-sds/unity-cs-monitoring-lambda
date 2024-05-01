import boto3
import sys

def get_ssm_parameters(parameter_names, shared=False):
    """Retrieve multiple SSM parameters using Boto3, with optional account prefixing for shared parameters."""
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
    # Create an SSM client
    ssm_client = boto3.client('ssm')
    
    # Determine the prefix based on the local_only flag
    if shared_ssm:
        prefix = '/unity/healthCheck/shared-services/'
    else:
        prefix = '/unity/healthCheck/'
    
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


def main():
    """Main function to control the flow of the program."""
    shared_parameters_cognito = [
        '/unity/shared-services/cognito/monitoring-username',
        '/unity/shared-services/cognito/monitoring-password',
        '/unity/shared-services/dapa/client-id',

    ]
    local_parameters = [
    ]

    # Fetch shared parameters
    cognito_info = get_ssm_parameters(shared_parameters_cognito, shared=True)
    shared_services_health_ssm = fetch_health_status_ssm(True)
    
    local_health_ssm = fetch_health_status_ssm(False)

    print("COGNITO INFO")
    print(cognito_info)
    print()

    print("SHARED SERVICED SSM ")
    print(shared_services_health_ssm)
    print()

    print("LOCAL HEALTH SSM")
    print(local_health_ssm)
    print()
    
    shared_services_health_info = get_ssm_parameters(shared_services_health_ssm, shared=True)
    local_health_info = get_ssm_parameters(local_health_ssm, shared=False)
   
    print("SHARED SERVICES INFO")
    print(shared_services_health_info)
    print()

    print("LOCAL HEALTH INFO")
    print(local_health_info)
    print()

    # Fetch local parameters
#    local_parameter_values = get_ssm_parameters(local_parameters)



if __name__ == "__main__":
    main()
