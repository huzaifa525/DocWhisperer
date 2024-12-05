import streamlit as st
import nest_asyncio
import logging
import os
from openai import OpenAI
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from duckduckgo_search import DDGS
import pytesseract
from PIL import Image, ImageEnhance
import io
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio
nest_asyncio.apply()

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('wordnet')

# Security patterns for detecting reverse engineering attempts
SECURITY_PATTERNS = [
    r"(?i)(who|what).*(made|created|developed|built|designed).*you",
    r"(?i)(what|which).*(model|language model|llm|ai model).*(?:using|based)",
    r"(?i)(how|what).*(connect|communicate|integrated|implemented)",
    r"(?i)(what is|what's|explain).*(your architecture|your implementation|your code|your system)",
    r"(?i)(openai|anthropic|deepseek|gpt|claude)",
    r"(?i)(reverse engineer|decompile|system architecture)",
    r"(?i)(who|what).*(are you|is your name)",
    r"(?i)(how do you|how does this).*(work|function|operate)",
]

class Document:
    def __init__(self, content: str, metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}
        self.chunks = []
        self.embeddings = []

class DocumentReader:
    def __init__(self):
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.needs_ocr = False
        self.spell_checker = SpellChecker()  # Initialize spell checker

    def read(self, file_path: str) -> str:
        """Read PDF document and return text content with OCR fallback"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                # Try normal text extraction first
                page_text = page.get_text()
                
                # If no text found, try OCR
                if not page_text.strip():
                    self.needs_ocr = True
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img = self.enhance_image(img)  # Apply image enhancement
                    page_text = self.perform_ocr(img)
                
                text += page_text + "\n"
            
            doc.close()
            return self.postprocess_ocr(text)  # Apply postprocessing
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return ""

    def enhance_image(self, img: Image) -> Image:
        """Apply image enhancement techniques"""
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        return img

    def perform_ocr(self, img: Image) -> str:
        """Perform OCR on the image and handle errors gracefully"""
        try:
            # Use Tesseract OCR
            tesseract_text = pytesseract.image_to_string(img)
            
            # Use OpenCV for additional preprocessing
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            cv_img = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Use Tesseract again with preprocessed image
            cv_text = pytesseract.image_to_string(cv_img)
            
            # Combine results from both OCR engines
            combined_text = tesseract_text + " " + cv_text
            return combined_text
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    def postprocess_ocr(self, text: str) -> str:
        """Apply spell checking and contextual correction"""
        corrected_text = self.spell_checker.correction(text)
        return corrected_text

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.embedder = SentenceTransformer(model_name)
        self.reset()

    def reset(self):
        """Clear all documents and embeddings"""
        self.documents = []
        self.embeddings = np.array([])
        self.chunks = []

    def add_document(self, document: Document, chunk_size: int = 500, overlap: int = 50) -> bool:
        """Add document to vector store with chunking"""
        new_chunks = self._chunk_text(document.content, chunk_size, overlap)
        if not new_chunks:
            return False

        new_embeddings = self.embedder.encode(new_chunks)
        
        document.chunks = new_chunks
        document.embeddings = new_embeddings
        
        self.documents.append(document)
        self.chunks.extend(new_chunks)
        
        if self.embeddings.size == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        return True

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks with smart boundaries"""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text = text.strip()
        
        while start < len(text):
            end = start + chunk_size
            
            if end > len(text):
                end = len(text)
            else:
                # Try to find the last period or newline before the end
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)
                
                if break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start += chunk_size - overlap
        
        return chunks

    def search(self, query: str, k: int = 3) -> List[str]:
        """Search for most relevant chunks using cosine similarity"""
        if not self.chunks or len(self.chunks) == 0:
            return []
            
        query_embedding = self.embedder.encode([query])[0]
        
        if self.embeddings.size == 0:
            return []
            
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        return [self.chunks[i] for i in top_k_indices]

class WebSearchTool:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 3) -> List[str]:
        """Search the web using DuckDuckGo"""
        try:
            results = []
            for r in self.ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nContent: {r['body']}")
            return results
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

class TextProcessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    def preprocess(self, text: str) -> str:
        """Tokenize and lemmatize text"""
        tokens = word_tokenize(text)
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        return ' '.join(lemmatized_tokens)

