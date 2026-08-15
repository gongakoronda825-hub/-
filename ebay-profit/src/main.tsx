import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { registerSW } from 'virtual:pwa-register';
import App from './App';
import './styles.css';

// オフライン動作用の Service Worker。新版は次回起動時に自動で入れ替える。
registerSW({ immediate: true });

const el = document.getElementById('root');
if (!el) throw new Error('#root が見つかりません');

createRoot(el).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
