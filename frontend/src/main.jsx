import { createRoot } from 'react-dom/client';
import { App } from './App.jsx';
import './style.css';
import { captureAccountAction } from './accountBootstrap.js';

const accountAction = captureAccountAction(window.location, window.history);
createRoot(document.getElementById('root')).render(<App initialAccountAction={accountAction} />);
