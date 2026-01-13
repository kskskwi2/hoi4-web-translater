import { useState, useEffect } from 'react';
import { X, Save, Key, Globe, Cpu, FolderOpen, BookOpen, Plus, Trash2 } from 'lucide-react';

const LANGUAGES = [
    { code: 'ko', name: 'Korean (한국어)' },
    { code: 'ja', name: 'Japanese (日本語)' },
    { code: 'zh-CN', name: 'Chinese Simplified (简体中文)' },
    { code: 'zh-TW', name: 'Chinese Traditional (繁體中文)' },
    { code: 'ru', name: 'Russian (Русский)' },
    { code: 'de', name: 'German (Deutsch)' },
    { code: 'fr', name: 'French (Français)' },
    { code: 'es', name: 'Spanish (Español)' },
    { code: 'pt', name: 'Portuguese (Português)' },
    { code: 'pl', name: 'Polish (Polski)' },
];

const DEFAULT_SETTINGS = {
    targetLang: 'ko',
    vanillaPath: 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Hearts of Iron IV',
    openaiKey: '',
    openaiModel: 'gpt-4o-mini',
    claudeKey: '',
    claudeModel: 'claude-3-5-sonnet-20241022',
    geminiKey: '',
    geminiModel: 'gemini-1.5-flash',
    ollamaUrl: 'http://localhost:11434',
    ollamaModel: 'gemma2',
    glossary: {}, // { "Reich": "제국", "Fuhrer": "총통" }
};

