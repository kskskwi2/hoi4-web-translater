import { useState, useEffect } from 'react';
import { X, Search, RefreshCw, Folder, Plus, ArrowLeft, Send } from 'lucide-react';
import api from '../lib/api';
import { useLanguage } from '../contexts/LanguageContext';

export function ProjectSelectorModal({ isOpen, onClose, onSelect, token }) {
    const { t } = useLanguage();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');
    const [mode, setMode] = useState('list'); // 'list', 'create', 'manual'
    
    // Create Form State
    const [newProjectName, setNewProjectName] = useState('');
    const [newSourceLang, setNewSourceLang] = useState('en');
    const [newTargetLang, setNewTargetLang] = useState('ko');

    // Manual ID State
    const [manualId, setManualId] = useState('');

    useEffect(() => {
        if (isOpen && token) {
            fetchProjects();
            setMode('list');
            setNewProjectName('');
            setManualId('');
        }
    }, [isOpen, token]);

    const fetchProjects = async () => {
        setLoading(true);
        try {
            const res = await api.get('/paratranz/projects', {
                headers: { Authorization: token }
            });
            // Sort by ID descending (Newest first)
            const sorted = (res.data || []).sort((a, b) => b.id - a.id);
            setProjects(sorted);
        } catch (err) {
            console.error(err);
            // Don't alert here, just show empty state
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProject = async () => {
        if (!newProjectName) {
            alert("Please enter a project name.");
            return;
        }
        
        setLoading(true);
        try {
            const res = await api.post('/paratranz/projects', {
                name: newProjectName,
                source_lang: newSourceLang,
                target_lang: newTargetLang,
                description: "Created by Paradox Localisation Manager"
            }, {
                headers: { Authorization: token }
            });
            
            const newProject = res.data;
            alert(`Project "${newProject.name}" created!`);
            onSelect(newProject.id); 
            
        } catch (err) {
            console.error(err);
            alert("Failed to create project: " + (err.response?.data?.detail || err.message));
            setLoading(false);
        }
    };

    const handleManualSubmit = () => {
        const id = parseInt(manualId, 10);
        if (isNaN(id) || id <= 0) {
            alert("Please enter a valid numeric Project ID.");
            return;
        }
        onSelect(id);
    };

    const filteredProjects = projects.filter(p => 
        p.name.toLowerCase().includes(search.toLowerCase()) || 
        p.id.toString().includes(search)
    );

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
            zIndex: 1100
        }}>
            <div style={{
                background: 'var(--bg-primary)',
                borderRadius: '1rem',
                width: '500px',
                maxHeight: '80vh',
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid var(--border)',
                overflow: 'hidden'
            }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {mode !== 'list' && (
                            <button onClick={() => setMode('list')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                                <ArrowLeft size={20} />
                            </button>
                        )}
                        <h3 style={{ margin: 0 }}>
                            {mode === 'create' ? "Create New Project" : mode === 'manual' ? "Enter ID Directly" : t('select_project')}
                        </h3>
                    </div>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}>
                        <X size={20} />
                    </button>
                </div>

                {mode === 'list' ? (
                    <>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <div style={{ flex: 1, display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'var(--bg-primary)', padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
                                    <Search size={18} color="var(--text-secondary)" />
                                    <input 
                                        type="text" 
                                        placeholder={t('search_placeholder')} 
                                        value={search}
                                        onChange={(e) => setSearch(e.target.value)}
                                        style={{ border: 'none', background: 'transparent', width: '100%', color: 'var(--text-primary)', outline: 'none' }}
                                    />
                                </div>
                                <button 
                                    onClick={() => setMode('create')}
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
                                    <Plus size={18} />
                                    New
                                </button>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <button 
                                    onClick={() => setMode('manual')}
                                    style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer', textDecoration: 'underline' }}
                                >
                                    Can't find project? Enter ID directly
                                </button>
                            </div>
                        </div>

                        <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                            {loading ? (
                                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                    <RefreshCw className="spin" size={24} />
                                </div>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    {filteredProjects.map(p => (
                                        <button
                                            key={p.id}
                                            onClick={() => onSelect(p.id)}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '1rem',
                                                padding: '1rem',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '0.5rem',
                                                cursor: 'pointer',
                                                textAlign: 'left',
                                                color: 'var(--text-primary)',
                                                transition: 'background 0.2s'
                                            }}
                                            onMouseOver={(e) => e.currentTarget.style.background = 'var(--border)'}
                                            onMouseOut={(e) => e.currentTarget.style.background = 'var(--bg-secondary)'}
                                        >
                                            <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '0.75rem', borderRadius: '0.5rem', color: '#60a5fa' }}>
                                                <Folder size={24} />
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>{p.name}</div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                                                    ID: {p.id} • {p.public ? 'Public' : 'Private'}
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                    {filteredProjects.length === 0 && (
                                        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                            {t('no_projects')}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                ) : mode === 'create' ? (
                    // CREATE MODE
                    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Project Name</label>
                            <input 
                                type="text"
                                value={newProjectName}
                                onChange={(e) => setNewProjectName(e.target.value)}
                                placeholder="My Translation Project"
                                style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                            />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Source</label>
                                <select 
                                    value={newSourceLang}
                                    onChange={(e) => setNewSourceLang(e.target.value)}
                                    style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                                >
                                    <option value="en">English</option>
                                    <option value="ko">Korean</option>
                                    <option value="ja">Japanese</option>
                                    <option value="zh">Chinese</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Target</label>
                                <select 
                                    value={newTargetLang}
                                    onChange={(e) => setNewTargetLang(e.target.value)}
                                    style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                                >
                                    <option value="ko">Korean</option>
                                    <option value="en">English</option>
                                    <option value="ja">Japanese</option>
                                    <option value="zh">Chinese</option>
                                    <option value="ru">Russian</option>
                                    <option value="de">German</option>
                                    <option value="fr">French</option>
                                </select>
                            </div>
                        </div>
                        <div style={{ marginTop: '1rem' }}>
                            <button 
                                onClick={handleCreateProject}
                                disabled={loading}
                                className="btn"
                                style={{ width: '100%', background: 'var(--accent)', justifyContent: 'center' }}
                            >
                                {loading ? <RefreshCw className="spin" size={18} /> : 'Create & Select'}
                            </button>
                        </div>
                    </div>
                ) : (
                    // MANUAL ID MODE
                    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                            Enter the numeric Project ID directly from the ParaTranz URL (e.g. paratranz.cn/projects/<b>1234</b>).
                        </p>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Project ID</label>
                            <input 
                                type="number"
                                value={manualId}
                                onChange={(e) => setManualId(e.target.value)}
                                placeholder="1234"
                                style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                            />
                        </div>
                        <div style={{ marginTop: '1rem' }}>
                            <button 
                                onClick={handleManualSubmit}
                                className="btn"
                                style={{ width: '100%', background: 'var(--accent)', justifyContent: 'center', display: 'flex', gap: '0.5rem' }}
                            >
                                <Send size={18} />
                                Select ID
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
