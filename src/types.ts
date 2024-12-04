export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface Document {
  id: string;
  name: string;
  uploadedAt: number;
  size: number;
  content?: string;
  chunks?: string[];
}

export interface Conversation {
  id: string;
  documentId: string;
  messages: Message[];
}

export interface DocumentChunk {
  content: string;
  index: number;
}