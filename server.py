from flask import Flask, request, jsonify, render_template
import os
import json
import hashlib
import logging
import httpx

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# API Keys (Ensure these are properly set)
SERP_API_KEY = os.environ.get("SERP_API_KEY") or "Your_API_Key"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "Your_API_Key"


# Function to call SERP API
def search_serp_api(query):
    simplified_query = f"optimize {query}"

    params = {
        "q": simplified_query,
        "engine": "google",
        "api_key": SERP_API_KEY,
        "num": 5,
        "output": "json",
    }

    logging.info(f"Requesting SERP API for query: {simplified_query}")

    try:
        response = httpx.get("https://serpapi.com/search", params=params)
        if response.status_code == 200:
            return extract_results(response.json())
        else:
            logging.error(f"SERP API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error during SERP API call: {e}")
        return []

# Function to extract relevant results from SERP API response
def extract_results(json_response):
    results = []
    if "organic_results" in json_response:
        for result in json_response["organic_results"]:
            results.append({
                "title": result.get("title", "No Title"),
                "content": result.get("snippet", "No Snippet"),
                "url": result.get("link", "No URL"),
                "grade": 0,  # Initial grade value set to 0
                "date": result.get("date", None),
            })
    return results

# Function to call Groq API for chat completions
def get_chat_completion(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}]
        }

        logging.info("Sending chat completion request to Groq API.")
        response = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logging.error(f"Groq API chat completion error: {response.status_code} - {response.text}")
            return "Error generating chat completion."
    except Exception as e:
        logging.error(f"Error during Groq API chat completion: {e}")
        return "Error generating chat completion."

# Function to evaluate and grade websites based on relevance, quality, and freshness
def grade_websites(websites):
    graded_websites = []
    
    # Example to guide the grading
    grading_example = """
    Example 1:
    Title: "Python DFS Implementation"
    Content: "This website provides an in-depth explanation of the depth-first search algorithm in Python with code examples and clear explanations."
    Grade: 8/10
    Reason: The content is highly relevant, well-organized, and clear. It provides code examples, which adds practical value.

    Example 2:
    Title: "DFS Algorithm Overview"
    Content: "This site provides a basic introduction to the depth-first search algorithm, with minimal details and no code examples."
    Grade: 5/10
    Reason: The content is relevant but lacks in-depth explanations and practical examples. Freshness is not considered here, as the page does not mention recent developments.
    """

    for website in websites:
        content = website.get("content", "")
        title = website.get("title", "")
        
        # Step 1: Analyze relevance, quality, and freshness using Groq
        prompt = f"""
        Assess the relevance, quality, and freshness of the following website based on the given examples. Grade it out of 10 based on these criteria and return only the grade as the response that too a numerical value out of 10:

        Title: {title}
        Content: {content}

        {grading_example}
        """
        
        grading_feedback = get_chat_completion(prompt)
        
        # Step 2: Extract the grade from Groq's response
        try:
            # If the response contains a numeric grade, use it. Otherwise, simulate grading.
            grade = int(grading_feedback.strip()) if grading_feedback.isdigit() else 7  # Default to a reasonable grade
        except Exception as e:
            logging.error(f"Error extracting grade from Groq response: {e}")
            grade = 5  # Default grade in case of failure
        
        website["grade"] = grade
        graded_websites.append(website)

    # Step 3: Sort the websites by grade in descending order and keep top 3
    graded_websites.sort(key=lambda x: x["grade"], reverse=True)
    return graded_websites[:3]  # Return only the top 3 websites


# Route for homepage
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# Route to handle search queries
@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        query = data.get("query")
        if not query:
            raise ValueError("Query is required.")

        # Step 1: Analyze the user's input with Groq API
        analysis = get_chat_completion(f"Analyze and break down the following code snippet: {query}")

        # Step 2: Send the analysis to the SERP API for search results
        search_results = search_serp_api(analysis)
        if not search_results:
            raise ValueError("Error fetching search results.")

        # Step 3: Grade the websites based on relevance, quality, and freshness
        graded_results = grade_websites(search_results)

        # Step 4: Pass the search results to Groq API for generating optimized code and grading
        summary = get_chat_completion(f"Based on the following results, generate optimized code: {graded_results}")

        # Step 5: Return results to user
        return jsonify({
            "summary": summary,
            "links": graded_results
        })

    except Exception as e:
        logging.error(f"Unhandled error in /search: {e}")
        return jsonify({"error": str(e)}), 500

# Route to handle code analysis and optimization
@app.route("/optimize", methods=["POST"])
def optimize():
    try:
        data = request.json
        code_snippet = data.get("code_snippet")
        if not code_snippet:
            raise ValueError("Code snippet is required.")

        # Step 1: Analyze the code with Groq
        analysis = get_chat_completion(f"Analyze the following code snippet. Understand the programming language used in this code snippet and it's verison: {code_snippet}")

        # Step 2: Get suggestions for optimization from Groq
        optimized_code = get_chat_completion(f"Optimize the following code snippet in the programming language as it is given but optimized code should be of the latest available verison. Don't change the programming language of the code unless it is instructed to do so.: {analysis}")

        return jsonify({
            "original_code": code_snippet,
            "optimized_code": optimized_code
        })
    except Exception as e:
        logging.error(f"Unhandled error in /optimize: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
