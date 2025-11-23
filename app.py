from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import TourismAgent

app = Flask(__name__)
CORS(app)

# Initialize the Tourism Agent
agent = TourismAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({'response': 'Please enter a message.'}), 400
        
        # Check for quit command
        if user_input.lower() in ['quit', 'exit', 'bye']:
            return jsonify({'response': 'Safe travels! Goodbye!', 'quit': True})
        
        # Process the request
        response = agent.process_request(user_input)
        
        return jsonify({'response': response, 'quit': False})
    
    except Exception as e:
        return jsonify({'response': f'An error occurred: {str(e)}', 'quit': False}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )



