const fs = require('fs');
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');

const app = express();
const port = 3001;

// Configure CORS
app.use(cors());

// Configure file upload
const upload = multer({ 
  dest: './uploads/', // This will store uploaded files in a folder called uploads
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB file size limit
});

// Create uploads folder if it doesn't exist
const uploadsFolder = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsFolder)){
    fs.mkdirSync(uploadsFolder);
}

// File upload endpoint
app.post('/upload', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'No file uploaded' });
    }

    // Here you can process the uploaded file
    // For now, we'll just return the file information
    return res.status(200).json({
      message: 'File uploaded successfully',
      fileName: req.file.filename,
      fileSize: req.file.size
    });
  } catch (error) {
    return res.status(500).json({ message: 'Error uploading file' });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Backend server running on http://localhost:${port}`);
});