import argparse
import json
import os
import shutil
import tarfile
from datetime import datetime

import requests


def run():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--index", help="The name of the index to backup",
                        type=str, required=True)
    parser.add_argument("--host", help="The elasticsearch host.",
                        type=str, required=False, default='localhost')
    parser.add_argument("--port", help="The elasticsearch port.",
                        type=str, required=False, default="9200")
    parser.add_argument("--chunksize", help="Size of each bulk operation.",
                        type=int, required=False, default=100)
    args = parser.parse_args()

    # Get the elasticsearch server
    host = args.host
    port = args.port
    index = args.index

    url = "http://%s:%s" % (host, port)
    print("Using ElasticSearch at %s" % url)

    try:
        r = requests.get(url)
        if r.status_code != 200:
            print("Error hitting ElasticSearch on %s, response code was %i" % (
                url, r.status_code))
            exit(1)
        else:
            print("Verified ElasticSearch server")
    except:
        print("Unable to hit ElasticSearch on %s" % url)
        exit(1)

    # Check with the user
    print("Backing up index '%s'" % index)
    print("Ctrl+C now to abort...")

    # time.sleep(3)

    # Make the directories we need
    print("Checking write permission to current directory")
    try:
        os.mkdir(index)
        os.mkdir("%s/data" % index)
    except FileExistsError:
        print("Unable to write to the current directory, " +
              "because it already exists.")
        exit(1)
    except:
        print("Unable to write to the current directory, " +
              "please resolve this and try again")
        exit(1)

    # Download and save the settings
    print("Downloading '%s' settings" % index)

    r = requests.get("%s/%s/_settings" % (url, index))
    if r.status_code != 200:
        print("Unable to get settings for index '%s', error code: %i" % (
            index, r.status_code))
        exit(1)

    json.dump(r.json(), open("%s/settings.json" % index, "w"))

    # Download and save the schema
    print("Downloading '%s' schema" % index)

    r = requests.get("%s/%s/_mapping" % (url, index))
    if r.status_code != 200:
        print("Unable to get schema for index '%s', error code: %i" % (
            index, r.status_code))
        exit(1)

    json.dump(r.json(), open("%s/schema.json" % index, "w"))

    # Download the data
    count = 0

    query = {
        "size": args.chunksize,
        "query": {
            "match_all": {}
        }
    }

    r = requests.post("{url}/{index}/_search?scroll=10m".format(
                      url=url, index=index), json=query)

    data = r.json()
    scroll_id = data["_scroll_id"]
    number = len(data["hits"]["hits"])
    print("Pass %i: Got %i results" % (count, number))
    finished = number < 1
    if not finished:
        json.dump(data["hits"]["hits"],
                  open("%s/data/%i.json" % (index, count), "w"))

    while not finished:
        count += 1
        query = {
            "scroll": "10m",
            "scroll_id": scroll_id
        }
        r = requests.post("{url}/_search/scroll".format(
            url=url, index=index), json=query)

        data = r.json()
        scroll_id = data["_scroll_id"]
        number = len(data["hits"]["hits"])
        print("Pass %i: Got %i results" % (count, number))

        finished = number < args.chunksize
        json.dump(data["hits"]["hits"],
            open("%s/data/%i.json" % (index, count), "w"))

    # Zip up the data
    filename = "{index}_{time}.esbackup.tar.gz".format(
        index=index, time=datetime.now().strftime('%Y%m%d_%H%M%S'))
    tar = tarfile.open(filename, "w:gz")
    tar.add(index)
    tar.close()

    # Delete the directory
    shutil.rmtree(index)

    print("Complete. Your file is:")
    print(filename)
    exit(0)


if __name__ == '__main__':
    run()
