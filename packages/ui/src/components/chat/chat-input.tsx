import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { Paperclip, Send } from 'lucide-react';
import { Button } from '../atoms/button/button';

interface ChatInputProps {
  onSend: (message: string) => void;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  fileRequest?: { document_type: string; reason: string } | null;
}

export function ChatInput({ onSend, onFileSelect, disabled, fileRequest }: ChatInputProps) {
  const [input, setInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
      e.target.value = '';
    }
  }

  return (
    <div className="border-t bg-background p-4">
      {fileRequest && (
        <div className="mb-3 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-800 dark:bg-blue-950">
          <p className="font-medium text-blue-900 dark:text-blue-100">
            Document requested: {fileRequest.document_type.replace(/_/g, ' ')}
          </p>
          {fileRequest.reason && (
            <p className="mt-1 text-blue-700 dark:text-blue-300">{fileRequest.reason}</p>
          )}
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={() => fileInputRef.current?.click()}
          >
            <Paperclip className="h-4 w-4" />
            Upload File
          </Button>
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
          onChange={handleFileChange}
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="shrink-0"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
        >
          <Paperclip className="h-5 w-5" />
        </Button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows={1}
          disabled={disabled}
          className="max-h-32 min-h-[40px] flex-1 resize-none rounded-xl border bg-muted/50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
        <Button
          type="submit"
          size="icon"
          className="shrink-0"
          disabled={disabled || !input.trim()}
        >
          <Send className="h-5 w-5" />
        </Button>
      </form>
    </div>
  );
}
