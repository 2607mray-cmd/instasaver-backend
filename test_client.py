import urllib.request
import json
import sys

def test_download():
    url = "http://localhost:8000/download"
    # A short video for testing purposes (Rick Astley sample or similar legal test video)
    # Using a known short video ID or URL.
    # Let's use a very short video to avoid huge downloads.
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo (first youtube video)
    
    data = json.dumps({"url": video_url}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    print(f"Sending request to {url} with video {video_url}...")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Success! Downloading file...")
                content_disposition = response.info().get('Content-Disposition')
                print(f"Content-Disposition: {content_disposition}")
                
                with open('downloaded_video.mp4', 'wb') as f:
                    f.write(response.read())
                print("Video saved to downloaded_video.mp4")
            else:
                print(f"Failed with status code: {response.status}")
                print(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_download()
