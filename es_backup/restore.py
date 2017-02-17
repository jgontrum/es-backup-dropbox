import sys
import os
import time
import json
import tarfile
import shutil
import requests
import argparse

def run():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--index", help="The name of the index to backup",
                        type=str, required=True)
    parser.add_argument("--host", help="The elasticsearch host.",
                        type=str, required=False, default='localhost')
    parser.add_argument("--port", help="The elasticsearch port.",
                        type=str, required=False, default="9200")
    parser.add_argument("--file", help="The .esbackup.tar.gz file to restore.",
                        type=str, required=True)
    args = parser.parse_args()

    # Get the elasticsearch server
    host = args.host
    port = args.port
    index = args.index
    url = "http://%s:%s" % (host, port)
    print("Using ElasticSearch at %s" % url)

    try:
        r = requests.get(url)
        if r.status_code is not 200:
            print("Error hitting ElasticSearch on %s, response code was %i" % (
                url, r.status_code))
            exit(1)
        else:
            print("Verified ElasticSearch server")
    except:
        print("Unable to hit ElasticSearch on %s" % url)
        exit(1)

    # Check with the user
    print("Restoring index '%s'" % index)
    print("Ctrl+C now to abort...")

    # time.sleep(3)

    # Check the index doesnt already exist
    r = requests.get("%s/%s/_mapping" % (url, index))
    if r.status_code != 404:
        print(
            "The index already exists. Please ensure it does not exist first.")
        print("This command can be executed to do this:")
        print("curl -XDELETE %s/%s" % (url, index))
        exit(1)

    # Unzip the backup file
    filename = args.file
    tar = tarfile.open(filename)
    tar.extractall()
    tar.close()

    # Read the settings
    settings = json.load(open("%s/settings.json" % index, "r"))

    main_index = list(settings.keys())[0]

    if main_index != index:
        r = requests.get("%s/%s/_mapping" % (url, main_index))
        if r.status_code != 404:
            print(
                "The index already exists. Please ensure it does not exist first.")
            print("This command can be executed to do this:")
            print("curl -XDELETE %s/%s" % (url, main_index))
            exit(1)

    settings = settings[main_index]
    if 'settings' in settings:
        settings = settings["settings"]
        if 'creation_date' in settings['index']:
            del settings['index']['creation_date']
        if 'provided_name' in settings['index']:
            del settings['index']['provided_name']
        if 'uuid' in settings['index']:
            del settings['index']['uuid']
        if 'version' in settings['index']:
            del settings['index']['version']

    # Read the schema
    schema = json.load(open("%s/schema.json" % index, "r"))

    schema = schema[main_index]
    if 'mappings' in schema:
        schema = schema['mappings']

    # Create the index on the server
    data = {"mappings": schema, "settings": settings}

    r = requests.put("%s/%s" % (url, main_index), data=json.dumps(data))
    if r.status_code != 200:
        print("Unable to put the index to the server (%i), aborting"
              % r.status_code)
        print(r.content)
        exit(1)

    # Load up the data files and put them all in
    data_files = os.listdir("%s/data" % index)
    for dfile in data_files:
        items = json.load(open("%s/data/%s" % (index, dfile)))
        if not items:
            continue
        bulk = ""
        for item in items:
            source = item["_source"]
            del item["_source"]
            if "_score" in item:
                del item["_score"]
            command = {"index": item}
            bulk = bulk + json.dumps(command) + "\n" + json.dumps(source) + "\n"
        print("Putting %i items" % len(items))
        r = requests.post("%s/_bulk" % url, data=bulk)
        if r.status_code != 200:
            print("Failed with code %i" % r.status_code)
            print(r.content)
            exit(1)

    # Create index alias if needed
    if main_index != index:
        alias = {"actions": [{"add": {"index": main_index, "alias": index}}]}
        r = requests.post("%s/_aliases" % url, data=json.dumps(alias))
        if r.status_code != 200:
            print("Unable to create the alias of the index (%s), aborting"
                  % main_index)
            print(r.content)
            exit(1)
        print("Setting alias {} -> {}".format(index, main_index))

    # Clean up the directory
    shutil.rmtree(index)

    print("Finished")


if __name__ == '__main__':
    run()
