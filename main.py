"""
YouTube Comment Fetcher
=======================

Fetches comments from a specific YouTube channel across videos from another channel's upload history.

SETUP:
1. Get a YouTube Data API v3 key from Google Cloud Console:
    https://console.cloud.google.com/apis/credentials
2. Fing the channel IDs (not @handles) from YouTube source code:
    - Open channel page -> CTRL+U -> search for "channelId":"UC"
3. Fill int the variables below
4. Run: python main.py
"""

import requests, json
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========
# Fill these before running
API_KEY = "YOUR_API_KEY_HERE"              # Google Cloud Console API Key
SOURCE_CHANNEL_ID = "UC..."                # Channel ID to scan videos from
TARGET_CHANNEL_ID = "UC..."                # Channel ID whose comments to fetch
YEARS_BACK = 3                             # How many years back to scan
# ===================================

BASE_URL = "https://www.googleapis.com/youtube/v3"


def get_videos(channel_id, api_key, years_back):
    """
    Fetch all videos from a channel published within the last N years.
    Uses pagination to handle channels with many videos.
    """
    # Calculate cutoff date for filtering
    cutoff_date = (datetime.utcnow() - timedelta(days=years_back * 365)).isoformat("T") + "Z"
    
    videos = []
    next_page_token = None
    
    # Paginate through results (max 50 per request)
    while True:
        params = {
            "key": api_key,
            "channelId": channel_id,
            "part": "snippet",
            "order": "date",
            "type": "video",
            "publishedAfter": cutoff_date,
            "maxResults": 50
        }
        if next_page_token:
            params["pageToken"] = next_page_token
            
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=30)
        data = response.json()
        
        # Handle API errors
        if "error" in data:
            print("ERROR:", data["error"]["message"])
            break
            
        # Extract video info
        for item in data.get("items", []):
            videos.append({
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "date": item["snippet"]["publishedAt"]
            })
        
        # Check for more pages
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
            
    return videos


def get_comments(video_id, api_key, target_channel_id):
    """
    Fetch all comments from a video and filter by target channel ID.
    Checks both top-level comments and replies.
    """
    comments = []
    next_page_token = None
    
    while True:
        params = {
            "key": api_key,
            "videoId": video_id,
            "part": "snippet",
            "maxResults": 100,
            "order": "time"
        }
        if next_page_token:
            params["pageToken"] = next_page_token
            
        response = requests.get(f"{BASE_URL}/commentThreads", params=params, timeout=30)
        data = response.json()
        
        # Skip videos with comments disabled or no comments
        if "error" in data:
            break
            
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            author_id = snippet.get("authorChannelId", {}).get("value", "")
            
            # Check if top-level comment matches target channel
            if author_id == target_channel_id:
                comments.append({
                    "video_id": video_id,
                    "author": snippet["authorDisplayName"],
                    "text": snippet["textDisplay"],
                    "date": snippet["publishedAt"],
                    "likes": snippet["likeCount"]
                })
            
            # Check replies to this comment
            if "replies" in item:
                for reply in item["replies"]["comments"]:
                    reply_snippet = reply["snippet"]
                    reply_author_id = reply_snippet.get("authorChannelId", {}).get("value", "")
                    
                    if reply_author_id == target_channel_id:
                        comments.append({
                            "video_id": video_id,
                            "author": reply_snippet["authorDisplayName"],
                            "text": reply_snippet["textDisplay"],
                            "date": reply_snippet["publishedAt"],
                            "likes": reply_snippet["likeCount"],
                            "reply": True
                        })
        
        # Paginate if more comments exist
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
            
    return comments


def save_to_txt(videos, all_comments, filename):
    """
    Save results to a formatted text file for human readability.
    Includes video titles, links, and all matching comments with metadata.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # Header section
        f.write("=" * 70 + "\n")
        f.write("YOUTUBE COMMENT FETCHER RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Search Date: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"Source Channel: {SOURCE_CHANNEL_ID}\n")
        f.write(f"Target Channel: {TARGET_CHANNEL_ID}\n")
        f.write(f"Total Videos Scanned: {len(videos)}\n")
        f.write(f"Total Comments Found: {sum(len(v['comments']) for v in all_comments)}\n")
        f.write("=" * 70 + "\n\n")
        
        if not all_comments:
            f.write("NO COMMENTS FOUND.\n")
            return
        
        # Write each video's comments
        for idx, video_group in enumerate(all_comments, 1):
            video_title = video_group['video_title']
            video_url = video_group['video_url']
            comments = video_group['comments']
            
            f.write(f"\n{'─' * 70}\n")
            f.write(f"VIDEO #{idx}: {video_title}\n")
            f.write(f"LINK: {video_url}\n")
            f.write(f"COMMENTS FOUND: {len(comments)}\n")
            f.write(f"{'─' * 70}\n")
            
            for c_idx, comment in enumerate(comments, 1):
                comment_type = "[REPLY]" if comment.get('reply') else "[COMMENT]"
                f.write(f"\n  {comment_type} #{c_idx}\n")
                f.write(f"  Author: {comment['author']}\n")
                f.write(f"  Date: {comment['date']}\n")
                f.write(f"  Likes: {comment['likes']}\n")
                f.write(f"  Text:\n")
                
                # Wrap long text with indentation
                text = comment['text']
                text = text.replace('<br>', '\n').replace('<br/>', '\n')
                for line in text.split('\n'):
                    f.write(f"    {line}\n")
                
                f.write("\n")
        
        f.write(f"\n{'=' * 70}\n")
        f.write("END OF REPORT\n")


def main():
    """Main execution flow: scan videos, fetch comments, save results."""
    print("=" * 50)
    print("YOUTUBE COMMENT FETCHER")
    print("=" * 50)
    
    print("\nFetching video list...")
    videos = get_videos(SOURCE_CHANNEL_ID, API_KEY, YEARS_BACK)
    print(f"Found {len(videos)} videos.\n")
    
    all_comments = []
    
    # Process each video
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] Scanning: {video['title'][:50]}...")
        comments = get_comments(video["id"], API_KEY, TARGET_CHANNEL_ID)
        
        if comments:
            print(f"  -> {len(comments)} comment(s) found!")
            all_comments.append({
                "video_title": video["title"],
                "video_url": f"https://youtube.com/watch?v={video['id']}",
                "comments": comments
            })
    
    # Generate output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_file = f"comment_results_{timestamp}.txt"
    json_file = f"comment_results_{timestamp}.json"
    
    # Save formatted text report
    save_to_txt(videos, all_comments, txt_file)
    
    # Save raw JSON for programmatic use
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "search_date": datetime.now().isoformat(),
            "source_channel": SOURCE_CHANNEL_ID,
            "target_channel": TARGET_CHANNEL_ID,
            "total_videos": len(videos),
            "total_comments": sum(len(v['comments']) for v in all_comments),
            "results": all_comments
        }, f, ensure_ascii=False, indent=2)
    
    total = sum(len(v['comments']) for v in all_comments)
    print(f"\n{'=' * 50}")
    print(f"DONE! Total comments found: {total}")
    print(f"TXT Report: {txt_file}")
    print(f"JSON Data: {json_file}")


if __name__ == "__main__":
    main()