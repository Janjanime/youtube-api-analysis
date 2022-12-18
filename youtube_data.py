#%%
import api_request as api

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

channel_ids = [ 'UCiM8arBZ-GyuBFG3wy6fEgw', #Hwasa
                'UC9Gxb0gMCh3EPIDLQXeQUog', #Chung ha Official
                'UCsVpgRB8YHLWA0ZrkhtHvTA', #Sunmi
                'UC8GmeiLd5xjh2j5VmdePWQw', #BIBI
                'UCXOMKEPp0CALdBSPkReI5BQ', #Wheein
                'UC0uTcuuOtUFwtn9aKUVGjXg', #Hyuna
                'UCN2bQLTTvNPZWCWU5TYghKA', #Jessi
    # more channel ids
]

# Get credentials and create an API client
api_service_name = "youtube"
api_version = "v3"

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=youtube_api_key)

#%%
#Running functions
channel_stats = api.get_channel_stats(youtube, channel_ids)
type(channel_stats)
print(channel_stats)
# %%
#Channel exploration
channel_stats.dtypes

number_cols = ['subscribers', 'views', 'totalVideos']
channel_stats[number_cols] = channel_stats[number_cols].apply(pd.to_numeric, errors='coerce')

# %%
# Number of subscribers per channel to have a view of how popular the channels are when compared with one another.
sns.set(rc={'figure.figsize':(10,8)})
ax = sns.barplot(x='channelName', y='subscribers', data=channel_stats.sort_values('subscribers', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

# %%
#rank considering the total number of views of the channels
sns.set(rc={'figure.figsize':(10,8)})
ax = sns.barplot(x='channelName', y='views', data=channel_stats.sort_values('views', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))

plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)

#%%
# Create main dataframes for video details and comments
video_df = pd.DataFrame()
comments_df = pd.DataFrame()

# Get video Ids from playlist data while loading each channel
for c in channel_stats['channelName'].unique(): #try group by instead of unique
    print('Loading information from ' + c )
    channel_playlist_id=channel_stats.loc[channel_stats['channelName']==c, 'playlistId'].iloc[0]
    video_ids = api.get_video_ids(youtube,channel_playlist_id)

    #get video details
    video_data = api.get_video_details(youtube, video_ids)

    #get comments on videos
    comment_data = api.get_comments_in_videos(youtube, video_ids)

    #combine comment and video detail data
    video_df = video_df.append(video_data, ignore_index=True)
    comments_df = comments_df.append(comment_data, ignore_index=True)

#%%
video_df.head()
#%%
comments_df
#%%
#Data Pre-processing
video_df.isnull().any()

#%%
video_df.dtypes

#%%
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
histogram = sns.histplot(data = video_df, x = 'durationSeconds', bins=50)
plt.xlim(0,1500)
# can also view on a logrithmic scale using
# histogram.set_yscale('log')

#%%
#Creating a word cloud from video comments
stop_words = set(stopwords.words(['english']))
comments_df['title_no_stopwords'] = comments_df['comments'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in comments_df['title_no_stopwords'].tolist() for a in b])
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

