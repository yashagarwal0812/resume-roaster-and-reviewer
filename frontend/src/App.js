import React, { useState, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [file, setFile] = useState(null);
  const [gdLink, setGdLink] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [results, setResults] = useState(null);
  const [dropActive, setDropActive] = useState(false);
  const fileInputRef = useRef(null);

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setUploadError("");
      } else {
        setUploadError("Please upload a PDF or DOCX file only.");
        setFile(null);
      }
    }
  };

  // Validate file type
  const validateFile = (file) => {
    const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    return validTypes.includes(file.type);
  };

  // Handle Google Drive link input
  const handleGdLinkChange = (e) => {
    setGdLink(e.target.value);
  };

  // Handle file upload via drag and drop
  const handleDrop = (e) => {
    e.preventDefault();
    setDropActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setUploadError("");
      } else {
        setUploadError("Please upload a PDF or DOCX file only.");
      }
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file && !gdLink) {
      setUploadError("Please upload a file or provide a Google Drive link.");
      return;
    }
    
    setIsUploading(true);
    setUploadError("");
    
    try {
      const formData = new FormData();
      
      if (file) {
        formData.append("file", file);
      } else if (gdLink) {
        formData.append("gdrive_link", gdLink);
      }
      
      const response = await axios.post(`${API}/upload-resume`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      setResults(response.data);
      setFile(null);
      setGdLink("");
      
    } catch (error) {
      console.error("Error uploading resume:", error);
      setUploadError(
        error.response?.data?.detail || 
        "Failed to upload and analyze your resume. Please try again."
      );
    } finally {
      setIsUploading(false);
    }
  };

  // Reset the application state
  const handleReset = () => {
    setResults(null);
    setFile(null);
    setGdLink("");
    setUploadError("");
  };

  // Trigger file input click
  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Resume Roaster</h1>
        <p className="tagline">Upload your resume and we'll roast it to perfection!</p>
      </header>
      
      <main className="main-content">
        {!results ? (
          <div className="upload-section">
            <div className="cartoons-container">
              <img src="https://cdn.pixabay.com/photo/2015/01/22/15/13/businessman-607834_1280.png" alt="Businessman cartoon" className="cartoon cartoon1" />
              <img src="https://cdn.pixabay.com/photo/2020/06/04/12/57/business-5258645_1280.png" alt="Business man with graph" className="cartoon cartoon2" />
              <img src="https://cdn.pixabay.com/photo/2022/06/29/10/38/job-7291427_1280.png" alt="Woman working on laptop" className="cartoon cartoon3" />
            </div>
            
            <form onSubmit={handleSubmit} className="upload-form">
              <div 
                className={`drop-area ${dropActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDropActive(true); }}
                onDragLeave={() => setDropActive(false)}
                onDrop={handleDrop}
                onClick={triggerFileInput}
              >
                <input 
                  type="file" 
                  onChange={handleFileChange} 
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept=".pdf,.docx"
                />
                
                {file ? (
                  <div className="file-info">
                    <svg xmlns="http://www.w3.org/2000/svg" className="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                      <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    <span className="file-name">{file.name}</span>
                  </div>
                ) : (
                  <div className="drop-content">
                    <svg xmlns="http://www.w3.org/2000/svg" className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="17 8 12 3 7 8"></polyline>
                      <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                    <p>Drop your resume here or click to browse</p>
                    <span className="file-types">Supports PDF and DOCX files</span>
                  </div>
                )}
              </div>
              
              <div className="divider">
                <span>OR</span>
              </div>
              
              <div className="gd-link-input">
                <label htmlFor="gd-link">Google Drive Link:</label>
                <input 
                  type="text" 
                  id="gd-link"
                  value={gdLink}
                  onChange={handleGdLinkChange}
                  placeholder="Paste your Google Drive document link here"
                />
              </div>
              
              {uploadError && <div className="error-message">{uploadError}</div>}
              
              <button 
                type="submit" 
                className="submit-btn"
                disabled={isUploading}
              >
                {isUploading ? "Analyzing Resume..." : "Roast My Resume!"}
              </button>
            </form>
          </div>
        ) : (
          <div className="results-section">
            <div className="result-card roast-card">
              <h2>The Roast 🔥</h2>
              <div className="result-content">
                {results.roast.split('\n').map((para, index) => (
                  para ? <p key={index}>{para}</p> : <br key={index} />
                ))}
              </div>
            </div>
            
            <div className="result-card review-card">
              <h2>The Review 📝</h2>
              <div className="result-content">
                {results.review.split('\n').map((para, index) => (
                  para ? <p key={index}>{para}</p> : <br key={index} />
                ))}
              </div>
            </div>
            
            <button onClick={handleReset} className="reset-btn">
              Roast Another Resume
            </button>
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>Resume Roaster &copy; 2025 - A humorous take on resume feedback</p>
      </footer>
    </div>
  );
}

export default App;
