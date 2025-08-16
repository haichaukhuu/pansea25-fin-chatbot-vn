# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

# Financial Chatbot Frontend

A modern, responsive React frontend for a financial chatbot assistant designed for ASEAN markets. Built with React, TypeScript, Vite, and Tailwind CSS.

## Features

### Authentication
- **Login/Register Pages**: Secure authentication with sample demo account
- **Demo Account**: 
  - Email: `admin123@gmail.com`
  - Password: `admin123`

### Chat Interface
- **Modern Chat UI**: Clean, responsive chat interface optimized for both desktop and mobile
- **Real-time Messaging**: Instant message exchange with typing indicators
- **Message History**: Persistent chat history with timestamps

### Sidebar Panels
- **Left Sidebar (Chat History)**:
  - Collapsible panel with all previous conversations
  - Search functionality to find specific messages
  - User profile and settings access at the bottom
  - Chat management (create, delete, select)

- **Right Sidebar (Generated Files)**:
  - Display AI-generated files organized by date
  - File download functionality
  - Supports various file types (PDF, Excel, Word, images)

### File Handling
- **File Upload**: Support for documents and images
- **File Management**: Generated files are automatically organized and downloadable
- **Multiple Formats**: Supports PDF, DOC, XLSX, images, and more

### Voice Input
- **Speech Recognition**: Voice-to-text input using Web Speech API
- **Cross-browser Support**: Works on modern browsers with speech recognition

### User Profile & Settings
- **Profile Management**: Update user information and avatar
- **Account Settings**: Change password and account preferences
- **Preferences**: Theme selection, language settings, notifications
- **Multi-language Support**: English, Bahasa Indonesia, Bahasa Malaysia, Thai, Vietnamese, Filipino

## Technology Stack

- **React 19**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Heroicons**: Beautiful SVG icons
- **date-fns**: Date manipulation and formatting

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Navigate to the UI directory:
   ```bash
   cd ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:5173`

### Demo Account

For testing purposes, use the following credentials:
- **Email**: `admin123@gmail.com`
- **Password**: `admin123`

## Backend Integration Ready

The frontend is designed to integrate seamlessly with a Python backend through REST APIs. All components are structured to work with your backend once implemented.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
