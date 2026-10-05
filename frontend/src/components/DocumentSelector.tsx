import React, { useRef } from 'react';
import type { DocumentMetadata } from '../types';

interface Props {
  documents: DocumentMetadata[];
  selectedDocId: string;
  onSelectDoc: (docId: string) => void;
  onUploadSuccess: (newDoc: DocumentMetadata) => void;
  isUploading: boolean;
  setIsUploading: (val: boolean) => void;
}

export const DocumentSelector: React.FC<Props> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onUploadSuccess,
  isUploading,
  setIsUploading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data: DocumentMetadata = await res.json();
      onUploadSuccess(data);
      onSelectDoc(data.doc_id);
    } catch (err: any) {
      alert(`Upload error: ${err.message || 'Could not upload PDF'}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const selectedDoc = documents.find((d) => d.doc_id === selectedDocId);

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--primary)' }}>📄</span> Active Document
        </h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          style={{
            background: 'var(--primary-bg)',
            color: 'var(--primary)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: isUploading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s',
          }}
        >
          {isUploading ? 'Uploading...' : '+ Upload New PDF'}
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf"
          style={{ display: 'none' }}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <select
          value={selectedDocId}
          onChange={(e) => onSelectDoc(e.target.value)}
          style={{
            width: '100%',
            background: 'var(--bg-secondary)',
            color: 'var(--text-main)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            fontSize: '14px',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          {documents.map((doc) => (
            <option key={doc.doc_id} value={doc.doc_id}>
              {doc.title || doc.filename} ({doc.page_count} pages)
            </option>
          ))}
        </select>

        {selectedDoc && (
          <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: 'var(--text-dim)' }}>
            <span>ID: <code style={{ color: 'var(--text-muted)' }}>{selectedDoc.doc_id}</code></span>
            <span>Pages: <b style={{ color: 'var(--text-muted)' }}>{selectedDoc.page_count}</b></span>
            {selectedDoc.size_bytes && (
              <span>Size: {(selectedDoc.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
