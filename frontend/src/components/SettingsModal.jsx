import { useState, useEffect } from 'react';
import { X, Save, Key, Globe, Cpu, FolderOpen, BookOpen, Plus, Trash2, Cloud, RefreshCw, ToggleLeft, ToggleRight, Power } from 'lucide-react';
import api from '../lib/api';
import { useLanguage } from '../contexts/LanguageContext';

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

const SOURCE_LANGUAGES = [
    { code: 'en', name: 'English (Default)' },
    { code: 'de', name: 'German' },
    { code: 'fr', name: 'French' },
    { code: 'ru', name: 'Russian' },
];

const DEFAULT_SETTINGS = {
    sourceLang: 'en',
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
    paratranzToken: '',
    paratranzProjectId: '', // New Field
    enableParaTranz: false, // Explicit toggle
    autoUploadParaTranz: false, // New Auto Upload setting
    autoShutdown: false,
};

export function SettingsModal({ isOpen, onClose, settings, onSave }) {
    const { t } = useLanguage();
    const [localSettings, setLocalSettings] = useState(settings || DEFAULT_SETTINGS);
    const [activeTab, setActiveTab] = useState('general'); // general, glossary, paratranz
    const [newTerm, setNewTerm] = useState({ key: '', value: '' });
    const [projects, setProjects] = useState([]);
    const [loadingProjects, setLoadingProjects] = useState(false);

    useEffect(() => {
            if (settings) {
            setLocalSettings(prev => ({ 
                ...prev, 
                ...settings,
                // Ensure paratranzProjectId is mapped correctly if it comes as snake_case from backend
                paratranzProjectId: settings.paratranzProjectId || settings.paratranz_project_id || '' 
            }));
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

    const fetchProjects = async () => {
        if (!localSettings.paratranzToken) return;
        setLoadingProjects(true);
        try {
            const res = await api.get('/paratranz/projects', {
                headers: { Authorization: localSettings.paratranzToken }
            });
            setProjects(res.data);
        } catch (err) {
            console.error(err);
            alert(t('no_projects'));
        } finally {
            setLoadingProjects(false);
        }
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
                        {t('settings')}
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
                        {t('tab_general')}
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
                        {t('tab_glossary')}
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'paratranz' ? 'active' : ''}`}
                        onClick={() => setActiveTab('paratranz')}
                        style={{
                            flex: 1,
                            padding: '1rem',
                            background: activeTab === 'paratranz' ? 'var(--bg-primary)' : 'transparent',
                            border: 'none',
                            borderBottom: activeTab === 'paratranz' ? '2px solid var(--accent)' : 'none',
                            color: activeTab === 'paratranz' ? 'var(--accent)' : 'var(--text-secondary)',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <Cloud size={16} /> {t('tab_paratranz')}
                    </button>
                </div>

                {/* Content */}
                <div style={{ padding: '1.5rem', overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    
                    {activeTab === 'general' && (
                        <>
                            {/* Source Language */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Globe size={18} />
                                    Source Language
                                </label>
                                <select
                                    value={localSettings.sourceLang || 'en'}
                                    onChange={(e) => handleChange('sourceLang', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-secondary)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '0.5rem',
                                        color: 'var(--text-primary)'
                                    }}
                                >
                                    {SOURCE_LANGUAGES.map(lang => (
                                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Target Language */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Globe size={18} />
                                    {t('target_language')}
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
                                    {t('vanilla_path')}
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
                                    {t('vanilla_path_desc')}
                                </p>
                            </div>

                            {/* Auto Shutdown Setting */}
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'space-between',
                                background: 'var(--bg-secondary)',
                                padding: '0.75rem',
                                borderRadius: '0.5rem',
                                border: '1px solid var(--border)',
                                marginTop: '0.5rem'
                            }}>
                                <div>
                                    <h4 style={{ margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.95rem' }}>
                                        <Power size={18} />
                                        {t('auto_shutdown')}
                                    </h4>
                                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {t('auto_shutdown_desc')}
                                    </p>
                                </div>
                                <button 
                                    onClick={() => handleChange('autoShutdown', !localSettings.autoShutdown)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: localSettings.autoShutdown ? '#ef4444' : 'var(--text-secondary)' }}
                                >
                                    {localSettings.autoShutdown ? <ToggleRight size={40} /> : <ToggleLeft size={40} />}
                                </button>
                            </div>

                            <hr style={{ border: 'none', borderTop: '1px solid var(--border)' }} />

                            {/* OpenAI Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    {t('openai_gpt')}
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
                                                        alert(t('model_fetch_success').replace('{count}', data.models.length).replace('{first}', data.models[0]));
                                                    } else {
                                                        alert(t('model_fetch_fail'));
                                                    }
                                                } catch(e) { alert(t('model_fetch_fail')); }
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
                                            {t('fetch')}
                                        </button>
                                    </div>
                                    <input
                                        type="text"
                                        list="openaiModels"
                                        placeholder="Model Name (e.g. gpt-4o)"
                                        value={localSettings.openaiModel}
                                        onChange={(e) => handleChange('openaiModel', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)',
                                            width: '100%'
                                        }}
                                    />
                                    <datalist id="openaiModels">
                                        <option value="gpt-4o-mini">gpt-4o-mini (Recommended)</option>
                                        <option value="gpt-4o">gpt-4o (Best Quality)</option>
                                        <option value="gpt-4-turbo">gpt-4-turbo</option>
                                        <option value="gpt-3.5-turbo">gpt-3.5-turbo (Fast)</option>
                                        <option value="o1-preview">o1-preview</option>
                                        <option value="o1-mini">o1-mini</option>
                                    </datalist>
                                </div>
                            </div>

                            {/* Claude Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    {t('claude_ai')}
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
                                    <input
                                        type="text"
                                        list="claudeModels"
                                        placeholder="Model Name (e.g. claude-3-5-sonnet)"
                                        value={localSettings.claudeModel}
                                        onChange={(e) => handleChange('claudeModel', e.target.value)}
                                        style={{
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    />
                                    <datalist id="claudeModels">
                                        <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet</option>
                                        <option value="claude-3-opus-20240229">claude-3-opus</option>
                                        <option value="claude-3-haiku-20240307">claude-3-haiku</option>
                                        <option value="claude-3-5-sonnet-latest">claude-3-5-sonnet-latest</option>
                                        <option value="claude-3-5-haiku-latest">claude-3-5-haiku-latest</option>
                                    </datalist>
                                </div>
                            </div>

                            {/* Gemini Settings */}
                            <div>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                    <Key size={18} />
                                    {t('gemini_ai')}
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
                                                {t('get_api_key')}
                                            </a>
                                        </div>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            list="geminiModels"
                                            placeholder="Model Name (e.g. gemini-1.5-flash)"
                                            value={localSettings.geminiModel}
                                            onChange={(e) => handleChange('geminiModel', e.target.value)}
                                            style={{
                                                padding: '0.75rem',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '0.5rem',
                                                color: 'var(--text-primary)',
                                                width: '100%'
                                            }}
                                        />
                                        <button 
                                            className="btn"
                                            onClick={async () => {
                                                if (!localSettings.geminiKey) return alert("Enter API Key first");
                                                try {
                                                    const res = await fetch(`http://127.0.0.1:8080/api/translate/gemini/models?api_key=${localSettings.geminiKey}`);
                                                    const data = await res.json();
                                                    if (data.models && data.models.length > 0) {
                                                        alert(t('model_fetch_success').replace('{count}', data.models.length).replace('{first}', data.models[0]));
                                                        // Note: Datalist doesn't automatically update from fetch unless we store it in state.
                                                        // But user can type anyway.
                                                    } else {
                                                        alert(t('model_fetch_fail'));
                                                    }
                                                } catch(e) { alert(t('model_fetch_fail')); }
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
                                            {t('fetch')}
                                        </button>
                                    </div>
                                    <datalist id="geminiModels">
                                        <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp (New)</option>
                                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                                        <option value="gemini-exp-1206">gemini-exp-1206</option>
                                    </datalist>
                                </div>
                            </div>

                    {/* Ollama Settings */}
                    <div>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                            <Cpu size={18} />
                            {t('ollama_local')}
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
                                                alert(t('ollama_fetch_success').replace('{count}', data.models.length).replace('{models}', data.models.join(', ')));
                                            } else {
                                                alert(t('ollama_fetch_fail'));
                                            }
                                        } catch(e) { 
                                            alert(t('ollama_conn_fail')); 
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
                                    {t('fetch')}
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
                    )}

                    {activeTab === 'glossary' && (
                        // Glossary Tab Content
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
                            <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
                                <p style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                    {t('glossary_desc')}
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
                                            <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>{t('original')}</th>
                                            <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>{t('translation')}</th>
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
                                                    {t('no_terms')}
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                    
                    {activeTab === 'paratranz' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
                            {/* Toggle Switch */}
                            <div style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'space-between',
                                background: 'var(--bg-secondary)',
                                padding: '1rem',
                                borderRadius: '0.5rem',
                                border: '1px solid var(--border)'
                            }}>
                                <div>
                                    <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem' }}>{t('enable_paratranz')}</h3>
                                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                        {t('enable_paratranz_desc')}
                                    </p>
                                </div>
                                <button 
                                    onClick={() => handleChange('enableParaTranz', !localSettings.enableParaTranz)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: localSettings.enableParaTranz ? 'var(--accent)' : 'var(--text-secondary)' }}
                                >
                                    {localSettings.enableParaTranz ? <ToggleRight size={40} /> : <ToggleLeft size={40} />}
                                </button>
                            </div>

                            {/* Auto Upload Toggle (Only visible if enabled) */}
                            {localSettings.enableParaTranz && (
                                <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'space-between',
                                    background: 'var(--bg-secondary)',
                                    padding: '1rem',
                                    borderRadius: '0.5rem',
                                    border: '1px solid var(--border)'
                                }}>
                                    <div>
                                        <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem' }}>{t('auto_upload_paratranz') || 'Auto Upload'}</h3>
                                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            {t('auto_upload_desc') || 'Automatically upload files to ParaTranz after translation completes'}
                                        </p>
                                    </div>
                                    <button 
                                        onClick={() => handleChange('autoUploadParaTranz', !localSettings.autoUploadParaTranz)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: localSettings.autoUploadParaTranz ? 'var(--accent)' : 'var(--text-secondary)' }}
                                    >
                                        {localSettings.autoUploadParaTranz ? <ToggleRight size={40} /> : <ToggleLeft size={40} />}
                                    </button>
                                </div>
                            )}

                            {/* Project ID Input (New) */}
                            {localSettings.enableParaTranz && (
                                <div className="form-group">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                        <FolderOpen size={18} />
                                        {t('paratranz_project_id')}
                                    </label>
                                    <input
                                        type="number"
                                        placeholder="e.g. 12345"
                                        value={localSettings.paratranzProjectId}
                                        onChange={(e) => handleChange('paratranzProjectId', e.target.value)}
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem',
                                            background: 'var(--bg-secondary)',
                                            border: '1px solid var(--border)',
                                            borderRadius: '0.5rem',
                                            color: 'var(--text-primary)'
                                        }}
                                    />
                                    <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {t('paratranz_project_id_desc')}
                                    </p>
                                </div>
                            )}

                            {/* Token Input (only visible if enabled) */}
                            {localSettings.enableParaTranz && (
                                <>
                                    <div className="form-group">
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                            <Key size={18} />
                                            {t('paratranz_token')}
                                        </label>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <input
                                                type="password"
                                                name="paratranzToken"
                                                value={localSettings.paratranzToken}
                                                onChange={(e) => handleChange('paratranzToken', e.target.value)}
                                                placeholder={t('paratranz_token_placeholder')}
                                                style={{
                                                    flex: 1,
                                                    padding: '0.75rem',
                                                    background: 'var(--bg-secondary)',
                                                    border: '1px solid var(--border)',
                                                    borderRadius: '0.5rem',
                                                    color: 'var(--text-primary)'
                                                }}
                                            />
                                            <button 
                                                className="btn" 
                                                onClick={fetchProjects} 
                                                disabled={!localSettings.paratranzToken}
                                                style={{
                                                    background: 'var(--accent)',
                                                    color: 'white',
                                                    border: 'none',
                                                    borderRadius: '0.5rem',
                                                    padding: '0 1rem',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.5rem'
                                                }}
                                            >
                                                {loadingProjects ? <RefreshCw className="spin" size={16} /> : t('list_projects')}
                                            </button>
                                        </div>
                                        <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                            {t('paratranz_link_desc')}
                                        </p>
                                    </div>
                                    
                                    {projects.length > 0 && (
                                        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '4px' }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                                <thead style={{ background: 'var(--bg-secondary)', textAlign: 'left' }}>
                                                    <tr>
                                                        <th style={{ padding: '0.5rem' }}>ID</th>
                                                        <th style={{ padding: '0.5rem' }}>Name</th>
                                                        <th style={{ padding: '0.5rem' }}>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {projects.map(p => (
                                                        <tr key={p.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                            <td style={{ padding: '0.5rem' }}>{p.id}</td>
                                                            <td style={{ padding: '0.5rem' }}>{p.name}</td>
                                                            <td style={{ padding: '0.5rem' }}>{p.public ? 'Public' : 'Private'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                    {projects.length === 0 && localSettings.paratranzToken && !loadingProjects && (
                                        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)', border: '1px dashed var(--border)', borderRadius: '0.5rem' }}>
                                            {t('no_projects')}
                                        </div>
                                    )}
                                </>
                            )}
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
                        {t('cancel')}
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
                        {t('save_settings')}
                    </button>
                </div>
            </div>
        </div>
    );
}

export { LANGUAGES, DEFAULT_SETTINGS };
