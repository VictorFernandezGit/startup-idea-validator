from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv



load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    idea = request.form.get("idea", "")

    prompt = f"""

    Act as a startup analyst. Analyze this startup idea:

"{idea}"

Give back:
1. One-sentence summary
2. Target audience
3. Value proposition
4. Pros
5. Cons
6. Competitor analysis
7. SWOT analysis
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )

        result = response.choices[0].message.content.strip()

        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)})
    
    

if __name__ == '__main__':
    app.run(debug=True)