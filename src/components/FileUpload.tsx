import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileUp, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
}

export function FileUpload({ onFileSelect, isProcessing }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
    disabled: isProcessing,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      {isProcessing ? (
        <Loader2 className="mx-auto h-12 w-12 text-blue-500 animate-spin mb-4" />
      ) : (
        <FileUp className="mx-auto h-12 w-12 text-gray-400 mb-4" />
      )}
      <p className="text-gray-600">
        {isProcessing
          ? "Processing document..."
          : isDragActive
          ? "Drop the PDF here"
          : "Drag and drop a PDF file here, or click to select"}
      </p>
      <p className="text-sm text-gray-500 mt-2">Only PDF files are supported</p>
    </div>
  );
}