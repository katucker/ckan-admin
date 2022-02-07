import json
import logging
import os
import sys
import re

from ckanapi import RemoteCKAN

# The name of the metadata field containing the accrual periodicity value.
ACCRUAL_FIELD = 'update_frequency'

# Syntax for a command line argument to turn off updates.
DO_UPDATE = '-update'

# Flag for whether to actually update or just log what would be updated.
do_update = False

# Function to retrieve the unique identifiers for all datasets in a CKAN instance.
def retrieve_metadata(ckan_connection):
    metadata = []
    limit = 1000
    # Do the initial search of datasets, returning the first batch and the total count 
    # of matching datasets
    try:
        result = ckan_connection.call_action(action='package_search', data_dict={
            'rows': limit,
            'start': 0,
            'include_private': True,
            'include_drafts': True,
            'fl': ['id','extras_update_frequency']
            })
    except:
        return metadata
    if not result:
        return metadata

    for p in result.get('results',[]):
        metadata.append({'id': p.get('id'), ACCRUAL_FIELD: p.get(ACCRUAL_FIELD, None)})
        
    count = result.get('count')
    if count < limit:
        return metadata
    batches = count / limit
    if count % limit != 0:
        batches += 1
    
    for batch in range(1,batches):
        try:
            result = ckan_connection.call_action(action='package_search', data_dict={
                        'rows': limit,
                        'start': batch * limit,
                        'include_private': True,
                        'include_drafts': True,
                        'fl': ['id','extras_update_frequency']
                        })
            for p in result.get('results',[]):
                metadata.append({'id': p.get('id'), ACCRUAL_FIELD: p.get(ACCRUAL_FIELD,None)})
        except:
            continue
            
    return metadata
        
def fix_periodicity(ckan_connection, meta_dict):
    # Define a regular expression for any valid value of the accrualPeriodicity field. The literal string "irregular" can be used, or a recurring duration encoded in ISO 8601 format.
    # This matches the regular expression used in the DCAT-US version 1.1 schema.
    periodicity_iso_8601_pattern = "^irregular|R\\/P(?:\\d+(?:\\.\\d+)?Y)?(?:\\d+(?:\\.\\d+)?M)?(?:\\d+(?:\\.\\d+)?W)?(?:\\d+(?:\\.\\d+)?D)?(?:T(?:\\d+(?:\\.\\d+)?H)?(?:\\d+(?:\\.\\d+)?M)?(?:\\d+(?:\\.\\d+)?S)?)?$"
    # An array of values expected in the accrualPeridocity field (from before the validation for that field was correctly implemented) with the corresponding ISO 8601 compliant string.
    periodicity_remove = "None"
    periodicity_lookup = [
        {"verbose": "Decennial(ly)*", "iso8601":"R/P10Y"},
        {"verbose": "Quadrennial(ly)*", "iso8601":"R/P4Y"},
        {"verbose": "Annual(ly)*", "iso8601":"R/P1Y"},
        {"verbose": "Bimonthly", "iso8601":"R/P2M"},
        {"verbose": "Semiweekly", "iso8601":"R/P3.5D"},
        {"verbose": "Daily", "iso8601":"R/P1D"},
        {"verbose": "Biweekly", "iso8601":"R/P2W"},
        {"verbose": "Semiannual(ly)*", "iso8601":"R/P6M"},
        {"verbose": "Biennial(ly)*", "iso8601":"R/P2Y"},
        {"verbose": "Biannual(ly)*", "iso8601":"R/P2Y"},
        {"verbose": "Triennial(ly)*", "iso8601":"R/P3Y"},
        {"verbose": "Triannual(ly)*", "iso8601":"R/P3Y"},
        {"verbose": "Three times a week", "iso8601":"R/P0.33W"},
        {"verbose": "Three times a month", "iso8601":"R/P0.33M"},
        {"verbose": "Continuously updated", "iso8601":"R/PT1S"},
        {"verbose": "Monthly", "iso8601":"R/P1M"},
        {"verbose": "Quarterly", "iso8601":"R/P3M"},
        {"verbose": "Semimonthly", "iso8601":"R/P0.5M"},
        {"verbose": "Three times a year", "iso8601":"R/P4M"},
        {"verbose": "Weekly", "iso8601":"R/P1W"},
        {"verbose": "Hourly", "iso8601":"R/PT1H"},
        {"verbose": "Other", "iso8601":"irregular"},
        {"verbose": "None", "iso8601": "" }
        ]

    # If the passed meta_dict doesn't have an accrual periodicity value,
    # there is nothing to fix.
    if meta_dict[ACCRUAL_FIELD] is None:
        return False
        
    accrual = meta_dict[ACCRUAL_FIELD]
    # Check the accrual periodicity against the regular expression pattern for valid entries.
    if re.search(periodicity_iso_8601_pattern, meta_dict[ACCRUAL_FIELD]) is None:
        # The value didn't match the regular expression, so try to replace it.
        for repl in periodicity_lookup:
            accrual = re.sub(repl['verbose'], repl['iso8601'], accrual)
        if accrual != meta_dict[ACCRUAL_FIELD]:
            # Patch the package to only update the periodicity field.
            if do_update:
                try:
                    meta_dict[ACCRUAL_FIELD] = accrual
                    ckan_connection.call_action(action='package_patch', data_dict = meta_dict)
                    logging.info('Updated periodicity to %s for %s', accrual, meta_dict['id'])
                    return True
                except Exception as e:
                    logging.error('Could not patch dataset %s.\n Error: %s', meta_dict['id'], e)
                    return False
            else:
                logging.debug('Would replace %s with %s', meta_dict[ACCRUAL_FIELD], accrual)
                return True
        else:
            # The accrual periodicity value doesn't match the regular expression,
            # but also didn't match any of the search patterns for replacement.
            logging.warning("Uncorrected accrual periodicity %s in %s", accrual, meta_dict['id'])
            return False


	
if __name__ == '__main__':

    url = os.getenv('ED_CKAN_URL', None)
    api_key = os.getenv('ED_CKAN_KEY', None)

    errors = []

    if not url:
        errors.append('ED_CKAN_URL environment variable is needed.')
    if not api_key:
        errors.append('ED_CKAN_KEY environment variable is needed.')

    for arg in sys.argv:
        if (arg == DO_UPDATE): 
            do_update = True
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

    logging.basicConfig(format='%(levelname)s %(message)s',level=log_level)

    if len(errors):
        for e in errors:
            logging.error(e)
        sys.exit(1)

    remote_ckan = RemoteCKAN(address=url, apikey=api_key)
    logging.info('Processing on CKAN at URL %s', url)

    # Retrieve the complete list of package identifiers.
    dataset_list = retrieve_metadata(remote_ckan)

    logging.info('Found %d datasets.', len(dataset_list))
    
    updated = 0
    for d in dataset_list:
        if fix_periodicity(remote_ckan, d):
            updated += 1
            
    logging.info('Updated %d datasets.', updated)
