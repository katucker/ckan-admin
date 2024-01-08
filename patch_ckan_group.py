import argparse
import getpass
import logging
import os

import ckanapi

def find_group_by_name(connection, group_name):
    
    try:
        result = connection.call_action(action='group_show', data_dict={'id':group_name})
        return result.get('id',None)

    except ckanapi.errors.NotFound:
        logging.error('No group found with name %s', group_name)
        return None

def patch_group(connection, group_id, param_list):
    
    try:
        dd = {'id':group_id}
        dd.update(param_list)
        logging.info('Patch parameters:%s\n', dd)
        result = connection.call_action(action='group_patch', data_dict=dd)
    except ckanapi.errors.NotFound:
        logging.error('No group found with id %s',group_id)
        return

    
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
        description='''Change parameters in an existing CKAN group.''',
        epilog='''The program uses the following environment variables for CKAN authentication credentials:
  ED_CKAN_URL: The Internet address to use for CKAN API calls
  ED_CKAN_KEY: The access key to use for authenticating CKAN API calls
''')
    ap.add_argument('-i','--id', 
        help='The identifier of the group to change.') 
    ap.add_argument('-n','--name', 
        help='If an id is also provided, changes the group name to this value. Otherwise, this value is used to find the group to change.')
    ap.add_argument('-d','--display',
        help='Change the display name for the group to this value.')
    ap.add_argument('--description',
        help='Change the description for ths group to this value.')
    ap.add_argument('-s','--state',
        help='Change the group state to this value.')
    ap.add_argument('-t','--title',
        help='Change the group title to this value.')
    ap.add_argument('--type',
        help='Change the group type to this value.')
    args = ap.parse_args()


    param_list = {}
    if args.name:
        if args.id:
            param_list.update({'name':args.name})
        else:
            args.id = find_group_by_name(remote, args.name)
    if args.display:
        param_list.update({'display_name':args.display})
    if args.description:
        param_list.update({'description':args.description})
    if args.state:
        param_list.update({'state':args.state})
    if args.title:
        param_list.update({'title':args.title})
    if args.type:
        param_list.update({'type':args.type})
    logging.info('Patching group %s', args.id)
    if args.id:
        patch_group(remote, args.id, param_list)
