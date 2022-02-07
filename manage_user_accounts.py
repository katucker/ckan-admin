"""Python command-line script for managing CKAN user accounts.
 This script can only create or update a user account. It does not
 manage memberships in groups or roles.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for input
 if the environment variable is not set.

 The script expects a single command-line argument, specifying the name
 of a file containing an array of user account data dictionaries, in JSON
 format and matching the specification at
 http://docs.ckan.org/en/2.8/api/#ckan.logic.action.create.user_create
 with one addition - a key of 'apikey' to indicate the API Key for an
 existing user account should be regenerated. Note the associated value for the
 'apikey' label must be the literal 'reset' to trigger the API Key regeneration.

 Sample content for the JSON file:
 [
    {
        "name": "user1_name",
        "email": "user1@exmple.com",
        "fullname": "User One"
    },
    {
        "name": "user2_name",
        "email": "user2@example.com",
        "fullname": "User Two"
    },
    {
        "id": "d5bd2e1a-0d4b-4381-84e4-98da475679e3",
        "name": "exiting_user1_name",
        "email": "new_email@example.com",
        "fullname": "New Full Name",
        "password": "F0rc3dUpd*t3"
    },
    {
        "id": "d5bd2e1a-0d4a-4380-83e4-98da465679e3",
        "apikey": "reset"
    }
]

"""
import getpass
import logging
import os
import random
import string
import sys

import ckanapi
import json


def create_user_account(connection, user_data_dict):
    """ Create a user account using the passed dictionary."""
    
    # If the user_data_dict does not contain a password element, add a random
    # string as the password. Set the first 4 characters to satisfy the
    # diversity requirements, then add some other random characters to satisfy
    # the length requirement.
    if 'password' not in user_data_dict:
        user_data_dict['password'] = random.choice(string.ascii_uppercase)
        user_data_dict['password'] += random.choice(string.ascii_lowercase)
        user_data_dict['password'] += random.choice(string.digits)
        user_data_dict['password'] += random.choice(string.punctuation)
        for x in range(9):
            user_data_dict['password'] += random.choice(string.printable)
    
    try:
        result = connection.call_action(action='user_create', data_dict=user_data_dict)
        logging.info("Created user account for %s", result['name'])

    except:
       logging.exception('Exception creating user account for {}'.format(user_data_dict['name']))

def update_user_account(connection, user_data_dict):
    """Update an existing user account.
        Explicitly check whether the update includes regenerating the API key.
    """
    try:
        if 'apikey' in user_data_dict:
            if user_data_dict['apikey'] == 'reset':
                api_dict = {'id': user_data_dict['id']}
                result = connection.call_action(action='user_generate_apikey', data_dict=api_dict)
                logging.info('Regenerated API Key for %s', user_data_dict['id'])
            # Remove the API Key key pair from the user_data_dict before proceeding
            user_data_dict.pop('apikey')
        # Remove any keys for fields that cannot be changed.
        user_data_dict.pop('name',None)
        user_data_dict.pop('email',None)
        if len(user_data_dict) > 1:
            result = connection.call_action(action='user_update', data_dict=user_data_dict)
            logging.info("Updated user account for %s", result['name'])
        else:
            logging.info("Nothing left to update for %s", user_data_dict['id'])

    except:
       logging.exception('Error attempting to update user account for {}'.format(user_data_dict['id']))
    
def manage_user_account(connection, user_data_dict):
    # If the user_data_dict contains an identifier, assume the user entry
    # needs to be updated.
    if 'id' in user_data_dict:
        update_user_account(connection, user_data_dict)
    else:
        create_user_account(connection, user_data_dict)
    
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

    if len(sys.argv) > 1:
        input_file_name = sys.argv[1]
        with open(input_file_name) as input_file:
            try:
                user_entries = json.load(input_file)
                for user_entry in user_entries:
                    manage_user_account(remote, user_entry)
            except:
                logging.exception('Exception reading input file.')
    else:
        print('Provide a file name containing JSON user entries as the only command argument.')

