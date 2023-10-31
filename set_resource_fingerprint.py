"""Python command-line script for setting a fingerprint for resources
in a CKAN instance. The fingerprint is stored in the 'hash' field
for the resource. The sha512 algorithm is used, in an attempt to
avoid collisions on large resources.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for input
 if the environment variable is not set.

 A command line switch can be specified to force recalculation of all
 resource hashes.

 A command line argument can set the size of the buffer to use for
 retrieving files for hash calculation.
"""
import argparse
import getpass
import hashlib
import json
import logging
import os
import requests
import sys
import urllib3

import ckanapi

BUFFER_SIZE = 16777216
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 20.0

def get_hash(http_pool, buffer_size, url):
    try:
        # Initialize the hash object.
        hash = hashlib.sha512()
        # Retrieve the file at the passed URL as a stream, 
        # in case it is larger than will fit in memory.
        with http_pool.request('GET',url,preload_content=False) as response:
            # Read the stream, updating the hash object for each chunk received.
            for buff in response.stream(buffer_size):
                if buff:
                    hash.update(buff)
        return f'sha512-{hash.hexdigest()}'
    except Exception as e:
        logging.error(e)
        return None


def set_resource_fingerprints(connection, force_update, buffer_size, http_pool, pkg_id):
    """Retrieve the metadata for all datasets in the connected CKAN repository.
       Update the resource entries for each to contain the fingerprint for
       the referenced data file.
    """
    try:
        if pkg_id:
            # Retrieve only the package specified in the pass ID, and update its resources.
            pkg_result = connection.call_action(action='package_show', data_dict={'id': pkg_id})
            logging.info(pkg_result)
            if pkg_result.get('type','') == 'dataset':
                    if 'resources' in pkg_result:
                        for resource in pkg_result['resources']:
                            if 'url' in resource:
                                logging.info(f'Calulating hash for {resource["url"]}')
                                res_hash = get_hash(http_pool=http_pool, buffer_size=buffer_size, url=resource['url'])
                                if res_hash:
                                    try:
                                        patch_data_dict = {"id":resource['id'], "hash": res_hash}
                                        logging.info(f'Patching {resource["id"]} with hash {res_hash}')
                                        patch_result = connection.call_action(action='resource_patch', data_dict=patch_data_dict)
                                    except Exception as e:
                                        logging.error(e)
                                        continue
            return

        offset = 0
        increment = 1000
        while (True):
            pass_data_dict = { 'limit': increment, 'offset': offset }
            pass_result = connection.call_action(action='current_package_list_with_resources', data_dict=pass_data_dict)
            if len(pass_result) == 0: break
            offset += increment
            # Iterate over the retrieved datasets.
            for dataset in pass_result:
                if ('type' in dataset and dataset['type'] == 'dataset'):
                    if 'resources' in dataset:
                        for resource in dataset['resources']:
                            if 'url' in resource:
                                if (not force_update and ('hash' in resource) and (len(resource['hash']) > 0)):
                                    logging.info(f'Resource {resource["url"]} already has hash {resource["hash"]}')
                                    continue
                                logging.info(f'Calulating hash for {resource["url"]}')
                                res_hash = get_hash(http_pool=http_pool, buffer_size=buffer_size, url=resource['url'])
                                if res_hash:
                                    try:
                                        patch_data_dict = {"id":resource['id'], "hash": res_hash}
                                        logging.info(f'Patching {resource["id"]} with hash {res_hash}')
                                        patch_result = connection.call_action(action='resource_patch', data_dict=patch_data_dict)
                                    except Exception as e:
                                        logging.error(e)
                                        continue

    except Exception as e:
        logging.error(e)
    
    
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.ERROR))
    
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Set resource fingerprints in a CKAN instance.

   Unless overridden on the command line, only resource records in the
   CKAN instance that do not currently have a value in the hash field
   and that have a download URL will be updated to record a hash using
   the sha512 algorithm.
  ''',
        epilog='''The program uses the following environment variables:
  CKAN_URL: The base URL for the API to use (without the trailing "/api/action" text).
  CKAN_KEY: The API key for authentication.
 ''')

    ap.add_argument('-f','--force', help='Force calculation of a hash for every resource that has a URL for a data file.', action="store_true") 
    ap.add_argument('-b','--buffer', type=int, help='Set the buffer size to use for retrieving data files.', default=BUFFER_SIZE)
    ap.add_argument('-c','--connect', type=float, help='Connection timeout for file retrieval requests.', default=CONNECT_TIMEOUT)
    ap.add_argument('-r','--read', type=float, help='Read timeout for file retrieval requests.', default=READ_TIMEOUT) 
    ap.add_argument('-p','--package', type=str, help='Identifier for a single data profile to update', default=None)
    args = ap.parse_args()
    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)

    http=urllib3.PoolManager(timeout=urllib3.Timeout(connect=args.connect, read=args.read))

    set_resource_fingerprints(connection=remote, force_update=args.force, buffer_size=args.buffer, http_pool=http, pkg_id=args.package)
