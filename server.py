from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import logging
from typing import List, Dict, Tuple
import json

# Import our existing classes
from app import Document, DocumentReader, VectorStore, WebSearchTool, TextProcessor, RAGAssistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
vector_store = VectorStore()
document_reader = DocumentReader()
web_search = WebSearchTool()
text_processor = TextProcessor()

# Initialize RAG Assistant with environment variable
rag_assistant = RAGAssistant(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        success, message = rag_assistant.add_document(filepath)
        if success:
            return jsonify({'message': 'File uploaded and processed successfully'}), 200
        else:
            return jsonify({'error': message}), 400

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    question = data['question']
    
    # Security check
    is_protected, response = rag_assistant.check_security(question)
    if is_protected:
        return jsonify({'response': response}), 200
    
    # Process the query
    response, tokens_used = rag_assistant.query(question)
    
    return jsonify({
        'response': response,
        'tokens_used': tokens_used,
        'chat_history': rag_assistant.get_chat_history()
    }), 200

@app.route('/api/reset', methods=['POST'])
def reset_knowledge():
    rag_assistant.reset_knowledge_base()
    return jsonify({'message': 'Knowledge base reset successfully'}), 200

@app.route('/api/token-usage', methods=['GET'])
def get_token_usage():
    usage = rag_assistant.get_token_usage()
    return jsonify({'total_tokens_used': usage}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
