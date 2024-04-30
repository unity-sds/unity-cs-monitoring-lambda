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

def main():
    """Main function to control the flow of the program."""
    shared_parameters = [
        '/unity/shared-services/cognito/monitoring-username',
        '/unity/shared-services/cognito/monitoring-password',
        '/unity/shared-services/dapa/client-id',
        '/unity/healthCheck/shared-services/data-catalog/url'

    ]

    local_parameters = [
    ]

    # Fetch shared parameters
    shared_parameter_values = get_ssm_parameters(shared_parameters, shared=True)
    # Fetch local parameters
#    local_parameter_values = get_ssm_parameters(local_parameters)

    # Combine results
#    all_parameter_values = {**shared_parameter_values, **local_parameter_values}

    if shared_parameter_values:
        for name, value in shared_parameter_values.items():
            print(f"Value of the parameter '{name}': {value}")
    else:
        print("Failed to retrieve the parameters.")

if __name__ == "__main__":
    main()
