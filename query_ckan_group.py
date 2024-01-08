import getpass
import logging
import os
import sys

import ckanapi
import json


def dump_group(connection, group_name):
    
    try:
        result = connection.call_action(action='group_show', data_dict={'id':group_name,
                                                                        'include_datasets': False, 
                                                                        'include_dataset_count': False, 
                                                                        'include_extras': True, 
                                                                        'include_users': False, 
                                                                        'include_groups': False, 
                                                                        'include_tags': False, 
                                                                        'include_followers': False})
        print(json.dumps(result, indent=2))
#        result = connection.call_action(action='group_list',data_dict={'all_fields':True})
#        print(json.dumps(result, indent=2))

    except ckanapi.errors.NotFound:
       logging.error(f'No group found named {group_name}')
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
    else:
        id = input('Enter group name:')

    dump_group(remote, id)