export function SettingsModal({ isOpen, onClose, settings, onSave }) {
    const [localSettings, setLocalSettings] = useState(settings || DEFAULT_SETTINGS);
    const [activeTab, setActiveTab] = useState('general'); // general, glossary
    const [newTerm, setNewTerm] = useState({ key: '', value: '' });

    useEffect(() => {
        if (settings) {
            setLocalSettings(prev => ({ ...prev, ...settings }));
        }
    }, [settings]);

    const handleChange = (key, value) => {
        setLocalSettings(prev => ({ ...prev, [key]: value }));
    };

    const addGlossaryTerm = () => {
        if (!newTerm.key || !newTerm.value) return;
        setLocalSettings(prev => ({
            ...prev,
            glossary: { ...prev.glossary, [newTerm.key]: newTerm.value }
        }));
        setNewTerm({ key: '', value: '' });
    };

    const removeGlossaryTerm = (key) => {
        const newGlossary = { ...localSettings.glossary };
        delete newGlossary[key];
        setLocalSettings(prev => ({ ...prev, glossary: newGlossary }));
    };

    const handleSave = () => {
        onSave(localSettings);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
        }}>
            <div style={{
                background: 'var(--bg-primary)',
                borderRadius: '1rem',
                width: '700px',
                maxHeight: '85vh',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid var(--border)'
            }}>
                {/* Header */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem 1.5rem',
                    borderBottom: '1px solid var(--border)'
                }}>
                    <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Cpu size={24} />
                        Settings
                    </h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}>
                        <X size={24} />
                    </button>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)' }}>
                    <button
                        onClick={() => setActiveTab('general')}
                        style={{
                            flex: 1,
                            padding: '1rem',
                            background: activeTab === 'general' ? 'var(--bg-primary)' : 'transparent',
                            border: 'none',
                            borderBottom: activeTab === 'general' ? '2px solid var(--accent)' : 'none',
                            color: activeTab === 'general' ? 'var(--accent)' : 'var(--text-secondary)',
                            fontWeight: 'bold',
                            cursor: 'pointer'
                        }}
                    >
                        General & AI
                    </button>
                    <button
                        onClick={() => setActiveTab('glossary')}
                        style={{
                            flex: 1,
                            padding: '1rem',
                            background: activeTab === 'glossary' ? 'var(--bg-primary)' : 'transparent',
                            border: 'none',
                            borderBottom: activeTab === 'glossary' ? '2px solid var(--accent)' : 'none',
                            color: activeTab === 'glossary' ? 'var(--accent)' : 'var(--text-secondary)',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <BookOpen size={18} />
                        Glossary
                    </button>
                </div>

                {/* Content */}
                <div style={{ padding: '1.5rem', overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    
                    {activeTab === 'general' ? (
                        <>
                            {/* Target Language */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Globe size={18} />
                                    Target Language
                                </label>
                                <select
                                    value={localSettings.targetLang}
                                    onChange={(e) => handleChange('targetLang', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-secondary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '0.5rem',
                                        color: 'var(--text-primary)'
                                    }}
                                >
                                    {LANGUAGES.map(lang => (
                                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Vanilla Path Setting */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <FolderOpen size={18} />
                                    HoI4 Installation Path (For Vanilla Reference)
                                </label>
                                <input
                                    type="text"
                                    placeholder="C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
                                    value={localSettings.vanillaPath}
                                    onChange={(e) => handleChange('vanillaPath', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-secondary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '0.5rem',
                                        color: 'var(--text-primary)'
                                    }}
                                />
                                <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                    * Used to copy official translations for matching text (Translation Memory).
                                </p>
                            </div>

                            <hr style={{ border: 'none', borderTop: '1px solid var(--border)' }} />

                            {/* OpenAI Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    OpenAI GPT
                                </label>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.5rem' }}>
                                        <input
                                            type="password"
                                            placeholder="API Key (sk-...)"
                                            value={localSettings.openaiKey}
                                            onChange={(e) => handleChange('openaiKey', e.target.value)}
                                            style={{
                                                padding: '0.75rem',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '0.5rem',
                                                color: 'var(--text-primary)'
                                            }}
                                        />
                                        <button 
                                            className="btn"
                                            onClick={async () => {
                                                if (!localSettings.openaiKey) return alert("Enter API Key first");
                                                try {
                                                    const res = await fetch(`http://127.0.0.1:8000/api/translate/openai/models?api_key=${localSettings.openaiKey}`);
                                                    const data = await res.json();
                                                    if (data.models && data.models.length > 0) {
                                                        alert(`Found ${data.models.length} models! First: ${data.models[0]}`);
                                                    } else {
                                                        alert("No GPT models found or invalid key.");
                                                    }
                                                } catch(e) { alert("Failed to fetch models"); }
                                            }}
                                            style={{
                                                background: 'var(--accent)',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '0.5rem',
                                                padding: '0 1rem',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Fetch
                                        </button>
                                    </div>
                                    <select
                                        value={localSettings.openaiModel}
                                        onChange={(e) => handleChange('openaiModel', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    >
                                        <option value="gpt-4o-mini">gpt-4o-mini (Recommended)</option>
                                        <option value="gpt-4o">gpt-4o (Best Quality)</option>
                                        <option value="gpt-4-turbo">gpt-4-turbo</option>
                                        <option value="gpt-3.5-turbo">gpt-3.5-turbo (Fast)</option>
                                    </select>
                                </div>
                            </div>

                            {/* Claude Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    Claude AI
                                </label>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                    <input
                                        type="password"
                                        placeholder="API Key"
                                        value={localSettings.claudeKey}
                                        onChange={(e) => handleChange('claudeKey', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    />
                                    <select
                                        value={localSettings.claudeModel}
                                        onChange={(e) => handleChange('claudeModel', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    >
                                        <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet</option>
                                        <option value="claude-3-opus-20240229">claude-3-opus</option>
                                        <option value="claude-3-haiku-20240307">claude-3-haiku</option>
                                    </select>
                                </div>
                            </div>

                            {/* Gemini Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    Gemini AI
                                </label>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
                                        <input
                                            type="password"
                                            placeholder="API Key"
                                            value={localSettings.geminiKey}
                                            onChange={(e) => handleChange('geminiKey', e.target.value)}
                                            style={{
                                                padding: '0.75rem',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '0.5rem',
                                                color: 'var(--text-primary)'
                                            }}
                                        />
                                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                            <a 
                                                href="https://aistudio.google.com/app/apikey" 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                style={{ fontSize: '0.85rem', color: '#60a5fa', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                            >
                                                <Globe size={14} />
                                                Get API Key via Google
                                            </a>
                                        </div>
                                    </div>
                                    <select
                                        value={localSettings.geminiModel}
                                        onChange={(e) => handleChange('geminiModel', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    >
                                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                                        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                                    </select>
                                </div>
                            </div>

                    {/* Ollama Settings */}
                    <div>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                            <Cpu size={18} />
                            Ollama (Local)
                        </label>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.5rem' }}>
                                <input
                                    type="text"
                                    placeholder="Server URL"
                                    value={localSettings.ollamaUrl}
                                    onChange={(e) => handleChange('ollamaUrl', e.target.value)}
                                    style={{
                                        padding: '0.75rem',
                                        background: 'var(--bg-secondary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '0.5rem',
                                        color: 'var(--text-primary)'
                                    }}
                                />
                                <button 
                                    className="btn"
                                    onClick={async () => {
                                        try {
                                            const url = localSettings.ollamaUrl || 'http://localhost:11434';
                                            const res = await fetch(`http://127.0.0.1:8080/api/translate/ollama/models?base_url=${encodeURIComponent(url)}`);
                                            const data = await res.json();
                                            if (data.models && data.models.length > 0) {
                                                alert(`Found ${data.models.length} models: \n${data.models.join(', ')}`);
                                            } else {
                                                alert("No models found. Check if Ollama is running.");
                                            }
                                        } catch(e) { 
                                            alert("Failed to connect to Ollama. Ensure it's running."); 
                                        }
                                    }}
                                    style={{
                                        background: 'var(--accent)',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '0.5rem',
                                        padding: '0 1rem',
                                        cursor: 'pointer'
                                    }}
                                >
                                    Fetch
                                </button>
                            </div>
                            <input
                                type="text"
                                placeholder="Model Name (e.g. gemma2, llama3)"
                                value={localSettings.ollamaModel}
                                onChange={(e) => handleChange('ollamaModel', e.target.value)}
                                style={{
                                    padding: '0.75rem',
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '0.5rem',
                                    color: 'var(--text-primary)'
                                }}
                            />
                        </div>
                    </div>
                        </>
                    ) : (
                        // Glossary Tab Content
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
                            <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
                                <p style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                    Define words that should be translated specifically. Useful for names, ranks, or lore terms.
                                </p>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem' }}>
                                    <input
                                        type="text"
                                        placeholder="Original (e.g. Reich)"
                                        value={newTerm.key}
                                        onChange={(e) => setNewTerm({ ...newTerm, key: e.target.value })}
                                        style={{ padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                                    />
                                    <input
                                        type="text"
                                        placeholder="Translation (e.g. 제국)"
                                        value={newTerm.value}
                                        onChange={(e) => setNewTerm({ ...newTerm, value: e.target.value })}
                                        style={{ padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                                    />
                                    <button 
                                        onClick={addGlossaryTerm}
                                        style={{ background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '0.25rem', padding: '0 1rem', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                                    >
                                        <Plus size={18} />
                                    </button>
                                </div>
                            </div>

                            <div style={{ flex: 1, overflow: 'auto', border: '1px solid var(--border)', borderRadius: '0.5rem' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ background: 'var(--bg-secondary)', position: 'sticky', top: 0 }}>
                                        <tr>
                                            <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>Original</th>
                                            <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>Translation</th>
                                            <th style={{ padding: '0.75rem', width: '40px', borderBottom: '1px solid var(--border)' }}></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {localSettings.glossary && Object.entries(localSettings.glossary).map(([key, value]) => (
                                            <tr key={key} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '0.75rem' }}>{key}</td>
                                                <td style={{ padding: '0.75rem' }}>{value}</td>
                                                <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                                                    <button 
                                                        onClick={() => removeGlossaryTerm(key)}
                                                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                        {(!localSettings.glossary || Object.keys(localSettings.glossary).length === 0) && (
                                            <tr>
                                                <td colSpan="3" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                                    No terms added yet.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer */}
                <div style={{
                    padding: '1rem 1.5rem',
                    borderTop: '1px solid var(--border)',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    gap: '0.5rem'
                }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '0.75rem 1.5rem',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border)',
                            borderRadius: '0.5rem',
                            color: 'var(--text-primary)',
                            cursor: 'pointer'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="btn"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <Save size={18} />
                        Save Settings
                    </button>
                </div>
            </div>
        </div>
    );
}

export { LANGUAGES, DEFAULT_SETTINGS };
