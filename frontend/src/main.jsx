import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './assets/styles/main.css'; // Import the CSS file from your assets folder

// Create the root and render the app
const root = createRoot(document.getElementById('root'));

// To ensure cookies (like JWT) are sent with every request
import axios from "axios";
axios.defaults.withCredentials = true;

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
