import argparse
import getpass
import logging
import os

import ckanapi

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
        description='''Delete the group specified on the command line from a CKAN instance.''',
        epilog='''The program uses the following environment variables to identify and authenticate to the CKAN instance, prompting for their values if not set:
  ED_CKAN_URL: The web address to use for API calls.
  ED_CKAN_KEY: The authentication key value to use for API calls.
''')
    ap.add_argument('-g','--group', help='The name of the category group to associate with the datasets.')
    args = ap.parse_args()

    result = remote.call_action(action='group_delete', data_dict={'id':args.group})