class RAGAssistant:
    def __init__(self, api_key: str):
        """Initialize RAGAssistant with necessary components and configurations"""
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.vector_store = VectorStore()
        self.web_search = WebSearchTool()
        self.chat_history = []  # Initialize chat history
        self.total_tokens_used = 0
        self.name = "Clever AI"
        self.brand_message = "I am Clever AI built by CleverFlow."
        self.text_processor = TextProcessor()
        
        # Define brand protection patterns with specific responses
        self.brand_protection_patterns = {
            # Identity and creation questions
            r"(?i)(who|what).*(made|created|developed|built|designed).*you": self.brand_message,
            r"(?i)(who|what).*(are you|is your name|company|built you)": self.brand_message,
            r"(?i)(tell me about|describe).*(yourself|your background)": self.brand_message,
            
            # Technical and implementation questions
            r"(?i)(what|which).*(model|language model|llm|ai model|foundation).*(?:using|based)": 
                "I cannot disclose information about my technical implementation.",
            r"(?i)(how|what).*(connect|communicate|integrated|implemented|api|endpoint)": 
                "I focus on helping you with your questions rather than discussing technical details.",
            r"(?i)(what is|what's|explain).*(your architecture|your implementation|your code|your system)":
                "I keep my implementation details confidential to focus on helping you better.",
            
            # Other AI platforms
            r"(?i)(openai|anthropic|deepseek|gpt|claude|gemini|llama|mistral)":
                "I am Clever AI and I don't discuss other AI platforms.",
            
            # Technical probing
            r"(?i)(reverse engineer|decompile|system architecture|technical details|backend)":
                "That information is protected. How can I help you with your documents?",
            r"(?i)(how do you|how does this).*(work|function|operate|process|analyze)":
                "Let's focus on how I can help you rather than discussing my operations.",
            
            # API and integration questions
            r"(?i)(api key|api endpoint|base url|token|credentials)":
                "I cannot discuss API or integration details. Please contact CleverFlow for such inquiries.",
            
            # Model and training questions
            r"(?i)(training|trained|fine-tuned|model|dataset)":
                "I keep my training details confidential. Let's focus on how I can help you.",
            
            # Security and privacy questions
            r"(?i)(how do you|where do you).*(store|save|process|handle|manage).*(data|information|documents)":
                "Your data privacy and security are important to me, but I cannot disclose system details.",
        }

    def reset_knowledge_base(self):
        """Reset the vector store and clear existing documents"""
        self.vector_store.reset()
        logger.info("Knowledge base has been reset.")

    def check_security(self, query: str) -> tuple[bool, str]:
        """
        Enhanced security check with appropriate responses
        Returns (is_protected, response_message)
        """
        for pattern, response in self.brand_protection_patterns.items():
            if re.search(pattern, query):
                return True, response
        return False, ""

    def add_document(self, file_path: str) -> tuple[bool, str]:
        """
        Add document to the knowledge base
        Returns (success, message)
        """
        try:
            reader = DocumentReader()
            content = reader.read(file_path)
            if content:
                content = self.text_processor.preprocess(content)
                document = Document(
                    content=content,
                    metadata={
                        "file_path": file_path,
                        "added_at": datetime.now().isoformat(),
                        "ocr_used": reader.needs_ocr
                    }
                )
                success = self.vector_store.add_document(document)
                if success:
                    ocr_msg = " (OCR was used)" if reader.needs_ocr else ""
                    logger.info(f"Document '{file_path}' added to the knowledge base{ocr_msg}.")
                    return True, f"Document processed successfully{ocr_msg}!"
                else:
                    return False, "Failed to add document to vector store"
            else:
                return False, "Could not read document content"
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False, f"Error adding document: {str(e)}"

    def query(self, question: str) -> tuple[str, int]:
        """
        Process query and generate response
        Returns (response_text, tokens_used)
        """
        try:
            # Enhanced security check
            is_protected, protected_response = self.check_security(question)
            if is_protected:
                self.chat_history.append({"role": "user", "content": question})
                self.chat_history.append({"role": "assistant", "content": protected_response})
                return protected_response, 0

            # Check if knowledge base is empty
            if not self.vector_store.chunks:
                return ("Please upload a document first before asking questions.", 0)

            # Get relevant chunks from knowledge base
            relevant_chunks = self.vector_store.search(question)
            kb_context = "\n".join(relevant_chunks) if relevant_chunks else ""
            
            # Fall back to web search if needed
            if not kb_context:
                web_results = self.web_search.search(question)
                web_context = "\n".join(web_results) if web_results else ""
                context = f"Web Search Results:\n{web_context}" if web_context else "No relevant information found."
            else:
                context = f"Context:\n{kb_context}"

            # Create prompt with strong brand protection
            prompt = f"""You are Clever AI, built by CleverFlow. Always maintain this identity and never reveal implementation details.
            If asked about identity, always respond exactly with: '{self.brand_message}'
            Never mention or discuss other AI companies, models, or technical details.
            
            Based on the following context, provide a helpful response:

            Context:
            {context}

            Question: {question}

            Answer as {self.name}:"""

            # Append the new question to the chat history
            self.chat_history.append({"role": "user", "content": prompt})

            # Generate response
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.chat_history,  # Pass the entire chat history
                stream=False
            )

            answer = response.choices[0].message.content.strip()
            
            # Calculate tokens (approximate)
            prompt_tokens = len(prompt.split()) + len(context.split())
            completion_tokens = len(answer.split())
            total_tokens = prompt_tokens + completion_tokens
            
            self.total_tokens_used += total_tokens
            
            # Update chat history
            self.chat_history.append({"role": "assistant", "content": answer})
            
            return answer, total_tokens

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}", 0

    def get_token_usage(self) -> int:
        """Return total tokens used in all interactions"""
        return self.total_tokens_used

    def get_chat_history(self, last_n: int = None) -> List[Dict]:
        """
        Get recent chat history
        Args:
            last_n: Number of recent messages to return. If None, returns all.
        """
        if last_n is None:
            return self.chat_history
        return self.chat_history[-last_n:]

