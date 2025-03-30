const express = require('express');
const app = express();
const multer = require('multer');
const upload = multer({ dest: './uploads/' });

app.use(express.json());

app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    res.status(400).send('No file was uploaded.');
  } else {
    res.send(`File uploaded successfully: ${req.file.originalname}`);
  }
});

app.listen(3001, () => {
  console.log('Server listening on port 3001');
});