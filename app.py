
from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
import supabase

app = Flask(__name__)

SUPABASE_URL = "https://ldkbzfcoewzynxawicxg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxka2J6ZmNvZXd6eW54YXdpY3hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU4NjQwMDQsImV4cCI6MjAzMTQ0MDAwNH0.sE_JK5ZbobAOzWKR6osasEVfZPWhVt08NhRf0XgrsmA"

# Initialize Supabase client
sb = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_review_count(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the span tag containing the review count
        review_span = soup.find('span', string=lambda text: text and '(' in text and ')' in text)

        if review_span:
            # Extract the text inside the parentheses and remove any non-numeric characters
            review_count_text = review_span.get_text(strip=True)
            review_count = ''.join(filter(str.isdigit, review_count_text))
            return int(review_count)
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: An error occurred while fetching the website: {e}")
        return None

def insert_review_count(count):
    try:
        # Check if the record with id=1 already exists
        review_counts_table = sb.table('review_counts')
        existing_record = review_counts_table.select('*').eq('id', 1).execute()

        # Upsert the record with id=1 and the provided count
        review_counts_table.upsert({"id": 1, "count": count}, on_conflict='id').execute()
    except Exception as e:
        print(f"Error: {e}")

@app.route('/')
def index():
    # Hardcoded URL for demonstration purposes
    website_url = "https://www.google.com/search?q=tharakans+royal+jewellery+kunnamkulam&sca_esv=89411bb37f4aa9f8&sca_upv=1&sxsrf=ADLYWILIV0DyK2N0KvOJ-LjlgLynA8U_DQ%3A1715775994290&ei=-qlEZtysEZWbseMPityT2AY&oq=tharakans+royal+kunnamkulam&gs_lp=Egxnd3Mtd2l6LXNlcnAiG3RoYXJha2FucyByb3lhbCBrdW5uYW1rdWxhbSoCCAAyBhAAGAgYHjIGEAAYCBgeMggQABiABBiiBDIIEAAYgAQYogRIgDBQ4hNYtx9wAXgBkAEAmAHDAaABowqqAQQwLjEwuAEByAEA-AEBmAIKoALsCcICChAAGLADGNYEGEfCAg0QLhiABBjHARgNGK8BwgIIEAAYBxgIGB7CAggQABgIGA0YHsICHBAuGIAEGMcBGA0YrwEYlwUY3AQY3gQY4ATYAQHCAgsQABiABBiGAxiKBZgDAIgGAZAGCLoGBggBEAEYFJIHAzEuOaAH4z0&sclient=gws-wiz-serp"
    review_count = extract_review_count(website_url)
    if review_count:
        insert_review_count(review_count)
        return render_template('index.html', review_count=review_count)
    else:
        return "Review count not found."

if __name__ == '__main__':
    app.run(debug=True)