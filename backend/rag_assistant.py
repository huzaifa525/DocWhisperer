from typing import List, Dict, Tuple
import logging
from datetime import datetime
import re
from openai import OpenAI
from utils.vector_store import VectorStore
from utils.web_search import WebSearchTool
from utils.text_processor import TextProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Document:
    def __init__(self, content: str, metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}
        self.chunks = []
        self.embeddings = []

class RAGAssistant:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.vector_store = VectorStore()
        self.web_search = WebSearchTool()
        self.chat_history = []
        self.total_tokens_used = 0
        self.name = "Clever AI"
        self.brand_message = "I am Clever AI built by CleverFlow."
        self.text_processor = TextProcessor()
        
        # Brand protection patterns (same as your original implementation)
        self.brand_protection_patterns = {
            r"(?i)(who|what).*(made|created|developed|built|designed).*you": self.brand_message,
            # ... (rest of your patterns)
        }

    def reset_knowledge_base(self):
        self.vector_store.reset()
        logger.info("Knowledge base has been reset.")

    def check_security(self, query: str) -> tuple[bool, str]:
        for pattern, response in self.brand_protection_patterns.items():
            if re.search(pattern, query):
                return True, response
        return False, ""

    def add_document(self, file_path: str) -> tuple[bool, str]:
        try:
            from utils.document_reader import DocumentReader
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
        try:
            # Security check
            is_protected, protected_response = self.check_security(question)
            if is_protected:
                self.chat_history.append({"role": "user", "content": question})
                self.chat_history.append({"role": "assistant", "content": protected_response})
                return protected_response, 0

            if not self.vector_store.chunks:
                return ("Please upload a document first before asking questions.", 0)

            relevant_chunks = self.vector_store.search(question)
            kb_context = "\n".join(relevant_chunks) if relevant_chunks else ""
            
            if not kb_context:
                web_results = self.web_search.search(question)
                web_context = "\n".join(web_results) if web_results else ""
                context = f"Web Search Results:\n{web_context}" if web_context else "No relevant information found."
            else:
                context = f"Context:\n{kb_context}"

            prompt = f"""You are {self.name}, built by CleverFlow. Always maintain this identity.
            Based on the following context, provide a helpful response:

            {context}

            Question: {question}

            Answer as {self.name}:"""

            self.chat_history.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.chat_history,
                stream=False
            )

            answer = response.choices[0].message.content.strip()
            
            prompt_tokens = len(prompt.split()) + len(context.split())
            completion_tokens = len(answer.split())
            total_tokens = prompt_tokens + completion_tokens
            
            self.total_tokens_used += total_tokens
            self.chat_history.append({"role": "assistant", "content": answer})
            
            return answer, total_tokens

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}", 0

    def get_token_usage(self) -> int:
        return self.total_tokens_used

    def get_chat_history(self, last_n: int = None) -> List[Dict]:
        if last_n is None:
            return self.chat_history
        return self.chat_history[-last_n:]