#%%
import os
import pandas as pd
import numpy as np
from dateutil import parser
from IPython.display import JSON
import isodate

#Google API
import googleapiclient.discovery

#Data Vizualization libraries
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
sns.set(style="darkgrid", color_codes=True)


# NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
from wordcloud import WordCloud

# %%
youtube_api_key= 'AIzaSyAwaq4T4D7A3DPI12aL7LMOnxLRQexoDFA'

channel_ids = [ 'UCcmxOGYGF51T1XsqQLewGtQ', #TrashTaste
                'UCuqmPL64ad8FW7cW0x2YV8g', #EmilyArtful
                #'UC-lHJZR3Gqxm24_Vd_AJ5Yw', #Pewdiepie
                'UC2UXDak6o7rBm23k3Vv5dww', #TinaHuang
                'UCFeqAfEuKm7lIg2ddQzh61A', #Emichiru
                'UCJQJAI7IjbLcpsjWdSzYz0Q', #Thu Vu
                'UC2Ds30pkifFVD0CE08wF50g', #Daidus
    # more channel ids
]

# Get credentials and create an API client
api_service_name = "youtube"
api_version = "v3"

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=youtube_api_key)

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

#%%
#Running functions
get_channel_stats(youtube, channel_ids)

video_ids = get_video_ids(youtube, 'UUJQJAI7IjbLcpsjWdSzYz0Q')
video_df = get_video_details(youtube, video_ids)
video_df

#%%
#Data Pre-processing

video_df.isnull().any()

video_df.dtypes
#change datatypes to numeric where relevant
numeric_cols = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
video_df[numeric_cols] = video_df[numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)

#create a column for Published day in the week
video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: parser.parse(x))
video_df['publishDayName'] = video_df['publishedAt'].apply(lambda x: x.strftime("%A"))

#change date type from Youtube API duration to seconds
video_df['durationSeconds'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
video_df['durationSeconds'] = video_df['durationSeconds'
].astype('timedelta64[s]')
video_df[['durationSeconds', 'duration']]

#add a tag count
video_df['tagsCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))

# Comments and likes per 1000 view ratio
video_df['likeRatio'] = video_df['likeCount']/ video_df['viewCount'] * 1000
video_df['commentRatio'] = video_df['commentCount']/ video_df['viewCount'] * 1000

# Title character length
video_df['titleLength'] = video_df['title'].apply(lambda x: len(x))

#%%
video_df.tail()

#%%
#Exploratory Data Analysis
top_10_videos = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending=False)[0:10])
best_plot = top_10_videos.set_xticklabels(top_10_videos.get_xticklabels(), rotation=90)
top_10_videos.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))

#%%
last_10_videos = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending=True)[0:10])
worst_plot = last_10_videos.set_xticklabels(last_10_videos.get_xticklabels(), rotation=90)
last_10_videos.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))

#%%
#View distribution per video
sns.violinplot(video_df['channelTitle'], video_df['viewCount'])
#can be useful if you want to compare several channels together

#%%
#Views vs likes and comments
fig, top_10_videos = plt.subplots(1,2)
sns.scatterplot(data = video_df, x = 'commentCount', y = 'viewCount', ax = top_10_videos[0])
sns.scatterplot(data = video_df, x = 'likeCount', y = 'viewCount', ax = top_10_videos[1])

#%%
#Video duration
sns.histplot(data = video_df, x = 'durationSeconds', bins=30)

#%%
#Creating a word cloud from video titles
stop_words = set(stopwords.words('english'))
video_df['title_no_stopwords'] = video_df['title'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in video_df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words)

def plot_cloud(wordcloud):
    plt.figure(figsize=(30,20))
    plt.imshow(wordcloud)
    plt.axis("off");


wordcloud = WordCloud(width=2000, height=1000, random_state=1, background_color='black',
                        colormap='viridis', collocations=False).generate(all_words_str)

plot_cloud(wordcloud)

#%%
#Upload Schedule
day_df = pd.DataFrame(video_df['publishDayName'].value_counts())
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_df = day_df.reindex(weekdays)
ax = day_df.reset_index().plot.bar(x='index', y='publishDayName', rot=0)

#%%
channel_stats = get_channel_stats(youtube, channel_ids)
print(channel_stats)

#changing a dataframe into a dictionary and returning a list
channel_dict = channel_stats.to_dict('list')
extract_playlist_id = channel_dict['playlistId']
print(extract_playlist_id)

#%%
#Using playlist from gett_channel_stats to find videos
test_video_ids = get_video_ids(youtube, 'UUcmxOGYGF51T1XsqQLewGtQ')

video_dataframe = get_video_details(youtube,test_video_ids)
video_dataframe
# %%
comments_dataframe = get_comments_in_videos(youtube,test_video_ids[0:5])
comments_dataframe

# %%
#Channel exploration
channel_data = get_channel_stats(youtube, channel_ids)
channel_data.dtypes

number_cols = ['subscribers', 'views', 'totalVideos']
channel_data[number_cols] = channel_data[number_cols].apply(pd.to_numeric, errors='coerce')

# %%
# Number of subscribers per channel to have a view of how popular the channels are when compared with one another.
sns.set(rc={'figure.figsize':(10,8)})
ax = sns.barplot(x='channelName', y='subscribers', data=channel_data.sort_values('subscribers', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

# %%
#rank considering the total number of views of the channels
sns.set(rc={'figure.figsize':(10,8)})
ax = sns.barplot(x='channelName', y='views', data=channel_data.sort_values('views', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))

plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

# %%
