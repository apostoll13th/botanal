import React from 'react';
import { useTheme } from '../ThemeContext';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  const handleClick = () => {
    console.log('Current theme:', theme);
    console.log('Document classes before:', document.documentElement.classList.toString());
    toggleTheme();
    setTimeout(() => {
      console.log('Document classes after:', document.documentElement.classList.toString());
    }, 100);
  };

  return (
    <button
      onClick={handleClick}
      className="theme-toggle-btn"
      aria-label="Toggle theme"
      title={theme === 'light' ? 'Переключить на тёмную тему' : 'Переключить на светлую тему'}
    >
      {theme === 'light' ? (
        // Луна для светлой темы (переключить на темную)
        <svg className="theme-icon" fill="currentColor" viewBox="0 0 24 24">
          <path d="M21.64,13a1,1,0,0,0-1.05-.14,8.05,8.05,0,0,1-3.37.73A8.15,8.15,0,0,1,9.08,5.49a8.59,8.59,0,0,1,.25-2A1,1,0,0,0,8,2.36,10.14,10.14,0,1,0,22,14.05,1,1,0,0,0,21.64,13Zm-9.5,6.69A8.14,8.14,0,0,1,7.08,5.22v.27A10.15,10.15,0,0,0,17.22,15.63a9.79,9.79,0,0,0,2.1-.22A8.11,8.11,0,0,1,12.14,19.73Z" />
        </svg>
      ) : (
        // Солнце для темной темы (переключить на светлую)
        <svg className="theme-icon" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12,17a5,5,0,1,1,5-5A5,5,0,0,1,12,17Zm0-8a3,3,0,1,0,3,3A3,3,0,0,0,12,9Z" />
          <path d="M12,2a1,1,0,0,0-1,1V5a1,1,0,0,0,2,0V3A1,1,0,0,0,12,2Z" />
          <path d="M21,11H19a1,1,0,0,0,0,2h2a1,1,0,0,0,0-2Z" />
          <path d="M12,20a1,1,0,0,0-1,1v2a1,1,0,0,0,2,0V21A1,1,0,0,0,12,20Z" />
          <path d="M5,11H3a1,1,0,0,0,0,2H5a1,1,0,0,0,0-2Z" />
          <path d="M17.66,6.34a1,1,0,0,0,.7-.29l1.41-1.41a1,1,0,1,0-1.41-1.41L17,4.64a1,1,0,0,0,0,1.41A1,1,0,0,0,17.66,6.34Z" />
          <path d="M6.34,17.66a1,1,0,0,0-.7.29L4.22,19.37a1,1,0,1,0,1.41,1.41L7,19.37a1,1,0,0,0,0-1.41A1,1,0,0,0,6.34,17.66Z" />
          <path d="M19.37,17.66a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41l1.41,1.41a1,1,0,0,0,1.41-1.41Z" />
          <path d="M6.34,6.34a1,1,0,0,0,.7-.29,1,1,0,0,0,0-1.41L5.64,3.22A1,1,0,0,0,4.22,4.64l1.41,1.41A1,1,0,0,0,6.34,6.34Z" />
        </svg>
      )}
    </button>
  );
};

export default ThemeToggle;
