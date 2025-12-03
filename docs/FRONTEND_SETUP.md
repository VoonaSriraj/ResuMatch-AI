# Frontend Setup Guide

## Prerequisites
- Node.js 16+
- npm or bun package manager

## Installation Steps

1. Install dependencies:
```bash
bun install
# or
npm install
```

2. Create .env file with:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_client_id
VITE_GITHUB_CLIENT_ID=your_github_id
```

3. Start development server:
```bash
bun run dev
# or
npm run dev
```

4. Build for production:
```bash
bun run build
# or
npm run build
```
