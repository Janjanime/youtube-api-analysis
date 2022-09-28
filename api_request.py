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
from IPython.display import JSON
# %%
youtube_api_key= 'AIzaSyAwaq4T4D7A3DPI12aL7LMOnxLRQexoDFA'
channel_ids = ['UCcmxOGYGF51T1XsqQLewGtQ',
    # more channel ids
]

#%%
api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=youtube_api_key)

#%%
#Channel APIs
def get_channel_stats(youtube, channel_ids):
    
    all_data = []

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()

    #loop through items
    for item in response['items']:
        data = {'channelName': item['snippet']['title'],
                'subscribers': item['statistics']['subscriberCount'],
                'views': item['statistics']['viewCount'],
                'totalVideos': item['statistics']['videoCount'],
                'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
        }

        all_data.append(data)

    return(pd.DataFrame(all_data))
# %%
channel_stats = get_channel_stats(youtube, channel_ids)
print(channel_stats)
# %%
