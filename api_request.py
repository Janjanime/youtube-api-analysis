#%%
import os
import pandas as pd
import numpy as np
from dateutil import parser
from IPython.display import JSON
import isodate

#Google API
import googleapiclient.discovery

# NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
from wordcloud import WordCloud

#%%

def get_channel_stats(youtube, channel_ids):
    """
    Dataframe containing the channel statistics for all channels in the provided list: title, subscriber count, view count, video count, upload playlist
    """
    all_data = []

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()

    #loop through items
    for i in range(len(response['items'])):
        data = dict(channelName = response['items'][i]['snippet']['title'],
                subscribers = response['items'][i]['statistics']['subscriberCount'],
                views = response['items'][i]['statistics']['viewCount'],
                totalVideos = response['items'][i]['statistics']['videoCount'],
                playlistId = response['items'][i]['contentDetails']['relatedPlaylists']['uploads']
        )

        all_data.append(data)

    return(pd.DataFrame(all_data))

#%%

def get_video_ids(youtube, playlist_id):
    """List of video IDs of all videos in the playlist"""

    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
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

# %%

def get_video_details(youtube,video_ids):
    """
    Dataframe with statistics of videos, i.e.:
        'channelTitle', 'title', 'description', 'tags', 'publishedAt'
        'viewCount', 'likeCount', 'favoriteCount', 'commentCount'
        'duration', 'definition', 'caption'
    """
    
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

def get_comments_in_videos(youtube, video_ids):
    """Dataframe with video IDs and associated top level comment in text."""

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
