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
 format and matching the specification for user data dictionaries at
 http://docs.ckan.org/en/2.9/api with one addition - a key of 'action'
 to indicate the action to take using the rest of the dictionary.
 The action value is expected to be one of the following:

 create - to create a new account with the specified values
 update - to update an existing account
 delete - to delete an existing account
 reset - to reset the API key for an existing account
 
 Sample content for the JSON file:
 [
    {
        "action": "create",
        "name": "user1_name",
        "email": "user1@exmple.com",
        "fullname": "User One"
    },
    {
        "action": "create",
        "name": "user2_name",
        "email": "user2@example.com",
        "fullname": "User Two"
    },
    {
        "action": "update",
        "id": "d5bd2e1a-0d4b-4381-84e4-98da475679e3",
        "name": "exiting_user1_name",
        "email": "new_email@example.com",
        "fullname": "New Full Name",
        "password": "F0rc3dUpd*t3"
    },
    {
        "action": "reset",
        "id": "d5bd2e1a-0d4a-4380-83e4-98da465679e3"
    },
    {
        "action": "delete",
        "id": "former_user_name"
    }
]

"""
import getpass
import json
import logging
import os
import random
import string
import sys

import ckanapi


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
        logging.exception('Exception creating user account for %s',user_data_dict['name'])

def update_user_account(connection, user_data_dict):
    """Update an existing user account."""

    try:
        # Remove any keys for fields that cannot be changed.
        user_data_dict.pop('name',None)
        user_data_dict.pop('email',None)
        if len(user_data_dict) > 1:
            result = connection.call_action(action='user_update', data_dict=user_data_dict)
            logging.info("Updated user account for %s", result['name'])
        else:
            logging.info("Nothing left to update for %s", user_data_dict['id'])
    except:
        logging.exception('Error attempting to update user account for %s', user_data_dict['id'])
    
def reset_user_apikey(connection, user_data_dict):
    """Regenerate the API key for an existing user account.
    """
    try:
        result = connection.call_action(action='user_generate_apikey', data_dict=user_data_dict)
        logging.info('Regenerated API Key for %s', user_data_dict['id'])
    except:
        logging.exception('Error attempting to regenerate API key for %s', user_data_dict['id'])
    
def delete_user_account(connection, user_data_dict):
    """Delete an existing user account.
    """
    try:
        result = connection.call_action(action='user_delete', data_dict=user_data_dict)
        logging.info("Deleted user account for %s", user_data_dict['id'])
    except:
        logging.exception('Error attempting to delete user account for %s', user_data_dict['id'])

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    
    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)

    if len(sys.argv) > 1:
        input_file_name = sys.argv[1]
        with open(input_file_name) as input_file:
            try:
                user_entries = json.load(input_file)
                for user_entry in user_entries:
                    action = user_entry.get('action', None)
                    if action is not None:
                        user_entry.pop('action')
                        
                        match action:

                            case 'create':
                                create_user_account(remote, user_entry)
                            case 'delete':
                                delete_user_account(remote, user_entry)
                            case 'reset':
                                reset_user_apikey(remote, user_entry)
                            case 'update':
                                update_user_account(remote, user_entry)
                            case _:
                                logging.error('Unknown action: %s', action)
                    else:
                        logging.info('Missing action in %s', user_entry)
            except:
                logging.exception('Exception reading input file.')
    else:
        print('Provide a file name containing JSON user entries as the only command argument.')

