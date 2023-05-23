const express = require('express');
const path = require('path');
const serveStatic = require('serve-static');

const app = express();
app.use(serveStatic(path.join(__dirname, 'dist'))); // Serve static files from 'dist' directory

const port = process.env.PORT || 5000; // Listen on the appropriate port
app.listen(port, () => {
  console.log('Server is running on port ' + port);
});
