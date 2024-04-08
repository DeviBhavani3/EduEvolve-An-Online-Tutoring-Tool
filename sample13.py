import streamlit as st
import requests
from datetime import datetime
from textblob import TextBlob  # Import TextBlob for sentiment analysis
import re
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import requests
import base64
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi

def get_udemy_courses():
    url = "https://www.udemy.com/api-2.0/courses/"
    client_id = "dnBvf97P8zBywkXuS1FKTuaMCraAK9c3rf8maPzn"
    client_secret = "cs0bug96p8avMWf6RGWRPu415aHLOuqLtAK4pX1eXGNghNX6dAsO8VxOGxW7dqxzfguxTCg2jbCTdJjNdjt1lUF2af6gMqy9qFbqlIjeaoJv3NNiGDC2H5xUbxLKY0MV"

    # Encode client_id and client_secret in base64
    encoded_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        courses = response.json()
        return courses
    else:
        print(f"Failed to fetch Udemy courses. Status code: {response.status_code}")
        return None

# Example usage
udemy_courses = get_udemy_courses()
API_KEY = 'AIzaSyAXI8RfY-zIPd6u9WZ5Vy4QKyE7y8Qdq6o'
BASE_URL = 'https://www.googleapis.com/youtube/v3/search'
VIDEO_DETAILS_URL = 'https://www.googleapis.com/youtube/v3/videos'
youtube = build("youtube", "v3", developerKey=API_KEY)

def parse_duration(duration_str):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration_str)
    hours = int(match.group(1)[:-1]) if match.group(1) else 0 if match.group(1) is not None else 0
    minutes = int(match.group(2)[:-1]) if match.group(2) else 0 if match.group(2) is not None else 0
    seconds = int(match.group(3)[:-1]) if match.group(3) else 0 if match.group(3) is not None else 0
    return hours * 3600 + minutes * 60 + seconds

def analyze_sentiment(text):
    analysis = TextBlob(text)
    # Classify sentiment as positive, negative, or neutral
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity < 0:
        return 'negative'
    else:
        return 'neutral'

def search_videos(query):
    params = {
        'part': 'snippet',
        'q': query,
        'key': API_KEY,
        'type': 'video',
        'maxResults': 100,  # Adjust as needed
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()
    videos = []
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        video_params = {
            'part': 'snippet,statistics,contentDetails',
            'id': video_id,
            'key': API_KEY, 
        }
        video_response = requests.get(VIDEO_DETAILS_URL, params=video_params)
        video_data = video_response.json()
        video_statistics = video_data['items'][0].get('statistics', {})
        like_count = int(video_statistics.get('likeCount', 0))
        video = {
            'title': video_data['items'][0]['snippet']['title'],
            'video_id': video_id,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'views': int(video_statistics.get('viewCount', 0)),
            'likes': like_count,
            'comments': int(video_statistics.get('commentCount', 0)),
            'length': parse_duration(video_data['items'][0]['contentDetails']['duration']),
            'channel_name': video_data['items'][0]['snippet']['channelTitle'],
            'date_posted': video_data['items'][0]['snippet']['publishedAt'],
        }
        videos.append(video)
    return videos

def display_results(videos, likes, views, freshness, length,topic):
    results = []  # Create an empty list to store results
    count = 0
    for video in videos:
        if video['likes'] > likes and video['views'] > views:
            video_length = video['length']
            short_video = video_length <= 900
            long_video = video_length > 900

            if freshness == "New" and int(video['date_posted'][0:4]) > 2021:
                if length == "Short" and short_video:
                    comments = get_video_comments(video['video_id'])
                    results.append((video, comments))  # Store the result in the list
                    count += 1
                elif length == "Long" and long_video:
                    comments = get_video_comments(video['video_id'])
                    results.append((video, comments))  # Store the result in the list
            elif freshness == "Old" and int(video['date_posted'][0:4]) <= 2020:
                if length == "Short" and short_video:
                    comments = get_video_comments(video['video_id'])
                    results.append((video, comments))  # Store the result in the list
                elif length == "Long" and long_video:
                    comments = get_video_comments(video['video_id'])
                    results.append((video, comments))  # Store the result in the list

    display_video_info(results,topic)  # Return the list of results



def get_video_comments(video_id):
    comments = []

    # Set up parameters for the request
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'key': API_KEY,  # Replace with your actual YouTube API key
        'maxResults': 100  # Adjust as needed
    }

    # Make the initial request to the YouTube API
    while True:
        response = requests.get('https://www.googleapis.com/youtube/v3/commentThreads', params=params)
        data = response.json()
        
        # Extract comments from the response
        if 'items' in data:
            for item in data['items']:
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment_text)
        
        # Check if there are more pages of comments
        if 'nextPageToken' in data:
            params['pageToken'] = data['nextPageToken']  # Set the token for the next page
        else:
            break  # Exit the loop if there are no more pages
        
    # Analyze sentiment of comments
    p = 0
    n = 0
    ne = 0
    for comment in comments:
        sentiment = analyze_sentiment(comment)
        if sentiment == 'positive':
            p += 1
        elif sentiment == 'negative':
            n += 1
        else:
            ne += 1
    
    print('positive comments: {}, negative comments: {}, neutral comments: {}'.format(p, n, ne))
    return p, n, ne
