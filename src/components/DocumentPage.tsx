import { useState, useEffect } from 'react';
import { Navbar } from './Navbar';
import { FileUpload } from './FileUpload';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { DocumentList } from './DocumentList';
import { ApiKeyInput } from './ApiKeyInput';
import { type Document, type Message, type Conversation } from '../types';
import { motion } from 'framer-motion';
import { 
  initializeAssistant,
  uploadDocument,
  queryDocument,
  getChatHistory,
  resetKnowledgeBase,
  setApiKey
} from '../services/api';
import { AlertCircle } from 'lucide-react';

export function DocumentPage() {
  const [documents, setDocuments] = useState<Document[]>(() => {
    const saved = localStorage.getItem('documents');
    return saved ? JSON.parse(saved) : [];
  });

  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const saved = localStorage.getItem('conversations');
    return saved ? JSON.parse(saved) : [];
  });

  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKeyState] = useState<string>('');

  useEffect(() => {
    localStorage.setItem('documents', JSON.stringify(documents));
    localStorage.setItem('conversations', JSON.stringify(conversations));
  }, [documents, conversations]);

  const handleApiKeyChange = async (key: string) => {
    setApiKeyState(key);
    setApiKey(key);
    try {
      await initializeAssistant(key);
    } catch (error) {
      setError('Failed to initialize AI assistant. Please check your API key.');
    }
  };

  const handleFileSelect = async (file: File) => {
    if (!apiKey) {
      setError('Please set your API key first');
      return;
    }

    setIsProcessing(true);
    setError(null);
    try {
      const response = await uploadDocument(file);
      
      const newDocument: Document = {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        uploadedAt: Date.now(),
      };

      setDocuments(prev => [...prev, newDocument]);
      setActiveDocumentId(newDocument.id);
      
      const newConversation: Conversation = {
        id: crypto.randomUUID(),
        documentId: newDocument.id,
        messages: [{
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.message || `I've processed "${file.name}". What would you like to know about it?`,
          timestamp: Date.now(),
        }],
      };
      
      setConversations(prev => [...prev, newConversation]);
    } catch (error) {
      setError('Failed to upload document. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!activeDocumentId || !apiKey) return;

    const newMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setConversations(prev => prev.map(conv => 
      conv.documentId === activeDocumentId
        ? { ...conv, messages: [...conv.messages, newMessage] }
        : conv
    ));

    setIsProcessing(true);
    setError(null);
    try {
      const response = await queryDocument(content);
      
      const responseMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        timestamp: Date.now(),
      };

      setConversations(prev => prev.map(conv => 
        conv.documentId === activeDocumentId
          ? { ...conv, messages: [...conv.messages, responseMessage] }
          : conv
      ));
    } catch (error) {
      setError('Failed to get response from AI. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    try {
      await resetKnowledgeBase();
      setDocuments(prev => prev.filter(doc => doc.id !== id));
      setConversations(prev => prev.filter(conv => conv.documentId !== id));
      if (activeDocumentId === id) {
        setActiveDocumentId(null);
      }
    } catch (error) {
      setError('Failed to delete document. Please try again.');
    }
  };

  const activeConversation = conversations.find(
    conv => conv.documentId === activeDocumentId
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <ApiKeyInput onApiKeyChange={handleApiKeyChange} />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <FileUpload 
                onFileSelect={handleFileSelect}
                isProcessing={isProcessing}
              />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <DocumentList
                documents={documents}
                activeDocumentId={activeDocumentId || undefined}
                onSelectDocument={setActiveDocumentId}
                onDeleteDocument={handleDeleteDocument}
              />
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="lg:col-span-3 bg-white rounded-xl shadow-sm border min-h-[600px] flex flex-col"
          >
            {!apiKey ? (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Please add your API key to start using DocWhisperer
              </div>
            ) : activeDocumentId && activeConversation ? (
              <>
                <div className="flex-1 overflow-y-auto">
                  {activeConversation.messages.map(message => (
                    <ChatMessage 
                      key={message.id}
                      message={message}
                      isProcessing={isProcessing && message === activeConversation.messages[activeConversation.messages.length - 1]}
                    />
                  ))}
                </div>
                <ChatInput 
                  onSendMessage={handleSendMessage}
                  disabled={!activeDocumentId}
                  isProcessing={isProcessing}
                />
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Select or upload a document to start a conversation
              </div>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}