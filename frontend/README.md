# Frontend - Physical AI Robotics Book

This directory contains the frontend code for the Physical AI Robotics Book project, including Docusaurus components and React hooks for the AI assistant functionality.

## Structure

### `src/components`
Contains custom React components for the Docusaurus site, including the chatbot UI.

### `src/hooks`
Contains custom React hooks, including the `useSelectionAI` hook for text selection and AI integration.

### `src/theme`
Contains custom theme components for the Docusaurus site.

### `src/css`
Contains custom CSS styles for the site.

### `src/pages`
Contains custom pages for the Docusaurus site.

## Key Features

### Text Selection AI Hook (`useSelectionAI.js`)
- Detects when user highlights text on the page
- Captures the selected text string
- Provides functionality to send selected text to the backend `/chat/selection` endpoint
- Integrates with the backend RAG system for contextual responses

## Environment Variables

The frontend may require the following environment variables:

- `REACT_APP_BACKEND_URL`: The URL of the backend API server
- `NEXT_PUBLIC_BACKEND_URL`: Alternative environment variable for Next.js projects

## Running the Frontend

This is a Docusaurus project. To run:

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. The site will be available at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

This will create a `build` directory with the production-ready site.