def display_video_info(results,topic):
    results=[x for x in results if sum(x[1])!=0]
    print(results)
    results.sort(key=lambda x: x[1][0] / sum(x[1]), reverse=True)  # Sort results by positive percentage in decreasing order
    flattened_results = []
    for course in udemy_courses['results']:
        flattened_course = {k: v for k, v in course.items() if k != 'visible_instructors'}
        for instructor in course.get('visible_instructors', []):
            flattened_course.update({f"instructor_{k}": v for k, v in instructor.items()})
        flattened_results.append(flattened_course)
    df = pd.DataFrame(flattened_results)
    try:
        course = df[df['title'].str.contains(topic, case=False, na=False)]
        for index, row in course.iterrows():
            st.write(f"Course: {row['title']}")
            st.write(f"Price: {row['price']}")
            st.write(f"Instructor: {row['instructor_name']}")
            st.write(f"URL: {'https://www.udemy.com' +row['url']}")
            st.divider()    
        else:
            pass
        for video, comments in results:
            st.video(video["url"])
            total_comments = sum(comments)
            if total_comments == 0:
                total_comments = 1
            positive_percentage = round((comments[0] / total_comments) * 100, 2)
            negative_percentage = round((comments[1] / total_comments) * 100, 2)
            neutral_percentage = round((comments[2] / total_comments) * 100, 2)

            if positive_percentage > negative_percentage:
                if positive_percentage > 75:
                    st.write(f'5💥')
                elif positive_percentage > 60:
                    st.write(f'4💥')
                elif positive_percentage > 45:
                    st.write(f'3💥')
                elif positive_percentage > 30:
                    st.write(f'2💥')
                else:
                    st.write(f'1💥')
            else:
                if negative_percentage > 75:
                    st.write(f'1💥')
                elif negative_percentage > 60:
                    st.write(f'2💥')
                elif negative_percentage > 45:
                    st.write(f'3💥')
                elif negative_percentage > 30:
                    st.write(f'4💥')
                else:
                    st.write(f'5💥')
            
            st.write(f"Positive Percentage: {positive_percentage}%")
            st.write(f"Negative Percentage: {negative_percentage}%")
            st.write(f"Neutral Percentage: {neutral_percentage}%")
            # Data for plotting
            labels = ['Positive', 'Negative', 'Neutral']
            sizes = [positive_percentage, negative_percentage, neutral_percentage]
            colors = ['green', 'red', 'gray']

            # Plotting
            fig, ax = plt.subplots()
            ax.bar(labels, sizes, color=colors)

            # Adding labels
            for i, v in enumerate(sizes):
                ax.text(i, v + 1, str(v) + '%', ha='center')

            # Adding title and labels
            ax.set_title('Sentiment Analysis')
            ax.set_ylabel('Percentage')

            # Display the plot using Streamlit
            st.pyplot(fig)
            try:
                text_dict = YouTubeTranscriptApi.get_transcript(video["url"].split("=")[1])
                combined_text = ' '.join(item['text'] for item in text_dict)
                st.write(combined_text)
                st.divider()
            except:
                pass
    except:
        pass      
def main():
    st.title("EduEvolve: An Online Tutoring Tool")
    st.sidebar.header("Settings")

    language_option = st.sidebar.selectbox("Select Language", ["English", "Hindi", "Telugu"])

    likes_option = st.sidebar.slider("Minimum Likes", min_value=0, max_value=100000, step=1000, value=0)

    views_option = st.sidebar.slider("Minimum Views", min_value=0, max_value=1000000, step=10000)

    freshness_option = st.sidebar.radio("Freshness", ["New", "Old"])

    content_level_option = st.sidebar.selectbox("Content Level", ["Beginner", "Intermediate", "Advanced"])

    length_option = st.sidebar.radio("Filter by Video Length", ["Short", "Long"])

    favorite_channel_option = st.sidebar.radio("Filter by Favorite Channel", ["Yes", "No"])

    # Main content
    topic = st.text_input("Enter a topic:")
    use_topic = topic
    if language_option == "English":
        topic = topic + " tutorial in english"
    elif language_option == "Hindi":
        topic = topic + " tutorial in hindi"
    elif language_option == "Telugu":
        topic = topic + " tutorial in telugu"
    else:
        pass
    if content_level_option == "Beginner":
        topic = topic + " for beginners"
    elif content_level_option == "Intermediate":
        topic = topic + " for intermediate"
    elif content_level_option == "Advanced":
        topic = topic + " for advanced"
    else:
        pass

    if st.button("Search"):
        result = search_videos(topic)
        
        if result:
            display_results(result, likes=int(likes_option), views=int(views_option),
                            freshness=freshness_option,
                            length=length_option,topic=use_topic)
            if favorite_channel_option == "Yes":
                st.subheader("Channels you may like:")
                
                channels = [
                    "@TutorialsPoint_",
                    "@khanacademy",
                    "@Intellipaat",
                    "@ApnaCollegeOfficial",
                    "@thenewboston",
                    "@krishnaik06",
                    "@EngineeringFunda",
                    "@CodeWithHarry",
                    "@JennyslecturesCSIT",
                    "@Telusko",
                    "@FeelFreetoLearn",
                    "@PhysicsWallah"
                ]

                for channel in channels:
                    youtube_link = f"https://www.youtube.com/@{channel[1:]}"  # Removing "@" from the username
                    st.markdown(f"[{channel}]({youtube_link})")
            else:
                pass
                
        else:
            st.warning("No videos found for the given topic.")
if __name__ == "__main__":
    main()
