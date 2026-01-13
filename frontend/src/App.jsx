import { useState, useEffect } from 'react';
import { Settings, RefreshCw, FolderOpen, Globe, Search, LayoutGrid, List as ListIcon } from 'lucide-react';
import api from './lib/api';
import { useLanguage } from './contexts/LanguageContext';
import { SettingsModal, DEFAULT_SETTINGS, LANGUAGES } from './components/SettingsModal';

function App() {
  const [mods, setMods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [selectedService, setSelectedService] = useState('google');
  const [lastTranslation, setLastTranslation] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [progress, setProgress] = useState({ percent: 0, currentFile: '', status: 'idle' });
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('hoi4_translator_settings');
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
  });

  const { t, language, setLanguage } = useLanguage();

  useEffect(() => {
    fetchConfig();
  }, []);

  useEffect(() => {
    localStorage.setItem('hoi4_translator_settings', JSON.stringify(settings));
  }, [settings]);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/config');
      setConfig(res.data);
      if (res.data.workshop_path) {
        scanMods(res.data.workshop_path);
      }
    } catch (err) {
      console.error(t('config_error'), err);
    }
  };

  const scanMods = async (path) => {
    setLoading(true);
    try {
      const res = await api.post('/mods/scan', { workshop_path: path });
      if (res.data.mods && res.data.mods.length > 0) {
        setMods(res.data.mods);
      } else {
        setMods([]);
        alert("No mods found in the selected folder. Please check your Steam Workshop path in Settings.");
      }
    } catch (err) {
      console.error(t('scan_error'), err);
      alert("Failed to scan mods. Make sure the backend is running and the path is correct.");
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'ko' : 'en');
  };

  const getTargetLangName = () => {
    const lang = LANGUAGES.find(l => l.code === settings.targetLang);
    return lang ? lang.name.split(' ')[0] : settings.targetLang;
  };

  const translateMod = async (mod) => {
    if (!config || !config.documents_path) {
      alert(t('config_error'));
      return;
    }

    const langName = getTargetLangName();
    if (!confirm(`${t('translate')} ${mod.name} to ${langName} with ${selectedService}?`)) return;

    setLoading(true);
    setLastTranslation(null);

    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await api.get('/translate/status');
        const data = statusRes.data;
        setProgress({
          percent: data.percent || 0,
          currentFile: data.current_file || '',
          status: data.status || 'idle',
          processed_files: data.processed_files || 0,
          total_files: data.total_files || 0,
          current_entry: data.current_entry || 0,
          total_entries: data.total_entries || 0,
          entries_translated: data.entries_translated || 0,
          avg_speed: data.avg_speed || 0,
          start_time: data.start_time || 0
        });
      } catch (e) { }
    }, 500);  // Poll faster for smoother updates

    try {
      // Build payload with settings
      const payload = {
        mod_path: mod.path,
        mod_name: mod.name,
        mod_id: mod.id || "local",
        output_path: config.documents_path,
        service: selectedService,
        target_lang: settings.targetLang,
        vanilla_path: settings.vanillaPath, // Pass vanilla path
        // Pass service-specific settings
        settings: {
          openai_key: settings.openaiKey,
          openai_model: settings.openaiModel,
          claude_key: settings.claudeKey,
          claude_model: settings.claudeModel,
          gemini_key: settings.geminiKey,
          gemini_model: settings.geminiModel,
          ollama_url: settings.ollamaUrl,
          ollama_model: settings.ollamaModel,
        }
      };
      const res = await api.post('/translate/run', payload);
      
      // Since it's background task now, we just wait for polling to show completion
      // But we need to know when it's ACTUALLY done to show the alert.
      // The poll interval logic needs to detect 'completed' status.
      
      // We'll modify the poll loop to handle completion instead of waiting for this POST to return a result
      // The POST returns { status: "started" } immediately now.

    } catch (err) {
      console.error(err);
      alert("Translation failed to start. " + (err.response?.data?.detail || err.message));
      setLoading(false);
      clearInterval(pollInterval);
    }
  };
  
  // Effect to handle polling logic better separately? 
  // For now, let's just update the translateMod function's polling to handle completion
  
  // RE-WRITE translateMod to handle background task flow
  const translateMod2 = async (mod) => {
     if (!config || !config.documents_path) {
      alert(t('config_error'));
      return;
    }

    const langName = getTargetLangName();
    if (!confirm(`${t('translate')} ${mod.name} to ${langName} with ${selectedService}?`)) return;

    setLoading(true);
    setLastTranslation(null);

    try {
        const payload = {
            mod_path: mod.path,
            mod_name: mod.name,
            mod_id: mod.id || "local",
            output_path: config.documents_path,
            service: selectedService,
            target_lang: settings.targetLang,
            vanilla_path: settings.vanillaPath,
            settings: {
                openai_key: settings.openaiKey,
                openai_model: settings.openaiModel,
                claude_key: settings.claudeKey,
                claude_model: settings.claudeModel,
                gemini_key: settings.geminiKey,
                gemini_model: settings.geminiModel,
                ollama_url: settings.ollamaUrl,
                ollama_model: settings.ollamaModel,
            }
        };

        // Start background task
        await api.post('/translate/run', payload);
        
        // Poll for completion
        const interval = setInterval(async () => {
            try {
                const statusRes = await api.get('/translate/status');
                const data = statusRes.data;
                
                setProgress({
                    percent: data.percent || 0,
                    currentFile: data.current_file || '',
                    status: data.status || 'idle',
                    processed_files: data.processed_files || 0,
                    total_files: data.total_files || 0,
                    current_entry: data.current_entry || 0,
                    total_entries: data.total_entries || 0,
                    entries_translated: data.entries_translated || 0
                });

                if (data.status === 'completed') {
                    clearInterval(interval);
                    setLoading(false);
                    
                    // Auto zip logic (can trigger manually or backend can do it, but here we do it from frontend to get path)
                    // The result path is needed. The status endpoint should probably return it or we reconstruct it.
                    // For now, let's assume standard naming if backend doesn't provide it in status.
                    // Actually, status endpoint in backend currently just returns progress dict.
                    // We might need to enhance status to return result path on completion.
                    
                    // Let's assume the user can just look at the folder for now, or we enhance backend status.
                    // Quick fix: Modify backend to store result in progress dict.
                    
                    if (data.path) {
                         const zipRes = await api.post(`/translate/zip?path=${encodeURIComponent(data.path)}&name=${encodeURIComponent(data.zip_name)}`);
                         setLastTranslation({
                            modId: mod.id || mod.path,
                            zipPath: zipRes.data.zip_path,
                            path: data.path
                        });
                        alert(`Success! Processed ${data.processed_files} files.\nSaved at: ${data.path}\nReady to download.`);
                    } else {
                        alert("Translation completed!");
                    }
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    setLoading(false);
                    alert("Error during translation.");
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 1000);

    } catch (err) {
        console.error(err);
        alert("Failed to start translation: " + (err.response?.data?.detail || err.message));
        setLoading(false);
    }
  };

  const handleDownload = () => {
    if (lastTranslation && lastTranslation.zipPath) {
      // Direct download link
      window.location.href = `http://127.0.0.1:8000/api/translate/download/file?mod_id=0&zip_path=${encodeURIComponent(lastTranslation.zipPath)}`;
    }
  };

  // Filter mods
  const filteredMods = mods.filter(mod =>
    mod.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container">
      <header style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Globe size={32} color="var(--accent)" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{t('app_title')}</h1>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
                padding: '0.5rem',
                borderRadius: '0.5rem'
              }}
            >
              <option value="google">Google Translate</option>
              <option value="gemini">Gemini AI</option>
              <option value="openai">OpenAI GPT</option>
              <option value="claude">Claude AI</option>
              <option value="ollama">Ollama (Local)</option>
            </select>

            <button className="btn" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }} onClick={toggleLanguage}>
              {language.toUpperCase()}
            </button>
            <button className="btn" onClick={() => config && scanMods(config.workshop_path)}>
              <RefreshCw size={18} style={{ marginRight: '0.5rem' }} />
              {t('rescan_button')}
            </button>
            <button
              className="btn"
              style={{ background: 'var(--accent)' }}
              onClick={() => setShowSettings(true)}
            >
              <Settings size={18} style={{ marginRight: '0.5rem' }} />
              Settings
            </button>
          </div>
        </div>

        {/* Search & View Toggle Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, maxWidth: '400px' }}>
            <Search size={18} color="var(--text-secondary)" />
            <input
              type="text"
              placeholder="Search mods..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                width: '100%',
                outline: 'none',
                fontSize: '0.95rem'
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                background: viewMode === 'grid' ? 'var(--accent)' : 'transparent',
                border: 'none',
                padding: '0.4rem',
                borderRadius: '4px',
                cursor: 'pointer',
                color: viewMode === 'grid' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              <LayoutGrid size={20} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                background: viewMode === 'list' ? 'var(--accent)' : 'transparent',
                border: 'none',
                padding: '0.4rem',
                borderRadius: '4px',
                cursor: 'pointer',
                color: viewMode === 'list' ? '#fff' : 'var(--text-secondary)'
              }}
            >
              <ListIcon size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Path Info Bar */}
      {config && (
        <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '0.5rem', marginBottom: '2rem', fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.5rem', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <FolderOpen size={16} />
            <span><strong>Workshop:</strong> {config.workshop_path}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <FolderOpen size={16} />
            <span><strong>Output:</strong> {config.documents_path}</span>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
          <RefreshCw className="spin" size={48} />
          <p style={{ marginTop: '1rem', fontSize: '1.2rem' }}>Translating...</p>
          {progress.status === 'running' && (
            <div style={{ marginTop: '1.5rem', maxWidth: '500px', marginInline: 'auto' }}>
              {/* File Progress */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span>Files: {progress.processed_files || 0} / {progress.total_files || '?'}</span>
                  <span>{progress.percent}%</span>
                </div>
                <div style={{ background: 'var(--border)', borderRadius: '8px', height: '12px', overflow: 'hidden' }}>
                  <div
                    style={{
                      background: 'var(--accent)',
                      height: '100%',
                      width: `${progress.percent}%`,
                      transition: 'width 0.3s ease'
                    }}
                  />
                </div>
              </div>

              {/* Current File Info */}
              <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
                <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  📄 {progress.currentFile || 'Preparing...'}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <div>
                        Entry: {progress.current_entry} / {progress.total_entries}
                    </div>
                    <div>
                        Speed: {progress.avg_speed ? progress.avg_speed.toFixed(1) : 0} entries/s
                    </div>
                </div>
                <p style={{ margin: 0, fontSize: '0.85rem', marginTop: '0.5rem', color: 'var(--accent)' }}>
                  Total translated: {progress.entries_translated}
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={
          viewMode === 'grid'
            ? { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }
            : { display: 'flex', flexDirection: 'column', gap: '1rem' }
        }>
          {filteredMods.map((mod) => (
            <div key={mod.path} className="card" style={viewMode === 'list' ? { display: 'flex', flexDirection: 'row', height: '140px', alignItems: 'center' } : {}}>
              <div style={
                viewMode === 'list'
                  ? { width: '140px', height: '100%', background: '#334155', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }
                  : { height: '160px', background: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }
              }>
                {mod.thumbnail_path ? (
                  <img
                    src={`http://127.0.0.1:8000/api/images/proxy?path=${encodeURIComponent(mod.thumbnail_path)}`}
                    alt={mod.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <FolderOpen size={48} color="#475569" />
                )}
              </div>

              <div style={{ padding: '1rem', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: viewMode === 'list' ? '100%' : 'auto' }}>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{mod.name}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                    {t('version_label')}: {mod.supported_version || 'Unknown'}
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                    {mod.tags && mod.tags.slice(0, 3).map(tag => (
                      <span key={tag} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem' }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: (lastTranslation && (lastTranslation.modId === mod.id || lastTranslation.modId === mod.path)) ? '1fr 1fr' : '1fr', gap: '0.5rem' }}>
                  <button className="btn" style={{ width: '100%' }} onClick={() => translateMod2(mod)}>
                    {t('translate')}
                  </button>
                  {(lastTranslation && (lastTranslation.modId === mod.id || lastTranslation.modId === mod.path)) && (
                    <button className="btn" style={{ background: '#10b981' }} onClick={handleDownload}>
                      Download ZIP
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSave={setSettings}
      />
    </div>
  );
}

export default App;
