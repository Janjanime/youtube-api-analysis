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
#piece of code from youtube API for playlist list
request = youtube.playlistItems().list(
    part="snippet,contentDetails",
    playlistId="UUcmxOGYGF51T1XsqQLewGtQ"
)
response = request.execute()

JSON(response)

#%%
playlist_id = 'UUcmxOGYGF51T1XsqQLewGtQ'

#Creating a function to return playlist video information
def get_video_ids(youtube, playlist_id):

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId="UUcmxOGYGF51T1XsqQLewGtQ",
    #API docs state that results default to 5, so we specify max
        maxResults = 50
        )

    response = request.execute()

    #Make a list of video IDs
    video_ids = []

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    more_pages = True
    
    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                        part='contentDetails',
                        playlistId = playlist_id,
                        maxResults = 50,
                        pageToken = next_page_token
                        )
            response = request.execute()
    
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
        
    return video_ids

#%%
video_ids = get_video_ids(youtube, playlist_id)
len(video_ids)

#%%
#Video list API

request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    id=video_ids[0:5]
)
response = request.execute()
JSON(response)
# %%
def get_video_details(youtube,video_ids):
    all_video_info = []

    for i in range(0, len(video_ids),50):
        request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                    'statistics': ['viewCount', 'likeCount', 'favoriteCount', 'commentCount'],
                    'contentDetails': ['duration', 'definition', 'caption'] 
            }

            video_info = {}
            video_info['video_id']= video['id']

            for k in stats.keys():
                for v in stats[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)
            
    return pd.DataFrame(all_video_info)

#%%
video_dataframe = get_video_details(youtube,video_ids)

video_dataframe
# %%
print(video_ids[0:5])
#%%
#can use the same methodology to create a function for comments

def get_comments_in_videos(youtube, video_ids):

    all_comments = []

    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id
            )
            response = request.execute()

            comments_in_video = [comment['snippet']['topLevelComment']['snippet']['textOriginal'] for comment in response['items'][0:10]]
            comments_in_video_info = {'video_id': video_id, 'comments': comments_in_video}

            all_comments.append(comments_in_video_info)
            
        except: 
            # When error occurs - most likely because comments are disabled on a video
            print('Could not get comments for video ' + video_id)
        
    return pd.DataFrame(all_comments)

# %%
comments_dataframe = get_comments_in_videos(youtube,video_ids[0:5])

comments_dataframe
# %%
