import logging
import psycopg

logging.basicConfig(level=logging.INFO)

try:
    conn = psycopg.connect(host="bpvhxlvcka302.lab.ed.gov", dbname="ckantestdb",  user="ckantester", sslmode="prefer")
    print('Connection succeeeded.')
except Exception as e:
    logging.error('Exception',exc_info=e)