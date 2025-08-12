import os 
import csv 
import datetime 
from instaloader import Instaloader, exceptions  
from dotenv import load_dotenv

NUM_POSTS = 7
MAX_DAYS = 5 

load_dotenv()

def get_hashtags_posts(query, num_posts=NUM_POSTS, max_days=MAX_DAYS):
    loader = Instaloader()

    username = os.getenv("IG_USERNAME")
    if not username:
        raise ValueError("Missing IG_USERNAME in .env file")

    # Load session from saved file
    try:
        loader.load_session_from_file(username)
        print(f"[INFO] Loaded saved session for {username}")
    except FileNotFoundError:
        raise RuntimeError(
            f"Session file not found for {username}. "
            f"Run 'instaloader --login={username}' in terminal first."
        )

    try:
        posts = loader.get_hashtag_posts(query)
    except exceptions.QueryReturnedNotFoundException:
        print(f"[ERROR] Instagram hashtag scraping is currently unavailable for #{query}.")
        print("        This is likely due to recent Instagram changes.")
        return []
    
    data = []
    header = ['post number', 'caption', 'url']
    count = 0
    current_date = datetime.datetime.now() 

    caption = ''
    url = '' 

    total_num_posts = 0
    for post in posts: 
        if post.caption is None: 
             continue 
        if (current_date - post.date).days > max_days: 
             break 
        
        total_num_posts += 1 
        caption = post.caption 
        url = f"instagram.com/p/{post.shortcode}" 

        image_name = f"{query}_{total_num_posts}.jpg"
        loader.download_pic(image_name, post.url, post.date_utc)

        data.append([total_num_posts, caption, url]) 

        if total_num_posts >= num_posts:
            break
         
    csv_filename = f"{query}_posts.csv"
    with open(csv_filename, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

    return data

if __name__ == "__main__":
    load_dotenv()
    hashtag = input("Enter hashtag (without #): ").strip()
    results = get_hashtags_posts(hashtag)
    print(f"Saved {len(results)} posts for #{hashtag}")