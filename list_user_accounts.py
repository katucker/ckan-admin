"""Python command-line script for listing CKAN user accounts.
 
 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for input
 if the environment variable is not set.

 
"""
import logging
import os
import string
import sys

import ckanapi
import json


    
if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    
    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = raw_input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)

    dd = {'order_by': 'created'}
    result = remote.call_action(action='user_list', data_dict=dd)

    print('User ID,role,account created date')
    for user in result:
        print(f'{user["email"]},{"admin" if user["sysadmin"] else "user"},{user["created"]}')
    