"""Python command-line script for listing CKAN groups and associated user accounts.
 
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

def build_user_role_list(org_response):
    roles = {}
    for org in org_response:
        for user in org["users"]:
            if user["id"] in roles:
                # The three roles expected are admin, editor, and member, which are in decreasing order or privilege.
                # Since the role names are alphabetical, capture the highest privilege by storing the lower role name.
                if user["capacity"] < roles[user["id"]]:
                    roles[user["id"]] = user["capacity"]
            else:
                roles[user["id"]] = user["capacity"]
    return roles

def get_role(user_id, user_roles):
    if user_id in user_roles:
        return user_roles[user_id]
    else:
        return "public"
    
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.ERROR))
    
    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = raw_input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)

    dd = {'all_fields': True, 'include_users': True}
    result = remote.call_action(action='organization_list', data_dict=dd)
    user_role_list = build_user_role_list(result)
    logging.info(user_role_list)

    dd = {'all_fields': True, 'order_by':'created'}
    result = remote.call_action(action='user_list', data_dict=dd)

    print('account_id,account_name,role,creation_date')
    for user in result:
        if user["sysadmin"]:
            print(f'{user["id"]},{user["display_name"]},admin,{user["created"]}')
        else:
            print(f'{user["id"]},{user["display_name"]},{get_role(user["id"], user_role_list)},{user["created"]}')
    