from flask import Flask, render_template, request, jsonify, redirect, url_for
import http.client
import requests
import json

app = Flask(__name__)

API_HOST = "website-categorization-api-now-with-ai.p.rapidapi.com"
API_KEY = "74c124c35dmshc28e82aa0b482fep173048jsn1b3068002929"

def get_website_category(website_name):
    """Fetches website categories from RapidAPI."""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }

    conn.request("GET", f"/website-categorization/{website_name}", headers=headers)
    res = conn.getresponse()
    data = res.read()

    try:
        json_data = json.loads(data.decode("utf-8"))
        print("Category API Response:", json_data)  # Debugging

        categories = json_data.get("categories", [])

        formatted_categories = [
            {"name": cat.get("name", "Unknown"), "confidence": cat.get("confidence", 0)}
            for cat in categories
        ]

        return formatted_categories if formatted_categories else [{"name": "Unknown", "confidence": 0}]

    except json.JSONDecodeError:
        return [{"name": "Unknown", "confidence": 0}]

def get_website_description(website_name):
    """Fetches website description from DuckDuckGo API."""
    website_name = website_name.replace('http://', '').replace('https://', '').split('/')[0]
    url = f"https://api.duckduckgo.com/?q={website_name}&format=json&no_html=1&skip_disambig=1"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        description = data.get("AbstractText", "").strip()
        if not description:
            description = data.get("RelatedTopics", [{}])[0].get("Text", "").strip()
        if not description:
            description = data.get("Definition", "").strip()
        
        return description if description else "No description available for this website."
    
    except requests.RequestException as e:
        print(f"Error fetching description for {website_name}:", e)
        return "Could not fetch description at this time. Please try again later."

@app.route("/", methods=["GET"])
def home():
    """Landing page that redirects to the categorization page."""
    return render_template("index.html")

@app.route("/categorize", methods=["GET", "POST"])
def categorize():
    """Handles website categorization and displays results."""
    categories = []
    entered_url = None

    if request.method == "POST":
        entered_url = request.form["url"].strip()
        if entered_url:
            categories = get_website_category(entered_url)
        return render_template("categorize.html", categories=categories, entered_url=entered_url)

    return render_template("categorize.html", categories=[], entered_url=None)

@app.route("/get-description", methods=["POST"])
def fetch_description():
    """Handles AJAX request for fetching website descriptions."""
    try:
        data = request.get_json()
        print("Received data:", data)  # Debugging

        if not data or "url" not in data:
            return jsonify({"error": "URL parameter is required"}), 400

        website_name = data["url"].strip()
        website_name = website_name.replace('http://', '').replace('https://', '').split('/')[0].split('?')[0]

        description = get_website_description(website_name)

        return jsonify({
            "description": description,
            "url": website_name
        })

    except Exception as e:
        print(f"Error in fetch_description: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500


if __name__ == "__main__":
    app.run(debug=True)
