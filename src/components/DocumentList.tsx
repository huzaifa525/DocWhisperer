import { type Document } from '../types';
import { FileText, Trash2 } from 'lucide-react';

interface DocumentListProps {
  documents: Document[];
  activeDocumentId?: string;
  onSelectDocument: (id: string) => void;
  onDeleteDocument: (id: string) => void;
}

export function DocumentList({ 
  documents, 
  activeDocumentId, 
  onSelectDocument, 
  onDeleteDocument 
}: DocumentListProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      {documents.length === 0 ? (
        <div className="p-4 text-center text-gray-500">
          No documents uploaded yet
        </div>
      ) : (
        <div className="divide-y">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50
                ${doc.id === activeDocumentId ? 'bg-blue-50' : ''}`}
              onClick={() => onSelectDocument(doc.id)}
            >
              <FileText className="w-5 h-5 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {doc.name}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(doc.uploadedAt).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteDocument(doc.id);
                }}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}