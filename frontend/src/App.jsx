import { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('samvidhan_sessions');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse sessions", e);
      }
    }
    return [{
      id: 'default',
      title: 'New Chat',
      messages: [],
      selectedDomains: ['all'],
      deepThinkActive: true
    }];
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    const saved = localStorage.getItem('samvidhan_sessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.length > 0) return parsed[0].id;
      } catch (e) {}
    }
    return 'default';
  });

  const [query, setQuery] = useState('');
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState(null);
  const [modelProvider, setModelProvider] = useState('local');
  const [modelsStatus, setModelsStatus] = useState({
    local: { available: false, message: "Checking...", model: "" },
    groq: { available: false, message: "Checking...", model: "" }
  });
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState('dark'); // 'dark' or 'light'
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarStatsOpen, setSidebarStatsOpen] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(0);
  const [hasPreselected, setHasPreselected] = useState(false);
  const [focusDropdownOpen, setFocusDropdownOpen] = useState(false);
  const [focusDropdownBottomOpen, setFocusDropdownBottomOpen] = useState(false);
  
  const messagesEndRef = useRef(null);

  // Auto pre-select available model provider
  useEffect(() => {
    if (!hasPreselected) {
      if (modelsStatus.local.available) {
        setModelProvider('local');
        setHasPreselected(true);
      } else if (modelsStatus.groq.available) {
        setModelProvider('groq');
        setHasPreselected(true);
      }
    }
  }, [modelsStatus, hasPreselected]);

  // Sync sessions to localStorage
  useEffect(() => {
    localStorage.setItem('samvidhan_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Active session helper
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0] || {
    id: 'default',
    title: 'New Chat',
    messages: [],
    selectedDomains: ['all'],
    deepThinkActive: true
  };

  const messages = activeSession.messages;

  const setMessages = (updateFn) => {
    setSessions(prevSessions => {
      return prevSessions.map(s => {
        if (s.id === activeSessionId) {
          const updatedMessages = typeof updateFn === 'function' ? updateFn(s.messages) : updateFn;
          
          // Update title if it's the first user message
          let title = s.title;
          if (s.title === 'New Chat' && updatedMessages.length > 0) {
            const firstUserMsg = updatedMessages.find(m => m.role === 'user');
            if (firstUserMsg) {
              title = firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '');
            }
          }
          
          return {
            ...s,
            messages: updatedMessages,
            title
          };
        }
        return s;
      });
    });
  };

  // Selected domains state (with backward compatible migration from searchFocus)
  let selectedDomains = activeSession.selectedDomains;
  if (!selectedDomains) {
    const oldFocus = activeSession.searchFocus || 'both';
    selectedDomains = oldFocus === 'both' ? ['all'] : [oldFocus];
  }
  const setSelectedDomains = (val) => {
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, selectedDomains: val } : s));
  };

  const DOMAIN_OPTIONS = [
    { id: 'all', label: 'All' },
    { id: 'constitution', label: 'Constitution' },
    { id: 'ipc', label: 'IPC' },
    { id: 'crpc', label: 'CrPC' },
    { id: 'cpc', label: 'CPC' },
    { id: 'evidence', label: 'Evidence Act' },
    { id: 'marriage', label: 'Marriage & Divorce' },
    { id: 'others', label: 'Other Statutes' }
  ];

  const toggleDomain = (domainId) => {
    if (domainId === 'all') {
      setSelectedDomains(['all']);
      return;
    }
    
    let next = selectedDomains.filter(x => x !== 'all');
    if (next.includes(domainId)) {
      next = next.filter(x => x !== domainId);
    } else {
      next.push(domainId);
    }
    
    if (next.length === 0) {
      setSelectedDomains(['all']);
    } else {
      setSelectedDomains(next);
    }
  };

  const getSelectedLabel = () => {
    if (selectedDomains.includes('all')) return 'All Statutes';
    const selectedLabels = DOMAIN_OPTIONS
      .filter(opt => selectedDomains.includes(opt.id))
      .map(opt => opt.label);
    if (selectedLabels.length === 0) return 'None';
    if (selectedLabels.length <= 2) return selectedLabels.join(', ');
    return `${selectedLabels.slice(0, 2).join(', ')} (+${selectedLabels.length - 2})`;
  };

  const deepThinkActive = activeSession.deepThinkActive !== undefined ? activeSession.deepThinkActive : true;
  const setDeepThinkActive = (val) => {
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, deepThinkActive: val } : s));
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  // Scroll to bottom on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Initial loads & intervals
  useEffect(() => {
    fetchStatus();
    fetchModelsStatus();
    fetchHistory();
    const intervalStatus = setInterval(fetchStatus, 15000);
    const intervalModels = setInterval(fetchModelsStatus, 15000);
    const intervalHistory = setInterval(fetchHistory, 15000);
    return () => {
      clearInterval(intervalStatus);
      clearInterval(intervalModels);
      clearInterval(intervalHistory);
    };
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/status`);
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      setStatus({ status: 'offline' });
    }
  };

  const fetchModelsStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/models/status`);
      const data = await res.json();
      setModelsStatus(data);
    } catch (e) {
      setModelsStatus({
        local: { available: false, message: "Server offline", model: "" },
        groq: { available: false, message: "Server offline", model: "" }
      });
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/history`);
      const data = await res.json();
      setHistory(data);
    } catch (e) {
      console.error("Error fetching history:", e);
    }
  };

  const handleNewChat = () => {
    const newId = Date.now().toString();
    const newSession = {
      id: newId,
      title: 'New Chat',
      messages: [],
      selectedDomains: ['all'],
      deepThinkActive: true
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newId);
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    if (sessions.length <= 1) {
      setSessions([{
        id: 'default',
        title: 'New Chat',
        messages: [],
        selectedDomains: ['all'],
        deepThinkActive: true
      }]);
      setActiveSessionId('default');
      return;
    }
    
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      const remaining = sessions.filter(s => s.id !== sessionId);
      setActiveSessionId(remaining[0].id);
    }
  };

  const clearAllSessions = () => {
    if (!window.confirm("Are you sure you want to clear all chat sessions?")) return;
    setSessions([{
      id: 'default',
      title: 'New Chat',
      messages: [],
      selectedDomains: ['all'],
      deepThinkActive: true
    }]);
    setActiveSessionId('default');
  };

  const handleSend = async (customQuery) => {
    const activeQuery = customQuery || query;
    if (!activeQuery.trim()) return;
    
    const userMessage = { role: 'user', content: activeQuery };
    setMessages(prev => [...prev, userMessage]);
    if (!customQuery) setQuery('');
    setLoading(true);
    setThinkingStep(1);

    // Simulate thinking steps for the general loader status text
    const t1 = setTimeout(() => setThinkingStep(2), 800);
    const t2 = setTimeout(() => setThinkingStep(3), 1800);
    const t3 = setTimeout(() => setThinkingStep(4), 3000);

    const focusLabel = selectedDomains.join(', ').toUpperCase();

    try {
      let queryToSend = activeQuery;

      // Build chat_history list to send to the backend
      const apiChatHistory = messages
        .filter(msg => (msg.role === 'user' || msg.role === 'assistant') && !msg.error)
        .slice(-5)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      const res = await fetch(`${API_BASE_URL}/api/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: queryToSend,
          chat_history: apiChatHistory,
          model_provider: modelProvider,
          focus: selectedDomains,
          session_id: activeSessionId
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let buffer = '';
      let doneReading = false;
      
      // Initialize an empty message bubble for real-time streaming updates
      const initialBotMessage = {
        role: 'assistant',
        content: '',
        deepThink: deepThinkActive,
        selectedDomains: selectedDomains,
        thinkingSteps: [
          `[01/04] Query focus verified: ${focusLabel}`,
          `[02/04] Querying index records from vector store...`
        ],
        metadata: {
          latency: 0,
          documents: []
        }
      };
      
      setMessages(prev => [...prev, initialBotMessage]);

      let accumulatedContent = '';
      let documents = [];
      let latencyVal = 0;

      while (!doneReading) {
        const { value, done } = await reader.read();
        doneReading = done;
        if (value) {
          buffer += decoder.decode(value, { stream: !done });
          
          const parts = buffer.split('\n\n');
          buffer = parts.pop();
          
          for (const part of parts) {
            if (!part.trim()) continue;
            
            const eventMatch = part.match(/^event:\s*(.+)$/m);
            const dataMatch = part.match(/^data:\s*(.+)$/m);
            
            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1].trim();
              const eventDataRaw = dataMatch[1].trim();
              
              try {
                const eventData = JSON.parse(eventDataRaw);
                
                if (eventType === 'documents') {
                  documents = eventData;
                  setMessages(prev => {
                    const next = [...prev];
                    if (next.length > 0) {
                      const last = { ...next[next.length - 1] };
                      last.metadata = { ...last.metadata, documents };
                      last.thinkingSteps = [
                        `[01/04] Query focus verified: ${focusLabel}`,
                        `[02/04] Retrieved ${documents.length} index records from vector store`,
                        `[03/04] Reranking metadata matches...`
                      ];
                      next[next.length - 1] = last;
                    }
                    return next;
                  });
                } else if (eventType === 'token') {
                  accumulatedContent += eventData;
                  setMessages(prev => {
                    const next = [...prev];
                    if (next.length > 0) {
                      const last = { ...next[next.length - 1] };
                      last.content = accumulatedContent;
                      if (last.thinkingSteps.length < 4) {
                        last.thinkingSteps = [
                          `[01/04] Query focus verified: ${focusLabel}`,
                          `[02/04] Retrieved ${documents.length} index records from vector store`,
                          `[03/04] Reranking metadata matches complete`,
                          `[04/04] Synthesizing answer in real-time...`
                        ];
                      }
                      next[next.length - 1] = last;
                    }
                    return next;
                  });
                } else if (eventType === 'done') {
                  latencyVal = eventData.latency;
                  const modelUsedVal = eventData.model_used || '';
                  setMessages(prev => {
                    const next = [...prev];
                    if (next.length > 0) {
                      const last = { ...next[next.length - 1] };
                      last.metadata = { ...last.metadata, latency: latencyVal, model_used: modelUsedVal };
                      last.thinkingSteps = [
                        `[01/04] Query focus verified: ${focusLabel}`,
                        `[02/04] Retrieved ${documents.length} index records from vector store`,
                        `[03/04] Reranking metadata matches complete (latency: ${latencyVal}s)`,
                        `[04/04] Answer synthesis executed via ${modelUsedVal || status?.model_name || 'llama3.1:8b'}`
                      ];
                      next[next.length - 1] = last;
                    }
                    return next;
                  });
                } else if (eventType === 'error') {
                  setMessages(prev => {
                    const next = [...prev];
                    if (next.length > 0) {
                      const last = { ...next[next.length - 1] };
                      last.content = `Error: ${eventData.detail}`;
                      last.error = true;
                      next[next.length - 1] = last;
                    }
                    return next;
                  });
                }
              } catch (e) {
                console.error("Error parsing SSE data line", e);
              }
            }
          }
        }
      }
      
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      fetchHistory();
    } catch (error) {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'An error occurred while generating the response. Please ensure Ollama is serving locally.', 
        error: true 
      }]);
    } finally {
      setLoading(false);
      setThinkingStep(0);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Helper: compute latency metrics
  const getAverageLatency = () => {
    if (history.length === 0) return '0.00';
    const sum = history.reduce((acc, curr) => acc + (curr.latency || 0), 0);
    return (sum / history.length).toFixed(2);
  };

  // Helper: compute document match metrics
  const getAverageDocMatches = () => {
    if (history.length === 0) return 0;
    const sum = history.reduce((acc, curr) => acc + (curr.documents?.length || 0), 0);
    return (sum / history.length).toFixed(1);
  };

  const handleHistoryItemClick = (item) => {
    setSelectedRecord(item);
    setActiveHistoryId(item.id);
  };

  const suggestions = [
    {
      title: "Right to Equality",
      desc: "What are the provisions under Article 14 of the Indian Constitution?",
      query: "Explain my right to equality under Article 14."
    },
    {
      title: "Right to Education",
      desc: "How does Article 21A mandate free and compulsory education?",
      query: "What is the Right to Education under Article 21A?"
    },
    {
      title: "Police Arrest Power",
      desc: "What are the rules regarding arrest without a warrant?",
      query: "Under what conditions can a police officer arrest someone without a warrant?"
    },
    {
      title: "Theft Punishment",
      desc: "What IPC section covers punishment for simple theft?",
      query: "What is the punishment for theft under the Indian Penal Code?"
    }
  ];

  return (
    <div className={`app-wrapper ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`} data-theme={theme}>
      
      {/* Mobile Sidebar Overlay */}
      <div className="mobile-sidebar-overlay" onClick={() => setSidebarCollapsed(true)} />
      
      {/* SIDEBAR - Ingestion & Improvement Hub */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">⚖</div>
          <div className="brand-text">
            <h1>SAMVIDHAN AI</h1>
            <p>CONSTITUTION & IPC INDEX</p>
          </div>
        </div>

        {/* Statistics Toggle Button */}
        <button 
          className="btn-stats-toggle" 
          onClick={() => setSidebarStatsOpen(!sidebarStatsOpen)}
        >
          {sidebarStatsOpen ? '[- Statistics]' : '[+ Statistics]'}
        </button>

        {/* System & Vector DB Status */}
        {sidebarStatsOpen && (
          <div className="stats-panel">
            <div className="system-card">
              <div className="stat-row">
                <span className="stat-lbl">System Engine</span>
                <span className={`status-badge ${status?.status === 'online' ? 'online' : 'offline'}`}>
                  {status?.status === 'online' ? '[ONLINE]' : '[OFFLINE]'}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-lbl">LLM Engine</span>
                <span className="stat-val">{status?.model_name || 'llama3.1:8b'}</span>
              </div>
              <div className="stat-row">
                <span className="stat-lbl">Embedding</span>
                <span className="stat-val" style={{fontSize: '0.65rem', fontFamily: 'var(--font-mono)'}}>{status?.embedding_model || 'bge-small-en-v1.5'}</span>
              </div>
              <div className="stat-row" style={{borderTop: '1px solid hsl(var(--border))', paddingTop: '0.5rem', marginTop: '0.25rem'}}>
                <span className="stat-lbl">Avg Response</span>
                <span className="stat-val">{getAverageLatency()}s</span>
              </div>
              <div className="stat-row">
                <span className="stat-lbl">Avg Retrieve</span>
                <span className="stat-val">{getAverageDocMatches()} docs</span>
              </div>
            </div>
          </div>
        )}

        {/* Action Container for New Chat */}
        <div className="sidebar-action-container">
          <button className="btn-new-chat" onClick={handleNewChat}>
            [+] NEW CHAT
          </button>
        </div>

        {/* Session Vault */}
        <div className="history-section">
          <div className="history-header">
            <h2>Session Vault</h2>
            <button className="btn-clear" onClick={clearAllSessions} title="Clear all chat sessions">
              Clear All
            </button>
          </div>

          <div className="history-scroll">
            {sessions.map((s) => (
              <div 
                key={s.id} 
                className={`history-card session-vault-card ${activeSessionId === s.id ? 'active' : ''}`}
                onClick={() => setActiveSessionId(s.id)}
              >
                <div className="session-card-content">
                  <span className="session-icon">🔒</span>
                  <div className="history-q">{s.title}</div>
                </div>
                <button 
                  className="btn-delete-session" 
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  title="Delete session"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* MAIN PLAYGROUND */}
      <main className="main-area">
        
        {/* Header */}
        <header className="main-header">
          <div className="header-left">
            <button className="sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} title="Toggle Sidebar">
              [☰]
            </button>
            <div className="header-title-sec">
              <h1>CONSTITUTION & CRIMINAL LAW DIGEST</h1>
            </div>
          </div>

          <div className="header-controls">
            <button className="theme-toggle" onClick={toggleTheme}>
              {theme === 'dark' ? '[☀️] LIGHT MODE' : '[🌙] DARK MODE'}
            </button>
          </div>
        </header>

        {/* Chat / Playground Space */}
        <div className="chat-screen">
          {messages.length === 0 ? (
            <div className="playground-intro">
              <div className="intro-badge">[⚖]</div>
              <h2>
                SAMVIDHAN AI SEARCH <br/>
                <span className="intro-retro-text">Accurate, Referenced & Formal</span>
              </h2>
              <p>
                A minimal, high-precision semantic search index containing the full text of the Constitution of India and the Indian Penal Code (IPC).
              </p>

              {/* Central Search Container */}
              <div className="central-search-box">
                <div className="search-input-container">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={loading ? "Generating response..." : "Enter query (e.g. 'Article 21 parameters', 'Theft punishment', 'Arrest warrant rule')..."}
                    disabled={loading}
                    rows="2"
                  />
                  <div className="search-controls-footer">
                    <div className="footer-left-pills">
                      <button 
                        className={`pill-btn ${deepThinkActive ? 'active' : ''}`}
                        onClick={() => setDeepThinkActive(!deepThinkActive)}
                        title="Toggle DeepThink"
                      >
                        <span className="mono-bracket">{deepThinkActive ? '[x]' : '[ ]'}</span> DeepThink
                      </button>
                      <div className="focus-selector">
                        <span className="focus-label">/focus:</span>
                        <div className="custom-dropdown-container">
                          <button 
                            className="focus-select dropdown-trigger" 
                            onClick={() => setFocusDropdownOpen(!focusDropdownOpen)}
                            type="button"
                          >
                            <span>{getSelectedLabel()}</span>
                            <span className="dropdown-arrow">▼</span>
                          </button>
                          {focusDropdownOpen && (
                            <>
                              <div className="dropdown-backdrop" onClick={() => setFocusDropdownOpen(false)} />
                              <div className="dropdown-menu open-down">
                                {DOMAIN_OPTIONS.map(opt => {
                                  const isActive = selectedDomains.includes(opt.id);
                                  return (
                                    <div 
                                      key={opt.id} 
                                      className={`dropdown-item ${isActive ? 'active' : ''}`}
                                      onClick={() => toggleDomain(opt.id)}
                                    >
                                      <span className="item-checkbox">{isActive ? '[x]' : '[ ]'}</span>
                                      <span className="item-label">{opt.label}</span>
                                    </div>
                                  );
                                })}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="focus-selector">
                        <span className="focus-label">/engine:</span>
                        <select 
                          value={modelProvider} 
                          onChange={(e) => setModelProvider(e.target.value)}
                          className="focus-select"
                        >
                          <option value="local">Local {modelsStatus?.local?.available ? "(Available)" : "(Not Available)"}</option>
                          <option value="groq">Groq Cloud {modelsStatus?.groq?.available ? "(Available)" : "(Not Available)"}</option>
                        </select>
                      </div>
                    </div>
                    <button 
                      className="btn-send-main" 
                      onClick={() => handleSend()} 
                      disabled={loading || !query.trim()}
                      title="Send query"
                    >
                      [→]
                    </button>
                  </div>
                </div>
              </div>

              {/* Suggestions Grid */}
              <div className="suggestions-grid">
                {suggestions.map((sug, i) => (
                  <div 
                    key={i} 
                    className={`suggestion-card ${loading ? 'disabled' : ''}`}
                    onClick={() => !loading && handleSend(sug.query)}
                  >
                    <div className="sug-header">
                      <span className="sug-index">0{i+1}.</span>
                      <h3>{sug.title}</h3>
                    </div>
                    <p>{sug.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="chat-thread-container">
              {messages.map((msg, idx) => (
                <div key={idx} className={`chat-bubble-wrapper ${msg.role}`}>
                  <div className={`chat-bubble ${msg.role} ${msg.error ? 'error' : ''}`}>
                    
                    {/* User message */}
                    {msg.role === 'user' && msg.content}

                    {/* Assistant message */}
                    {msg.role === 'assistant' && (
                      <div className="assistant-response-container">
                        
                        {/* DeepThink Process Accordion */}
                        {msg.deepThink && msg.thinkingSteps && (
                          <div className="thought-process-container">
                            <details className="thought-process-accordion" open>
                              <summary className="thought-summary">
                                [Thought Process - {msg.metadata?.latency || '0.5'}s]
                              </summary>
                              <div className="thought-content">
                                <ul className="thought-steps-list">
                                  {msg.thinkingSteps.map((step, sIdx) => (
                                    <li key={sIdx} className="thought-step">
                                      {step}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </details>
                          </div>
                        )}

                        {/* Sources Grid */}
                        {!msg.error && msg.metadata?.documents?.length > 0 && (
                          <div className="sources-container">
                            <div className="sources-header">
                              [Retrieved Legal Sources - {msg.metadata.documents.length}]
                            </div>
                            <div className="sources-grid">
                              {msg.metadata.documents.map((doc, i) => {
                                const isIPC = doc.metadata.type === 'ipc_section';
                                const refNo = doc.metadata.article_no || doc.metadata.section_no || 'N/A';
                                const part = doc.metadata.part || 'IPC';
                                return (
                                  <div 
                                    key={i} 
                                    className="source-card"
                                    onClick={() => setSelectedRecord({
                                      query: msg.content,
                                      latency: msg.metadata.latency,
                                      model_used: msg.metadata.model_used,
                                      documents: msg.metadata.documents
                                    })}
                                    title="Click to inspect source"
                                  >
                                    <div className="source-card-badge">
                                      <span className="source-type">{isIPC ? 'IPC' : 'Art'}</span>
                                      <span className="source-no">{refNo}</span>
                                    </div>
                                    <div className="source-card-part">{part}</div>
                                    <div className="source-card-snippet">{doc.content}</div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Answer Text */}
                        <div className="answer-text-content">
                          {msg.content}
                        </div>

                        {/* Actions */}
                        {!msg.error && (
                          <div className="assistant-action-bar">
                            <button className="btn-action" onClick={() => navigator.clipboard.writeText(msg.content)} title="Copy Response">
                              [Copy]
                            </button>
                             <button className="btn-action" onClick={() => setSelectedRecord({
                              query: msg.content,
                              latency: msg.metadata.latency,
                              model_used: msg.metadata.model_used,
                              documents: msg.metadata.documents
                            })} title="Inspect citations">
                              [Inspect]
                            </button>
                          </div>
                        )}

                      </div>
                    )}
                  </div>
                  
                  <div className={`chat-meta-tag ${msg.role}`}>
                    {msg.role === 'user' ? 'CITIZEN' : `INDEX CONSULTANT (${msg.metadata?.model_used || 'Local Engine'})`}
                    {msg.metadata?.latency && ` | LATENCY: ${msg.metadata.latency}s`}
                  </div>
                </div>
              ))}

              {/* Dynamic thinking indicator */}
              {loading && (
                <div className="agent-thinking">
                  <div className="thinking-bubble">
                    <span className="thinking-text">
                      {thinkingStep === 1 && "[STATUS] Analyzing query parameters..."}
                      {thinkingStep === 2 && "[STATUS] Executing vector database search..."}
                      {thinkingStep === 3 && "[STATUS] Reranking matching context..."}
                      {thinkingStep === 4 && "[STATUS] Executing inference..."}
                      {thinkingStep === 0 && "[STATUS] Ingesting context..."}
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        {messages.length > 0 && (
          <div className="chat-input-bar">
            <div className="input-glow-wrapper-bottom">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask follow-up query..."
                disabled={loading}
                rows="1"
              />
              <div className="bottom-input-actions">
                <button 
                  className={`pill-btn-bottom ${deepThinkActive ? 'active' : ''}`}
                  onClick={() => setDeepThinkActive(!deepThinkActive)}
                  title="Toggle DeepThink"
                >
                  {deepThinkActive ? '[x] Think' : '[ ] Think'}
                </button>
                <div className="focus-selector" style={{marginRight: '8px'}}>
                  <span className="focus-label">/focus:</span>
                  <div className="custom-dropdown-container">
                    <button 
                      className="focus-select dropdown-trigger" 
                      onClick={() => setFocusDropdownBottomOpen(!focusDropdownBottomOpen)}
                      type="button"
                    >
                      <span>{getSelectedLabel()}</span>
                      <span className="dropdown-arrow">▼</span>
                    </button>
                    {focusDropdownBottomOpen && (
                      <>
                        <div className="dropdown-backdrop" onClick={() => setFocusDropdownBottomOpen(false)} />
                        <div className="dropdown-menu open-up">
                          {DOMAIN_OPTIONS.map(opt => {
                            const isActive = selectedDomains.includes(opt.id);
                            return (
                              <div 
                                key={opt.id} 
                                className={`dropdown-item ${isActive ? 'active' : ''}`}
                                onClick={() => toggleDomain(opt.id)}
                              >
                                <span className="item-checkbox">{isActive ? '[x]' : '[ ]'}</span>
                                <span className="item-label">{opt.label}</span>
                              </div>
                            );
                          })}
                        </div>
                      </>
                    )}
                  </div>
                </div>
                <select 
                  value={modelProvider} 
                  onChange={(e) => setModelProvider(e.target.value)}
                  className="focus-select-bottom"
                >
                  <option value="local">Local {modelsStatus?.local?.available ? "(Available)" : "(Not Available)"}</option>
                  <option value="groq">Groq Cloud {modelsStatus?.groq?.available ? "(Available)" : "(Not Available)"}</option>
                </select>
                <button 
                  className="btn-send-bottom" 
                  onClick={() => handleSend()} 
                  disabled={loading || !query.trim()}
                  title="Send follow-up"
                >
                  [→]
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* RAG INSPECTOR SLIDE-OUT DRAWER */}
      {selectedRecord && (
        <div className="inspector-overlay" onClick={() => setSelectedRecord(null)}>
          <div className="inspector-drawer" onClick={e => e.stopPropagation()}>
            <div className="inspector-header">
              <div className="inspector-title">
                <h2>RAG Citation Inspector</h2>
                <p>Detailed breakdown of vector query search & references</p>
              </div>
              <button className="btn-close-drawer" onClick={() => setSelectedRecord(null)}>✕</button>
            </div>
            
            <div className="inspector-body">
              <div className="drawer-stats">
                <div className="d-stat-card">
                  <h4>RAG Engine</h4>
                  <p>{selectedRecord.model_used || status?.model_name || 'llama3.1:8b'}</p>
                </div>
                <div className="d-stat-card">
                  <h4>Latency</h4>
                  <p>{selectedRecord.latency || '0.0'}s</p>
                </div>
                <div className="d-stat-card">
                  <h4>References</h4>
                  <p>{selectedRecord.documents?.length || 0} matches</p>
                </div>
              </div>

              <h3 className="doc-section-title">Source Material Context</h3>
              
              {selectedRecord.documents && selectedRecord.documents.length > 0 ? (
                selectedRecord.documents.map((doc, idx) => {
                  const isIPC = doc.metadata.type === 'ipc_section';
                  const label = isIPC ? 'IPC Section' : 'Constitution Article';
                  const refNo = doc.metadata.article_no || doc.metadata.section_no || 'N/A';
                  
                  return (
                    <div key={idx} className="doc-card">
                      <div className="doc-card-header">
                        <span className={`doc-badge ${isIPC ? 'ipc' : ''}`}>
                          {label} {refNo}
                        </span>
                        {doc.metadata.chapter && (
                          <span className="doc-chapter">
                            Chapter {doc.metadata.chapter}
                          </span>
                        )}
                      </div>
                      <div className="doc-content">{doc.content}</div>
                    </div>
                  );
                })
              ) : (
                <div className="history-empty" style={{marginTop: '2rem'}}>
                  <p>No document source context available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
