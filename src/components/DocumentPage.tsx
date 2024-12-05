import { useState, useEffect } from 'react';
import { Navbar } from './Navbar';
import { FileUpload } from './FileUpload';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { DocumentList } from './DocumentList';
import { ApiKeyInput } from './ApiKeyInput';
import { type Document, type Message, type Conversation } from '../types';
import { motion } from 'framer-motion';

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
  const [apiKey, setApiKey] = useState<string>('');

  useEffect(() => {
    localStorage.setItem('documents', JSON.stringify(documents));
    localStorage.setItem('conversations', JSON.stringify(conversations));
  }, [documents, conversations]);

  const handleFileSelect = async (file: File) => {
    if (!apiKey) {
      alert('Please set your API key first');
      return;
    }

    setIsProcessing(true);
    try {
      const arrayBuffer = await file.arrayBuffer();
      const textContent = await processDocument(arrayBuffer);
      
      const newDocument: Document = {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        uploadedAt: Date.now(),
        content: textContent,
      };

      setDocuments(prev => [...prev, newDocument]);
      setActiveDocumentId(newDocument.id);
      
      const newConversation: Conversation = {
        id: crypto.randomUUID(),
        documentId: newDocument.id,
        messages: [{
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `I've processed "${file.name}". What would you like to know about it?`,
          timestamp: Date.now(),
        }],
      };
      
      setConversations(prev => [...prev, newConversation]);
    } catch (error) {
      console.error('Error processing document:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const processDocument = async (arrayBuffer: ArrayBuffer): Promise<string> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve("This is a placeholder for the document's content.");
      }, 1000);
    });
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
    try {
      const aiResponse = await simulateAIResponse(content);
      
      const responseMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: aiResponse,
        timestamp: Date.now(),
      };

      setConversations(prev => prev.map(conv => 
        conv.documentId === activeDocumentId
          ? { ...conv, messages: [...conv.messages, responseMessage] }
          : conv
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  const simulateAIResponse = async (query: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return `This is a simulated response to your query: "${query}"`;
  };

  const activeConversation = conversations.find(
    conv => conv.documentId === activeDocumentId
  );

  const handleDeleteDocument = (id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
    setConversations(prev => prev.filter(conv => conv.documentId !== id));
    if (activeDocumentId === id) {
      setActiveDocumentId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <ApiKeyInput onApiKeyChange={setApiKey} />
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
                Please add your API key to start using the application
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