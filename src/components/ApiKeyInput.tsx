import { useState, useEffect } from 'react';
import { Key, Eye, EyeOff, Save, Check, Info, ExternalLink, AlertCircle } from 'lucide-react';

interface ApiKeyInputProps {
  onApiKeyChange: (apiKey: string) => void;
}

export function ApiKeyInput({ onApiKeyChange }: ApiKeyInputProps) {
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem('deepseekApiKey') || '';
  });
  const [showKey, setShowKey] = useState(false);
  const [isSaved, setIsSaved] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem('deepseekApiKey', apiKey);
      onApiKeyChange(apiKey);
    } else {
      localStorage.removeItem('deepseekApiKey');
      onApiKeyChange('');
    }
  }, [apiKey, onApiKeyChange]);

  const validateApiKey = (key: string): boolean => {
    if (!key) return true; // Empty is valid (though not useful)
    return key.startsWith('sk-') && key.length > 3;
  };

  const handleSave = () => {
    if (!apiKey) {
      setError(null);
      setIsSaved(true);
      setIsEditing(false);
      return;
    }

    if (!validateApiKey(apiKey)) {
      setError('Invalid API key format. DeepSeek API keys must start with "sk-"');
      return;
    }

    setError(null);
    setIsSaved(true);
    setIsEditing(false);
  };

  const handleKeyChange = (value: string) => {
    setApiKey(value);
    setIsSaved(false);
    setError(null);
  };

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-center gap-2 mb-2">
        <Key className="w-4 h-4 text-gray-500" />
        <h3 className="text-sm font-medium text-gray-900">DeepSeek API Key</h3>
        <button
          className="text-gray-400 hover:text-gray-600"
          onClick={() => setShowInfo(!showInfo)}
          onMouseEnter={() => setShowInfo(true)}
          onMouseLeave={() => setShowInfo(false)}
        >
          <Info className="w-4 h-4" />
        </button>
      </div>

      {showInfo && (
        <div className="mb-3 p-3 bg-blue-50 text-sm text-blue-800 rounded">
          <p className="mb-2">
            To use DocWhisperer, you need a DeepSeek API key. Your key helps power our AI features and document analysis capabilities.
          </p>
          <a
            href="https://platform.deepseek.com/api"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
          >
            Get your DeepSeek API key
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}

      {error && (
        <div className="mb-3 p-3 bg-red-50 text-sm text-red-800 rounded flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
      
      {isEditing ? (
        <div className="space-y-2">
          <div className="relative">
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => handleKeyChange(e.target.value)}
              placeholder="sk-..."
              className={`w-full pr-10 pl-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500
                ${error ? 'border-red-300' : 'border-gray-300'}`}
            />
            <button
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showKey ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={isSaved}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              Save
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {apiKey ? (
                <span className="text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500 inline mr-1" />
                  DeepSeek API key is set
                </span>
              ) : (
                <span className="text-sm text-gray-600">No DeepSeek API key set</span>
              )}
            </div>
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-blue-500 hover:text-blue-600"
            >
              {apiKey ? 'Change' : 'Add'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}