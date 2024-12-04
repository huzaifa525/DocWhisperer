import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const setApiKey = (apiKey: string) => {
  if (!apiKey) {
    delete api.defaults.headers.common['api-key'];
    return;
  }

  // Validate DeepSeek API key format
  if (!apiKey.startsWith('sk-')) {
    throw new Error('Invalid DeepSeek API key format. API keys should start with "sk-"');
  }

  api.defaults.headers.common['api-key'] = apiKey;
};

export const initializeAssistant = async (apiKey: string) => {
  try {
    const response = await api.post('/initialize', null, {
      params: { api_key: apiKey }
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Invalid DeepSeek API key. Please check your API key and try again.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to initialize AI assistant');
    }
    throw error;
  }
};

export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const queryDocument = async (question: string) => {
  const response = await api.post('/query', { question });
  return response.data;
};

export const getChatHistory = async () => {
  const response = await api.get('/chat-history');
  return response.data;
};

export const resetKnowledgeBase = async () => {
  const response = await api.post('/reset');
  return response.data;
};