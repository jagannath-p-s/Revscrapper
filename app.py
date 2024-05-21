from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup
import requests
import supabase
import time

app = Flask(__name__)

SUPABASE_URL = "https://ldkbzfcoewzynxawicxg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxka2J6ZmNvZXd6eW54YXdpY3hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU4NjQwMDQsImV4cCI6MjAzMTQ0MDAwNH0.sE_JK5ZbobAOzWKR6osasEVfZPWhVt08NhRf0XgrsmA"

REVIEW_LINK = "https://search.google.com/local/writereview?placeid=ChIJJ6NJOESVpzsRIt_GsR8GqBM"
EXTRACTION_URL = "https://www.google.com/search?q=tharakans+royal+jewellery+kunnamkulam&sca_esv=89411bb37f4aa9f8&sca_upv=1&sxsrf=ADLYWILIV0DyK2N0KvOJ-LjlgLynA8U_DQ%3A1715775994290&ei=-qlEZtysEZWbseMPityT2AY&oq=tharakans+royal+kunnamkulam&gs_lp=Egxnd3Mtd2l6LXNlcnAiG3RoYXJha2FucyByb3lhbCBrdW5uYW1rdWxhbSoCCAAyBhAAGAgYHjIGEAAYCBgeMggQABiABBiiBDIIEAAYgAQYogRIgDBQ4hNYtx9wAXgBkAEAmAHDAaABowqqAQQwLjEwuAEByAEA-AEBmAIKoALsCcICChAAGLADGNYEGEfCAg0QLhiABBjHARgNGK8BwgIIEAAYBxgIGB7CAggQABgIGA0YHsICHBAuGIAEGMcBGA0YrwEYlwUY3AQY3gQY4ATYAQHCAgsQABiABBiGAxiKBZgDAIgGAZAGCLoGBggBEAEYFJIHAzEuOaAH4z0&sclient=gws-wiz-serp"

sb = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.ico', mimetype='image/x-icon')

def extract_review_count(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        review_span = soup.find('span', string=lambda text: text and '(' in text and ')' in text)

        if review_span:
            review_count_text = review_span.get_text(strip=True)
            review_count = ''.join(filter(str.isdigit, review_count_text))
            return int(review_count)
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: An error occurred while fetching the website: {e}")
        return None

def get_current_review_count():
    try:
        review_counts_table = sb.table('review_counts')
        record = review_counts_table.select('count').eq('id', 1).execute()
        if record.data:
            return record.data[0]['count']
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def insert_or_update_review_count(count):
    try:
        review_counts_table = sb.table('review_counts')
        review_counts_table.upsert({"id": 1, "count": count}, on_conflict='id').execute()
    except Exception as e:
        print(f"Error: {e}")

def update_salesman_points(salesman_id):
    try:
        salesmen_table = sb.table('salesmen')
        record = salesmen_table.select('points').eq('id', salesman_id).execute()
        if record.data:
            current_points = record.data[0]['points'] or 0
            new_points = current_points + 1
            salesmen_table.update({"points": new_points}).eq('id', salesman_id).execute()
    except Exception as e:
        print(f"Error: {e}")

@app.route('/app/<int:salesman_id>')
def app_route(salesman_id):
    current_review_count = get_current_review_count()
    if current_review_count is not None:
        review_url = REVIEW_LINK
        return render_template('review.html', salesman_id=salesman_id, review_count=current_review_count, review_url=review_url)
    else:
        return "Error fetching review count from database."

@app.route('/check_review_increment/<int:salesman_id>', methods=['GET'])
def check_review_increment(salesman_id):
    initial_count = get_current_review_count()
    if initial_count is None:
        return jsonify({"status": "error", "message": "Error fetching initial review count."})

    new_count = extract_review_count(EXTRACTION_URL)
    if new_count is None:
        return jsonify({"status": "error", "message": "Error fetching new review count."})

    if new_count > initial_count:
        insert_or_update_review_count(new_count)
        update_salesman_points(salesman_id)
        return jsonify({"status": "success", "message": f"New review submitted! The total number of reviews is now {new_count}."})
    else:
        return jsonify({"status": "error", "message": "No new reviews submitted."})

@app.route('/')
def index():
    review_count = extract_review_count(EXTRACTION_URL)
    if review_count:
        insert_or_update_review_count(review_count)
        return render_template('index.html', review_count=review_count)
    else:
        return "Review count not found."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
