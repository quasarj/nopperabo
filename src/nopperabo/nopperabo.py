#!/usr/bin/env python3
HELP="""\
A daemon that removes faces
"""

import httpx
import argparse
import time
import os
import shutil
import subprocess
# import logging
import hashlib
import json
import time
from datetime import timedelta
from loguru import logger


# set here to something inside the local compose network, just for testing
# HOSTNAME='oneposda-web-1:8080'
# TOKEN='e9a63bc2-bfa5-4299-afb3-c844fb2ef38b'
# HOSTNAME='aries-posda-a1.ad.uams.edu'
# TOKEN='fcda15e2-297e-4893-984c-d2667371d9f5'
HOSTNAME='tcia-posda-rh-1.ad.uams.edu'
TOKEN='e9a63bc2-bfa5-4299-afb3-c844fb2ef38b'

DELAY=5
TEMP='/temp'

# logging.basicConfig()
# logger = logging.getLogger(__name__)
# # logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

headers = {
    'Authorization': f'Bearer {TOKEN}',
}

def parse_args():
    parser = argparse.ArgumentParser(description=HELP)
    parser.add_argument('--flag', help='an optional argument that takes a value')

    return parser.parse_args()

def md5sum(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()



def url(url_part):
    ret =  f'http://{HOSTNAME}/papi/v1/{url_part}'
    return ret

def get_work():
    r = httpx.get(url('masking/getwork'), headers=headers)

    if r.status_code == 200:
        obj = r.json()

        return obj['image_equivalence_class_id']
    else:
        return None

def get_masking_details(iec):
    r = httpx.get(url(f'masking/{iec}'), headers=headers)

    obj = r.json()

    masking_parameters = json.loads(obj['masking_parameters'])
    return masking_parameters

def get_iec_files(iec):
    r = httpx.get(url(f'iecs/{iec}/files'), headers=headers)

    obj = r.json()
    return obj['file_ids']

def download_file(some_url, file_id, path):
    logger.debug(f"Downloading file: {file_id}:{some_url}")
    resp = httpx.get(some_url, headers=headers)
    tmp_path = os.path.join(path, f"temp_{file_id}")

    with open(tmp_path, "wb") as out_file:
        for chunk in resp.iter_bytes():
            out_file.write(chunk)


def download_files(iec, files, path):
    for file in files:
        download_file(url(f'files/{file}/data'), file, path)

def update_masking_item(iec, exit_code, import_event_id=None):
    data = {
        'import_event_id': import_event_id,
        'exit_code': exit_code,
    }
    u = url(f'masking/{iec}/complete')
    r = httpx.post(u, json=data, headers=headers)

    #TODO check that it worked

def create_import_event(iec):
    u = url('import/event')
    r = httpx.put(u, params={
        'source': f'Masking result for iec={iec}'
    })

    resp = r.json()
    return resp['import_event_id']


def upload_file(import_event_id, filename):
    logger.debug(f"Uploading {filename} for import_event_id={import_event_id}")
    digest = md5sum(filename)
    with open(filename, "rb") as infile:
        r = httpx.put(
            url('import/file'), params={
                'import_event_id': import_event_id,
                'digest': digest,
                'localpath': filename,
            },
            data=infile
        )

        try:
            resp = r.json()
            return resp
        except:
            print(r.content)
            raise

def upload_output_files(iec):
    # create an import event
    import_event_id = create_import_event(iec)

    # upload the files
    for root, dirs, files in os.walk('/output'):
        for file in files:
            path = os.path.join(root, file)
            upload_file(import_event_id, path)

    logger.debug(import_event_id)
    return import_event_id

def do_work(iec):
    start_time = time.time()
    logger.info(f"Processing Masking for iec={iec}")

    # get the masking item details for the IEC
    logger.debug("Getting details for iec")
    details = get_masking_details(iec)

    # get list of files in IEC
    logger.debug("Getting file list for iec")
    files = get_iec_files(iec)
    logger.info(f"IEC has {len(files)} files...")

    # create dir for iec
    logger.debug("Creating temporary directory to store files")
    path = os.path.join(TEMP, str(iec))
    os.makedirs(path, exist_ok=True)
    os.makedirs('/output', exist_ok=True)

    # download each file to a temporary location
    logger.info(f"Downloading {len(files)} files for iec...")
    download_files(iec, files, path)
    download_time = timedelta(seconds=(time.time() - start_time))
    logger.info(f"Downloading complete, elapsed time {download_time}, masking...")

    # call masker on the downlaoded files
    details_order = ['lr', 'pa', 'i', 's', 'd']

    logger.debug("Running Masker...")
    proc = subprocess.run(
        [
            'masker',
            '--norender',
            '--multiprocessing',
            '-i', path,
            '-o', '/output',
            '-c', *[str(details[x]) for x in details_order],
        ],
        capture_output=True,
        text=True
    )
    result = proc.returncode

    if result == 0:
        masker_time = timedelta(seconds=(time.time() - start_time))
        logger.info(f"Masker was successful ({masker_time}) uploading results...")

        # if successful, upload the resulting dicom files to posda
        logger.debug("Uploading output files")
        import_event_id = upload_output_files(iec)
    else:
        logger.info(f"Masker failed with exit code {result}")
        logger.info(proc.stderr)
        import_event_id = 0


    # update the masking item
    logger.debug("Updating Masking item")
    update_masking_item(iec, result, import_event_id)

    # delete the temp path
    logger.debug("Cleaning up temp files")
    shutil.rmtree(path)
    shutil.rmtree("/output")

    total_eapsed_time = timedelta(seconds=(time.time() - start_time))
    logger.info(f"Completed IEC {iec}, took {total_eapsed_time} seconds")

def main(args):
    # print some startup messages
    logger.info(f"starting up {HOSTNAME=} {TOKEN=}")

    # enter infinite loop
    while True:
        # check for new work
        iec = get_work()

        if iec is not None:
            do_work(iec)
            # return
        else:
            # wait a bit so we don't spam the server
            # return
            time.sleep(DELAY)

if __name__ == '__main__':
    main(parse_args())
    # update_masking_item(3, 0, 1)
