import boto3

def fetch_shared_parameters(file_path):
    # Create an SSM client
    ssm_client = boto3.client('ssm')

    # Open a file to write the parameters' details
    with open(file_path, 'w') as file:
        # Using paginator to handle potential large number of parameters
        paginator = ssm_client.get_paginator('describe_parameters')
        # Fetch only shared parameters
        page_iterator = paginator.paginate(
            ParameterFilters=[],
            MaxResults=50,
            Shared=True
        )

        # Iterate through each page of results
        for page in page_iterator:
            for param in page.get('Parameters', []):
                # Write details about each parameter to the file
                file.write(f"Name: {param['Name']}, Type: {param['Type']}, Last Modified: {param.get('LastModifiedDate')}\n")

# Usage of the function
if __name__ == "__main__":
    fetch_shared_parameters('shared_parameters.txt')

