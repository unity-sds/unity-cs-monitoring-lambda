import boto3

import boto3

def fetch_services_health_status(shared_ssm):
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

# Usage of the function
if __name__ == "__main__":
    shared_params = fetch_services_health_status(True)
    print(shared_params)

