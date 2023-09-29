import streamlit as st
import yt_dlp
from io import BytesIO
import base64
import requests
from requests.exceptions import ChunkedEncodingError
import time

def download_youtube_video(url, resolution):
    try:
        ydl_opts = {
            'format': f'best[height<={resolution}]',
            'progress_hooks': [download_progress_hook],
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if 'url' in info_dict:
                video_url = info_dict['url']
                title = info_dict['title']
                views = info_dict.get('view_count', 'N/A')
                likes = info_dict.get('like_count', 'N/A')
                duration = info_dict.get('duration', 'N/A')

                st.success(f"Video information fetched: {title}")
                return video_url, title, views, likes, duration
            else:
                st.error("Video download link not found.")
                return None, None, None, None, None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None, None, None, None, None

def download_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d['_percent_str']
        speed = d['_speed_str']
        eta = d['_eta_str']
        st.write(f"Downloading... {percent} complete ({speed}, ETA: {eta})")

def download_video_with_retry(url, resolution, max_retries=3):
    for _ in range(max_retries):
        try:
            video_url, title, views, likes, duration = download_youtube_video(url, resolution)
            return video_url, title, views, likes, duration
        except ChunkedEncodingError as e:
            st.error(f"Error downloading video: {str(e)}")
            st.warning("Retrying in a moment...")
            time.sleep(5)  # Wait for a few seconds before retrying
    st.error("Failed to download video after multiple attempts.")
    return None, None, None, None, None

def perform_youtube_search(query):
    try:
        ydl_opts = {
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
            videos = []
            for result in search_results['entries']:
                title = result.get('title', 'N/A')
                url = result.get('url', 'N/A')
                videos.append({'title': title, 'url': url})
            return videos
    except Exception as e:
        st.error(f"An error occurred during the search: {str(e)}")
        return []

def main():
    st.title("DR-Media Downloader")
    media_choice = st.radio("Choose Media", ["YouTube", "Search"])

    if media_choice == "YouTube":
        url = st.text_input("Enter the video URL")
        resolution = st.selectbox("Choose Resolution", ["144p", "240p", "360p", "480p", "720p"])
        
        if st.button("Download YouTube Video") and url:
            selected_resolution = {"144p": 144, "240p": 240, "360p": 360, "480p": 480, "720p": 720}.get(resolution, 720)
            video_url, title, views, likes, duration = download_video_with_retry(url, selected_resolution)
            
            if video_url and title:
                st.write("Video Metadata:")
                st.write(f"- Title: {title}")
                st.write(f"- Views: {views}")
                st.write(f"- Likes: {likes}")
                st.write(f"- Duration: {duration} seconds")
                
                # Display video URL
                st.write(f"Video URL: {video_url}")

                # Create a download link that behaves like a button
                st.markdown(get_video_download_link(video_url, title), unsafe_allow_html=True)

    elif media_choice == "Search":
        st.header("Search for YouTube Videos")
        search_query = st.text_input("Enter your search query")
        if st.button("Search"):
            search_results = perform_youtube_search(search_query)
            if search_results:
                st.header("Search Results:")
                for video in search_results:
                    st.write(f"- [{video['title']}]({video['url']})")
            else:
                st.warning("No search results found.")

def get_video_download_link(video_url, title):
    response = requests.get(video_url)
    video_data = BytesIO(response.content)
    b64 = base64.b64encode(video_data.getvalue()).decode()
    return f'<a href="data:video/mp4;base64,{b64}" download="{title}.mp4" style="text-decoration: none; background-color: #008CBA; color: #ffffff; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Download {title}</a>'

if __name__ == "__main__":
    main()
