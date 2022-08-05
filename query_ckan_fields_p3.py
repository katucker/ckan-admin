import getpass
import logging
import os
import sys

import ckanapi
import json


def dump_dataset(connection, id):
    
    try:
        result = connection.call_action(action='package_search', data_dict={'q': 'name:{} OR id:{}'.format(id,id), 'fl': 'id, name, title, dataset_type'})
        print("Filtered search results:")
        print(json.dumps(result, indent=2))

    except ckanapi.errors.NotFound:
       logging.error('ID not found: {}'.format(id))
       return

    
if __name__ == '__main__':

    url = os.getenv('ED_CKAN_URL', None)
    apiKey = os.getenv('ED_CKAN_KEY', None)

    if not url:
        url = input('Enter CKAN URL:')
    if not apiKey:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, apiKey)

    id = ''
    if len(sys.argv) > 1:
        id = sys.argv[1]
        dump_dataset(remote,id)
    else:
        id = input('Enter dataset identifier:')

    dump_dataset(remote, id)
