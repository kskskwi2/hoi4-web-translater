import { createContext, useState, useContext } from 'react';
import en from '../locales/en.json';
import ko from '../locales/ko.json';

const translations = { en, ko };
const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const [language, setLanguage] = useState('ko'); // Default to Korean as per user context

    const t = (key) => {
        return translations[language][key] || key;
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => useContext(LanguageContext);
