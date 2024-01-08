import argparse
import getpass
import logging
import os

import ckanapi
import json


def find_dataset(connection, title):
    
    try:
        result = connection.call_action(action='package_search', data_dict={'q': f'title:{title}', 'fl': 'id'})
        results_list = result.get('results')
        if len(results_list) > 0:
            return results_list[0].get('id')
        else:
            return None

    except ckanapi.errors.NotFound:
        logging.error('No package found with title %s', title)
        return None

def set_category(connection, package_name, category_name):
    category_id = None
    try:
        result = connection.call_action(action='group_show', data_dict={'id':category_name,
                                                                        'include_datasets': False, 
                                                                        'include_dataset_count': False, 
                                                                        'include_extras': True, 
                                                                        'include_users': False, 
                                                                        'include_groups': False, 
                                                                        'include_tags': False, 
                                                                        'include_followers': False})
        category_id = result.get('id')
        result = connection.call_action(action='member_create', data_dict={'id': category_id, 'object': package_name, 'object_type': 'package', 'capacity': 'member'})
    except ckanapi.errors.NotFound:
        logging.info('Cannot find group %s', category_name)

    
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.ERROR))

    url = os.getenv('ED_CKAN_URL', None)
    apiKey = os.getenv('ED_CKAN_KEY', None)

    if not url:
        url = input('Enter CKAN URL:')
    if not apiKey:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, apiKey)

    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Set category associations in a CKAN instance for every dataset listed in an input file to the category name specified on the command line.''',
        epilog='''The program expects the input file to be compliant with the DCAT-US version 1.1 schema, and looks for title fields in the dataset list.
        The program creates the category as a type of CKAN group if it does not already exist in the instance.
        The program uses the following environment variables to identify and authenticate to the CKAN instance, prompting for their values if not set:
  ED_CKAN_URL: The web address to use for API calls.
  ED_CKAN_KEY: The authentication key value to use for API calls.
''')
    ap.add_argument('-f','--filename', 
        help='Use the data in the specified file to identify the datasets to change.')
    ap.add_argument('-c','--category', required=True, help='The name of the category group to associate with the datasets.')
    ap.add_argument('-i','--id',help='The identifier for a specific package to change.')
    args = ap.parse_args()

    if args.filename is not None:
        with open(args.filename) as ifp:
            input_dict = json.load(ifp)
            for dataset in input_dict.get('dataset'):
                dataset_title = dataset.get('title')
                logging.info('Searching for dataset %s', dataset_title)
                pkg_id = find_dataset(remote,dataset_title)
                if pkg_id is not None:
                    logging.info('Setting category for package id %s to %s', pkg_id, args.category)
                    set_category(remote, pkg_id, args.category)
    if args.id is not None:
        set_category(remote, args.id, args.category)
        