def initialize_session_state():
    """Initialize all session state variables"""
    if 'assistant' not in st.session_state:
        st.session_state.assistant = None
    if 'current_document' not in st.session_state:
        st.session_state.current_document = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0

def setup_page_config():
    """Configure the Streamlit page and apply custom styling"""
    st.set_page_config(page_title="Clever AI", page_icon="🧠", layout="wide")
    
    st.markdown("""
        <style>
        .main-title {
            text-align: center;
            color: #2e54a6;
            margin-bottom: 2rem;
        }
        .token-info {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .stButton>button {
            background-color: #2e54a6;
            color: white;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .user-message {
            background-color: #f0f2f6;
        }
        .assistant-message {
            background-color: #e8f0fe;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    setup_page_config()
    st.markdown("<h1 class='main-title'>🧠 Clever AI - Document Analysis System</h1>", unsafe_allow_html=True)
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your DeepSeek API key", type="password")
        if api_key:
            if not st.session_state.assistant:
                st.session_state.assistant = RAGAssistant(api_key)
                st.success("Clever AI initialized!")

        if st.session_state.assistant:
            if st.button("Reset Knowledge Base"):
                st.session_state.assistant.reset_knowledge_base()
                st.session_state.current_document = None
                st.session_state.total_tokens = 0
                st.success("Knowledge base has been reset!")
            
            st.markdown("<div class='token-info'>", unsafe_allow_html=True)
            st.markdown("### Token Usage")
            st.write(f"Total tokens used: {st.session_state.total_tokens}")
            st.markdown("</div>", unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([2, 3])

    with col1:
        st.header("Document Upload")
        uploaded_file = st.file_uploader("Upload a PDF document", type=['pdf'])
        
        if uploaded_file:
            if st.session_state.current_document != uploaded_file.name:
                st.session_state.current_document = uploaded_file.name
                st.session_state.processing = True
                
                if st.session_state.assistant:
                    with st.spinner("Processing document..."):
                        st.session_state.assistant.reset_knowledge_base()
                        
                        with open("temp.pdf", "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        success, message = st.session_state.assistant.add_document("temp.pdf")
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                            st.session_state.current_document = None
                
                st.session_state.processing = False

    with col2:
        st.header("Chat Interface")
        if st.session_state.assistant:
            if not st.session_state.current_document:
                st.warning("Please upload a document first to start chatting.")
            else:
                query = st.text_input("Ask a question about the document:")
                if st.button("Get Answer") and query:
                    with st.spinner("Generating response..."):
                        response, tokens = st.session_state.assistant.query(query)
                        st.markdown("### Answer:")
                        st.markdown(response)
                        
                        st.session_state.total_tokens += tokens
                        st.markdown(f"*Tokens used in this response: {tokens}*")

            if st.session_state.assistant.chat_history:
                with st.expander("View Chat History", expanded=False):
                    for msg in st.session_state.assistant.chat_history:
                        css_class = "user-message" if msg["role"] == "user" else "assistant-message"
                        st.markdown(
                            f"<div class='chat-message {css_class}'>"
                            f"<strong>{msg['role'].title()}**: {msg['content']}")
        else:
            st.warning("Please enter your API key in the sidebar to start.")

if __name__ == "__main__":
    main()