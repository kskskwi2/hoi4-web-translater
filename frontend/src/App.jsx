import { useState, useEffect } from 'react';
import { Settings, RefreshCw, FolderOpen, Globe, Search, LayoutGrid, List as ListIcon, CloudUpload, Download } from 'lucide-react';
import api from './lib/api';
import { useLanguage } from './contexts/LanguageContext';
import { SettingsModal, DEFAULT_SETTINGS, LANGUAGES } from './components/SettingsModal';
import { ProjectSelectorModal } from './components/ProjectSelectorModal';

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
  
  // Project Selector State
    const [showProjectSelector, setShowProjectSelector] = useState(false);
    const [wakeLock, setWakeLock] = useState(null); // Screen Wake Lock

    // Initialize with defaults (no local storage)
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);

    // Selected mod for sync (ParaTranz)
    const [selectedModForSync, setSelectedModForSync] = useState(null);
    const [projectSelectorMode, setProjectSelectorMode] = useState('upload'); // 'upload' or 'download'

  const { t, language, setLanguage } = useLanguage();

  useEffect(() => {
    fetchConfig();
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
        const res = await api.get('/settings');
        if (res.data) {
            const s = res.data;
            let loadedGlossary = {};
            try {
                loadedGlossary = typeof s.glossary === 'string' ? JSON.parse(s.glossary) : (s.glossary || {});
            } catch (e) {
                console.error("Failed to parse glossary JSON", e);
            }

            setSettings(prev => ({
                ...prev,
                // Map Backend (snake_case) to Frontend (camelCase)
                sourceLang: s.source_language || 'en',
                targetLang: s.target_language || 'ko',
                vanillaPath: s.vanilla_path || prev.vanillaPath,
                
                openaiKey: s.openai_api_key || '',
                openaiModel: s.openai_model || 'gpt-4o-mini',
                
                claudeKey: s.claude_api_key || '',
                claudeModel: s.claude_model || 'claude-3-5-sonnet-20241022',
                
                geminiKey: s.gemini_api_key || '',
                geminiModel: s.gemini_model || 'gemini-1.5-flash',
                
                ollamaUrl: s.ollama_url || 'http://localhost:11434',
                ollamaModel: s.ollama_model || 'gemma2',
                
                paratranzToken: s.paratranz_token || '',
                paratranzProjectId: s.paratranz_project_id || '', // Map backend setting
                enableParaTranz: s.enable_paratranz || false,
                autoUploadParaTranz: s.auto_upload_paratranz || false, // Map backend setting
                
                autoShutdown: s.auto_shutdown || false,
                glossary: loadedGlossary
            }));
        }
    } catch (err) {
        console.error("Failed to load settings from DB", err);
    }
  };

  const handleSaveSettings = async (newSettings) => {
    // 1. Update Local State
    setSettings(newSettings);

    // 2. Persist to Backend DB
    try {
        const payload = {
            source_language: newSettings.sourceLang,
            target_language: newSettings.targetLang,
            vanilla_path: newSettings.vanillaPath,
            
            openai_api_key: newSettings.openaiKey,
            openai_model: newSettings.openaiModel,
            
            claude_api_key: newSettings.claudeKey,
            claude_model: newSettings.claudeModel,
            
            gemini_api_key: newSettings.geminiKey,
            gemini_model: newSettings.geminiModel,
            
            ollama_url: newSettings.ollamaUrl,
            ollama_model: newSettings.ollamaModel,
            
            paratranz_token: newSettings.paratranzToken,
            paratranz_project_id: newSettings.paratranzProjectId ? parseInt(newSettings.paratranzProjectId) : null, // Save project ID
            enable_paratranz: newSettings.enableParaTranz,
            auto_upload_paratranz: newSettings.autoUploadParaTranz, // Save new setting
            
            auto_shutdown: newSettings.autoShutdown,
            glossary: JSON.stringify(newSettings.glossary || {})
        };

        await api.post('/settings', payload);
        console.log("Settings saved to DB");
    } catch (err) {
        console.error("Failed to save settings to DB", err);
        alert(t('save_fail') || "Failed to save settings");
    }
  };

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
        alert(t('no_mods_found_desc'));
      }
    } catch (err) {
      console.error(t('scan_error'), err);
      alert(t('mod_scan_fail'));
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
    if (!confirm(t('confirm_translate').replace('{name}', mod.name).replace('{lang}', langName).replace('{service}', selectedService))) return;

    setLoading(true);
    setLastTranslation(null);
    
    // Request Wake Lock
    if ('wakeLock' in navigator) {
        try {
            const lock = await navigator.wakeLock.request('screen');
            setWakeLock(lock);
            console.log('Screen Wake Lock acquired');
        } catch (err) {
            console.error('Failed to acquire Wake Lock:', err);
        }
    }
    
    // Reset progress UI immediately
    setProgress({ percent: 0, currentFile: t('initializing'), status: 'running' });

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
            },
            glossary: settings.glossary || {},
            shutdown_when_complete: settings.autoShutdown, // Use DB setting
        };

        // Start background task
        const res = await api.post('/translate/run', payload);
        const taskId = res.data.task_id;
        
        console.log("Started translation task:", taskId);

        // Poll for completion
        const interval = setInterval(async () => {
            try {
                // Pass task_id in params
                const statusRes = await api.get('/translate/status', { params: { task_id: taskId } });
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
                    avg_speed: data.avg_speed || 0
                });

                if (data.status === 'completed') {
                    // Double check if all files are actually processed (prevent premature trigger)
                    // Ensure processed_files equals total_files AND total_files is > 0
                    if (data.total_files > 0 && data.processed_files < data.total_files) {
                        console.log(`Waiting for completion... ${data.processed_files}/${data.total_files}`);
                        return;
                    }

                    clearInterval(interval);
                    setLoading(false);
                    
                    // Release Wake Lock
                    if (wakeLock) {
                        wakeLock.release().then(() => setWakeLock(null));
                    }
                    
                    // Workflow Branch: Check for Auto Upload to ParaTranz
                    if (settings.enableParaTranz && settings.paratranzToken && settings.autoUploadParaTranz) {
                        const modWithTrans = { ...mod, translationPath: data.path };
                        // Automatically start upload without prompt
                        // We need project ID. If it's saved in settings backend-side, 
                        // executeUpload can handle it if we pass null/undefined, 
                        // BUT executeUpload expects a projectId or prompts selector.
                        
                        // Strategy: Call upload directly. If backend handles ID, we don't need selector.
                        // Ideally we should use the stored project ID from backend settings.
                        // We pass the ID explicitly just in case, though backend has fallback.
                        
                        const projectId = settings.paratranzProjectId ? parseInt(settings.paratranzProjectId) : null;
                        executeUpload(modWithTrans, projectId); 
                        // Note: If project ID is missing in backend settings, executeUpload will fail (alert user).
                        return;
                    }

                    // Default Flow: Generate Mod & Download (Only if NOT auto-uploading or upload finished?)
                    // If auto-upload triggers, we usually stop there?
                    // Or do we want both? User said "If failed, make mod".
                    // For now, if auto-upload is OFF, we do standard behavior.
                    
                    if (data.path) {
                         const zipRes = await api.post(`/translate/zip?path=${encodeURIComponent(data.path)}&name=${encodeURIComponent(data.zip_name)}`);
                         setLastTranslation({
                            modId: mod.id || mod.path,
                            zipPath: zipRes.data.zip_path,
                            path: data.path
                        });
                        alert(t('success_process').replace('{count}', data.processed_files) + '\n' + t('saved_at').replace('{path}', data.path) + '\n' + t('ready_download'));
                    } else {
                        alert(t('translation_complete'));
                    }
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    setLoading(false);
                    if (wakeLock) wakeLock.release(); // Release on error
                    alert(t('error_translation'));
                }
            } catch (e) {
                console.error("Polling error", e);
                // If 404, maybe task lost?
            }
        }, 1000);

    } catch (err) {
        console.error(err);
        alert(t('fail_start').replace('{msg}', err.response?.data?.detail || err.message));
        setLoading(false);
    }
  };

  const openProjectSelector = (mod, mode) => {
      if (!settings.paratranzToken) {
          alert(t('no_token'));
          setShowSettings(true);
          return;
      }
      setSelectedModForSync(mod);
      setProjectSelectorMode(mode);
      setShowProjectSelector(true);
  };

  const handleProjectSelect = async (projectId) => {
      setShowProjectSelector(false);
      const mod = selectedModForSync;
      
      if (!mod || !projectId) return;

      if (projectSelectorMode === 'upload') {
          await executeUpload(mod, projectId);
      } else if (projectSelectorMode === 'download') {
          await executeDownload(mod, projectId);
      }
  };

  const executeUpload = async (mod, projectId) => {
      if (!mod.path) {
          alert("Error: Mod path is missing.");
          return;
      }

      setLoading(true);
      try {
          const res = await api.post('/paratranz/upload', {
              project_id: projectId,
              mod_path: mod.path,
              translation_path: mod.translationPath || null // Pass translation path if available
          }, {
              headers: { Authorization: settings.paratranzToken }
          });
          
          if (res.data.errors && res.data.errors.length > 0) {
              // Convert errors to string if they are objects
              const errorStr = res.data.errors.map(e => typeof e === 'object' ? JSON.stringify(e) : e).join(', ');
              alert(t('upload_errors').replace('{count}', res.data.uploaded.length).replace('{errors}', errorStr));
              console.error(res.data.errors);
          } else {
              alert(t('upload_success').replace('{count}', res.data.uploaded.length));
          }
      } catch (err) {
          console.error(err);
          let errorDetail = err.message;
          if (err.response && err.response.data) {
              errorDetail = JSON.stringify(err.response.data, null, 2);
          }
          alert(t('upload_fail').replace('{msg}', errorDetail));
      } finally {
          setLoading(false);
      }
  };

  const executeDownload = async (mod, projectId) => {
        if (!config || !config.documents_path) {
            alert(t('config_not_loaded'));
            return;
        }
        
        const modId = mod.id || "local";
        const safeName = `paratranz_sync_${modId}_${Date.now()}`;
        const targetPath = `${config.documents_path}/${safeName}`;

        setLoading(true);
        try {
            const res = await api.post(`/paratranz/download/${projectId}?target_mod_path=${encodeURIComponent(targetPath)}`, {}, {
                headers: { Authorization: settings.paratranzToken }
            });
            
            alert(t('synced_success').replace('{count}', res.data.files_synced) + '\n' + t('synced_path').replace('{path}', targetPath) + '\n\n' + t('synced_note'));
        } catch (err) {
            console.error(err);
            let errorDetail = err.message;
            if (err.response && err.response.data) {
                errorDetail = JSON.stringify(err.response.data, null, 2);
            }
            alert(t('download_fail').replace('{msg}', errorDetail));
        } finally {
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
              {t('settings')}
            </button>
          </div>
        </div>

        {/* Search & View Toggle Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, maxWidth: '400px' }}>
            <Search size={18} color="var(--text-secondary)" />
            <input
              type="text"
              placeholder={t('search_placeholder')}
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
          <p style={{ marginTop: '1rem', fontSize: '1.2rem' }}>{t('processing')}</p>
          {progress.status === 'running' && (
            <div style={{ marginTop: '1.5rem', maxWidth: '500px', marginInline: 'auto' }}>
              {/* File Progress */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span>{t('files')}: {progress.processed_files || 0} / {progress.total_files || '?'}</span>
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
                  📄 {progress.currentFile || t('initializing')}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <div>
                        {t('entry')}: {progress.current_entry} / {progress.total_entries}
                    </div>
                    <div>
                        {t('speed')}: {progress.avg_speed ? progress.avg_speed.toFixed(1) : 0} entries/s
                    </div>
                </div>
                <p style={{ margin: 0, fontSize: '0.85rem', marginTop: '0.5rem', color: 'var(--accent)' }}>
                  {t('total_translated')}: {progress.entries_translated}
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
                  <button className="btn" style={{ width: '100%' }} onClick={() => translateMod(mod)}>
                    {t('translate')}
                  </button>
                  
                  {/* ParaTranz Action Buttons (Visible only if Enabled AND Token is set) */}
                  {settings.enableParaTranz && settings.paratranzToken && (
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                          <button 
                            className="btn" 
                            style={{ padding: '0.5rem', background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                            title="Upload to ParaTranz"
                            onClick={() => openProjectSelector(mod, 'upload')}
                          >
                              <CloudUpload size={18} />
                          </button>
                          <button 
                            className="btn" 
                            style={{ padding: '0.5rem', background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                            title="Download from ParaTranz"
                            onClick={() => openProjectSelector(mod, 'download')}
                          >
                              <Download size={18} />
                          </button>
                      </div>
                  )}

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
        onSave={handleSaveSettings}
      />

      {/* Project Selector Modal */}
      <ProjectSelectorModal
        isOpen={showProjectSelector}
        onClose={() => setShowProjectSelector(false)}
        token={settings.paratranzToken}
        onSelect={handleProjectSelect}
      />
    </div>
  );
}

export default App;
