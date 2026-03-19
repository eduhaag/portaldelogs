const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = Number(process.env.PORT || 3000);
const DIST_DIR = path.join(__dirname, '..', 'frontend-angular', 'dist', 'frontend-angular', 'browser');

// This folder no longer contains a React application.
// It is only the thin HTTP layer that serves the Angular build and proxies the API.

// Proxy /api requests to backend
app.use('/api', createProxyMiddleware({
    target: 'http://127.0.0.1:8001',
    changeOrigin: true,
}));

// Serve static Angular build files
app.use(express.static(DIST_DIR));

// For Angular routing - serve index.html for all non-API, non-static routes
app.get('*', (req, res) => {
    res.sendFile(path.join(DIST_DIR, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend server running on port ${PORT}`);
    console.log(`Serving Angular build from: ${DIST_DIR}`);
});
