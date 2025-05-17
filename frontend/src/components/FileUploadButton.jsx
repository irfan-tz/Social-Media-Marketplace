// frontend/src/components/FileUploadButton.jsx
import { useState } from 'react';
import axios from 'axios';

const FileUploadButton = ({ onSuccess, onError }) => {
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/attachments/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      onSuccess(response.data);
    } catch (error) {
      onError(error.response?.data?.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <label className="upload-button">
        <input
          type="file"
          onChange={handleFileUpload}
          disabled={isUploading}
          style={{ display: 'none' }}
          accept="image/*,video/*"
        />
        {isUploading ? 'Uploading...' : '📎 Attach File'}
      </label>
    </div>
  );
};

export default FileUploadButton;