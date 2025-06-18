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
    return render_template('homepage.html')

@app.route('/validator')
def validator():
    return render_template('validator.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    idea = data.get("idea", "")
    mode = data.get("mode", "general")

    base_prompt = {
        "general": f"""Act as a startup analyst. Analyze this startup idea:\n\n"{idea}"\n\nGive back a structured analysis including summary, audience, value prop, pros/cons, competitor review, and SWOT.""",
        "sharktank": f"""Act like a Shark Tank investor. Review this pitch idea:\n\n"{idea}"\n\nTell me how viable it is, how much you'd invest, what's wrong with it, and how it can scale fast. Include risks and profitability potential.""",
        "lean": f"""Act as a Lean Startup coach. Analyze this idea:\n\n"{idea}"\n\nGive MVP advice, customer validation strategy, and what to test first. Include assumptions and risks.""",
        "vc": f"""Act like a venture capitalist. Analyze this idea:\n\n"{idea}"\n\nEvaluate TAM/SAM/SOM, GTM strategy, defensibility, CAC/LTV potential, and team strength.""",
        "tech": f"""Act like a technical co-founder. Analyze this idea:\n\n"{idea}"\n\nEstimate build time, tech stack, risks, and whether it's technically feasible in 3 months. Suggest architecture too."""
    }

    
    prompt = base_prompt.get(mode, base_prompt["general"])

    
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