import React, { useState } from 'react';

const ProductImageUploader = ({
  productId,
  apiBaseUrl = 'https://internaloox-1.onrender.com/api',
  token = (typeof window !== 'undefined' ? localStorage.getItem('access_token') : ''),
  onUploaded,
  className = ''
}) => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e) => {
    const selected = e.target.files && e.target.files[0];
    setError('');
    setSuccess('');
    if (!selected) {
      setFile(null);
      setPreviewUrl('');
      return;
    }
    if (selected.size > 5 * 1024 * 1024) {
      setError('File exceeds 5 MB limit');
      return;
    }
    setFile(selected);
    const url = URL.createObjectURL(selected);
    setPreviewUrl(url);
  };

  const handleUpload = async () => {
    if (!file || !productId) return;
    setIsUploading(true);
    setError('');
    setSuccess('');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${apiBaseUrl}/orders/products/${productId}/upload_main_image/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token || ''}`
        },
        body: form
      });
      if (!res.ok) {
        const msg = await safeError(res);
        throw new Error(msg || `Upload failed (${res.status})`);
      }
      setSuccess('Image uploaded');
      if (typeof onUploaded === 'function') {
        const data = await res.json();
        onUploaded(data);
      }
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const safeError = async (res) => {
    try {
      const t = await res.text();
      try {
        const j = JSON.parse(t);
        return j.error || j.detail || t;
      } catch {
        return t;
      }
    } catch {
      return '';
    }
  };

  return (
    <div className={`border rounded-md p-3 bg-white ${className}`}>
      <div className="flex items-start gap-3">
        <div className="w-28 h-28 flex-shrink-0 border rounded-md bg-gray-50 overflow-hidden flex items-center justify-center">
          {previewUrl ? (
            <img src={previewUrl} alt="preview" className="w-full h-full object-cover" />
          ) : (
            <span className="text-xs text-gray-400">No image</span>
          )}
        </div>
        <div className="flex-1">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={handleUpload}
              disabled={!file || isUploading || !productId}
              className={`px-4 py-2 rounded-md text-white text-sm ${(!file || isUploading || !productId) ? 'bg-gray-300' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
              {isUploading ? 'Uploading…' : 'Upload Image'}
            </button>
            {success && <span className="text-green-600 text-sm">{success}</span>}
            {error && <span className="text-red-600 text-sm">{error}</span>}
          </div>
          {productId && (
            <div className="mt-2 text-xs text-gray-500">
              Max 5 MB. Product: {productId}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductImageUploader;

