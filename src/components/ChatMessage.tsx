import { type Message } from '../types';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
  isProcessing?: boolean;
}

export function ChatMessage({ message, isProcessing }: ChatMessageProps) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex gap-4 p-4 ${isAssistant ? 'bg-gray-50' : ''} ${isProcessing ? 'opacity-50' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center
        ${isAssistant ? 'bg-green-100' : 'bg-blue-100'}`}>
        {isAssistant ? (
          <Bot className="w-5 h-5 text-green-600" />
        ) : (
          <User className="w-5 h-5 text-blue-600" />
        )}
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-600">{isAssistant ? 'AI Assistant' : 'You'}</p>
        <p className="mt-1 text-gray-900 whitespace-pre-wrap">{message.content}</p>
        {message.timestamp && (
          <p className="text-xs text-gray-500 mt-2">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
}