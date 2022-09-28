#%%
# -*- coding: utf-8 -*-

# Sample Python code for youtube.channels.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
# %%
youtube_api_key= 'AIzaSyAwaq4T4D7A3DPI12aL7LMOnxLRQexoDFA'

api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=youtube_api_key)

request = youtube.channels().list(
    part="snippet,contentDetails,statistics",
    id="UC_x5XG1OV2P6uZZ5FSM9Ttw"
)
response = request.execute()

print(response)
# %%
