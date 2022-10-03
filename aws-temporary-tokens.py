#!/usr/bin/env python3
# Author: Alvaro Mantilla Gimenez <alvaro@alvaromantilla.com>

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import sys
import subprocess


if __name__ == "__main__":

    # ARGPARSE MESSAGES
    command_description = "Simplifies STS tokens used for accessing AWS through aws-cli commands when MFA is enabled for user"
    command_mfa_help = "MFA code generated by your (virtual)device"
    command_mfa_arn_help = "AWS ARN for your (virtual)device"
    command_time_help = "Time in seconds before the new token expires. (Min)900s - (Max)129600s"
    command_profile_help = "AWS Profile that you want to use from your ars credentials file"
    # ARGPARSE ARGUMENTS
    parser = ArgumentParser(description=command_description)
    parser.add_argument('-c', '--mfa_code', type=str, required=True, help=command_mfa_help)
    parser.add_argument('-d', '--mfa_device', type=str, required=False, help=command_mfa_arn_help, default='None')
    parser.add_argument('-t', '--time', type=str, required=False, help=command_time_help, default='28800')
    parser.add_argument('-p', '--profile', type=str, required=False, help=command_profile_help, default='default')
    # ARGPARSE OBJECT
    args = parser.parse_args()
    print("[+] Parsing object for given arguments")
    # OPEN CONFIGURATION FILE IF NO MFA_DEVICE ON ARGUMENTS
    if args.mfa_device == 'None':
        configuration_file = str(Path.home()) + "/.aws_temporary_tokens.json"
        print(f"[+] MFA not passed as argument. Opening {configuration_file}.")
        try:
            with open(configuration_file) as conf:
                print(f"[+] Loading configuration data for profile {args.profile}") 
                conf_data = json.load(conf)
        except Exception:
            print(f'There was an error trying to load the local configuration file. Please confirm the file exist or json syntax is correct.')
            sys.exit(1)
        # Look for specified profile
        mfa_device = conf_data['default'][0]['arn_device'] if args.profile == 'default' else conf_data[f'{args.profile}'][0]['arn_device']
    else:
        mfa_device = args.mfa_device
    # Execute sts commands
    if args.profile == 'default':
        sts_command = f"sts get-session-token \
                        --duration-seconds {args.time} \
                        --serial-number {mfa_device} \
                        --token-code {args.mfa_code}"
    else:
        sts_command = f"sts get-session-token \
                        --duration-seconds {args.time} \
                        --serial-number {mfa_device} \
                        --token-code {args.mfa_code} \
                        --profile {args.profile}"
    try:
        sts_output = subprocess.run("aws " + f"{sts_command}", shell=True, capture_output=True, text=True).stdout
    except Exception as e:
        print(e)
        sys.exit(1)
    # GETTING NEW GENERATED CREDENTIALS
    temporal_access = json.loads(sts_output)
    temporal_access_key = temporal_access['Credentials']['AccessKeyId']
    temporal_secret_key = temporal_access['Credentials']['SecretAccessKey']
    temporal_session_token = temporal_access['Credentials']['SessionToken']
    # OPEN A NEW TERMINAL WITH TEMPORARY CREDENTIALS
    export_script = f"export AWS_ACCESS_KEY_ID={temporal_access_key} \
                        && export AWS_SECRET_ACCESS_KEY={temporal_secret_key} \
                        && export AWS_SESSION_TOKEN={temporal_session_token}"
    if sys.platform == 'darwin':
        terminal_command = f"/usr/bin/osascript -e 'tell application \"Terminal\" to do script \"{export_script}\"'"
        subprocess.run(terminal_command, shell=True)
    else:
        print("Please copy/paste the following in your terminal:\n")
        print(f"{export_script}\n")
    sys.exit(0)
