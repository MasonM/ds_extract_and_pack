#!/usr/bin/env python

import os
import flickrapi
import requests

base_dir = "/home/masonm/src/darksouls"
download_dir = base_dir + "/flickr_images"

count = len(os.listdir(download_dir))

if count < 3600:
    api_key, secret = open('flickr_creds.txt', 'r').readlines()
    flickr = flickrapi.FlickrAPI(api_key.strip(), secret.strip(), format='etree')

    photos = flickr.walk(
        tag_mode='all',
        tags='christmas,santa',
        media='photos',
        extras='url_z',
        sort='relevance'
    )

    for photo in photos:
        if count > 3600:
            break

        out_path = "{}/{}.jpg".format(download_dir, photo.get('id'))
        if os.path.isfile(out_path):
            continue

        if not photo.get('url_z'):
            continue

        print("{}: Fetching {}".format(count, photo.get('url_z')))
        photo_response = requests.get(photo.get('url_z'))
        with open(out_path, "wb") as out_file:
            out_file.write(photo_response.content)
        count += 1
