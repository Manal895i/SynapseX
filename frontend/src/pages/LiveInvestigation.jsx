import { useState, useEffect, useRef } from 'react'
import {
  Radio, Play, Pause, RotateCcw, Zap,
  Activity, Shield, Video, Lock, Monitor,
  Usb, FileSearch, Network, Brain, Cpu,
  CheckCircle2, Clock, AlertTriangle, Eye,
  Filter, Search, Terminal, ArrowRight,
  Sparkles, Layers, Info, RefreshCw,
  ChevronRight, ChevronDown, Check,
  Volume2, VolumeX, ShieldAlert, Bot
} from 'lucide-react'
import './LiveInvestigation.css'

/* ═══════════════════════════════════════════════════
   PRE-DEFINED & DYNAMIC EVENTS STREAM
═══════════════════════════════════════════════════ */
const INITIAL_EVENTS = [
  {
    id: 'evt-101',
    time: '10:02:14',
    source: 'CCTV Agent',
    sourceCategory: 'cctv',
    icon: Video,
    label: 'CCTV Agent detected person entering restricted area',
    detail: 'Camera CAM-07 Server Room B corridor. Facial match unverified; subject badge scan mismatch.',
    severity: 'suspicious',
    correlated: true,
    correlationIndex: 1,
    confidence: '84%',
    payload: { cam: 'CAM-07', zone: 'Server Room B', motionScore: 0.94 }
  },
  {
    id: 'evt-102',
    time: '10:03:02',
    source: 'Access Log',
    sourceCategory: 'access',
    icon: Lock,
    label: 'Access Log received — Door opened (Tailgating anomaly)',
    detail: 'Physical Access Door DR-B02 unlocked via badge EMP-4421 within 48s of motion sensor trigger.',
    severity: 'suspicious',
    correlated: true,
    correlationIndex: 2,
    confidence: '91%',
    payload: { door: 'DR-B02', badge: 'EMP-4421', authType: 'RFID_PROX' }
  },
  {
    id: 'evt-103',
    time: '10:04:10',
    source: 'Endpoint Agent',
    sourceCategory: 'system',
    icon: Monitor,
    label: 'User login detected on LAPTOP-07 (jsmith@corp.int)',
    detail: 'Interactive logon Session 2 on terminal WKST-041 / LAPTOP-07. Kerberos ticket issued.',
    severity: 'normal',
    correlated: true,
    correlationIndex: 3,
    confidence: '99%',
    payload: { host: 'LAPTOP-07', user: 'jsmith@corp.int', logonType: 2 }
  },
  {
    id: 'evt-104',
    time: '10:05:32',
    source: 'USB Agent',
    sourceCategory: 'usb',
    icon: Usb,
    label: 'USB device connected (SanDisk 128GB unverified)',
    detail: 'Hardware ID: USBSTOR\\DiskSanDisk_Cruzer_Glide_SDCZ48-128G. Device unregistered in corporate asset database.',
    severity: 'critical',
    correlated: true,
    correlationIndex: 4,
    confidence: '96%',
    payload: { serial: 'SDCZ48-128G-84912', driveLetter: 'E:\\', capacity: '128 GB' }
  },
  {
    id: 'evt-105',
    time: '10:07:45',
    source: 'File Audit',
    sourceCategory: 'file',
    icon: FileSearch,
    label: 'Sensitive file accessed: /Finance/Q2-Projections/ confidential data',
    detail: '34 items (2.1 GB) copied from secure CIFS volume \\\\fs-core\\Finance\\Q2-Projections to staging directory E:\\tmp.',
    severity: 'critical',
    correlated: true,
    correlationIndex: 5,
    confidence: '88%',
    payload: { path: '\\\\fs-core\\Finance\\Q2-Projections\\*', files: 34, size: '2.1 GB' }
  },
  {
    id: 'evt-106',
    time: '10:09:20',
    source: 'Network Agent',
    sourceCategory: 'network',
    icon: Network,
    label: 'Large outbound network transfer detected (1.8 GB via TOR node)',
    detail: 'Encrypted outbound stream to 185.220.101.47:443 (TOR Exit Consensus). High entropy burst, 18 MB/s.',
    severity: 'critical',
    correlated: true,
    correlationIndex: 6,
    confidence: '95%',
    payload: { destIp: '185.220.101.47', port: 443, proto: 'TLSv1.3', transferred: '1.8 GB' }
  }
]

const STREAMING_POOL = [
  {
    timeOffset: 8,
    source: 'Network Agent',
    sourceCategory: 'network',
    icon: Network,
    label: 'DNS tunneling probe detected on subsidiary gateway',
    detail: 'High frequency encoded TXT record queries resolved against NS1.DARKNET-RESOLVER.CC.',
    severity: 'suspicious',
    correlated: false,
    confidence: '73%',
    payload: { query: 'x8f3.exfil.darknet-resolver.cc', count: 142 }
  },
  {
    timeOffset: 16,
    source: 'Endpoint Agent',
    sourceCategory: 'system',
    icon: Monitor,
    label: 'PowerShell execution with EncodedCommand parameter',
    detail: 'PID 4812 executed: powershell.exe -ExecutionPolicy Bypass -NoProfile -enc SQBFAFgA...',
    severity: 'critical',
    correlated: false,
    confidence: '92%',
    payload: { pid: 4812, parent: 'cmd.exe', user: 'SYSTEM' }
  },
  {
    timeOffset: 24,
    source: 'CCTV Agent',
    sourceCategory: 'cctv',
    icon: Video,
    label: 'CCTV CAM-03: Subject exit observed via Stairwell North',
    detail: 'Subject matching Server Room B visitor exited via fire door at North perimeter.',
    severity: 'suspicious',
    correlated: false,
    confidence: '81%',
    payload: { cam: 'CAM-03', direction: 'outbound', time: '10:14:02' }
  },
  {
    timeOffset: 32,
    source: 'Correlation Agent',
    sourceCategory: 'correlation',
    icon: Brain,
    label: 'Sequence alignment verified across 6 forensic telemetry channels',
    detail: 'Temporal clustering within 7m 06s window confirms single continuous operator hypothesis.',
    severity: 'normal',
    correlated: false,
    confidence: '89%',
    payload: { correlationScore: 0.89, windowSec: 426 }
  }
]

const INITIAL_AGENTS = [
  {
    id: 'evidence',
    name: 'Evidence Agent',
    status: 'Analyzing',
    statusType: 'analyzing',
    task: 'Ingesting CIFS file audit logs & USB hardware signatures',
    telemetry: '2.4 MB/s · 1,248 items cached',
    load: 74,
    color: 'blue'
  },
  {
    id: 'timeline',
    name: 'Timeline Agent',
    status: 'Processing',
    statusType: 'processing',
    task: 'Synchronizing NTP clock skew across 4 log origins',
    telemetry: 'Offset corrected: -14ms',
    load: 62,
    color: 'cyan'
  },
  {
    id: 'network',
    name: 'Network Agent',
    status: 'Active',
    statusType: 'active',
    task: 'Deep packet inspection on TOR exit stream 185.220.101.47',
    telemetry: 'PCAP stream 4.8 GB · 14.2k pkts/s',
    load: 88,
    color: 'green'
  },
  {
    id: 'cctv',
    name: 'CCTV Agent',
    status: 'Active',
    statusType: 'active',
    task: 'Continuous computer vision OCR & badge recognition on CAM-07',
    telemetry: '30 FPS · Latency 42ms',
    load: 81,
    color: 'green'
  },
  {
    id: 'correlation',
    name: 'Correlation Agent',
    status: 'Running',
    statusType: 'running',
    task: 'Multi-modal graph correlation (Physical + Digital vectors)',
    telemetry: 'Hypothesis matrix: 3 active clusters',
    load: 92,
    color: 'purple'
  },
  {
    id: 'reasoning',
    name: 'Reasoning Agent',
    status: 'Waiting',
    statusType: 'waiting',
    task: 'Synthesizing investigative narrative for human investigator review',
    telemetry: 'Prompt buffer ready · 0 tokens/s',
    load: 15,
    color: 'gray'
  }
]

export default function LiveInvestigation() {
  const [events, setEvents] = useState(INITIAL_EVENTS)
  const [isPlaying, setIsPlaying] = useState(true)
  const [playbackSpeed, setPlaybackSpeed] = useState(1) // 1x, 2x, 5x
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [agents, setAgents] = useState(INITIAL_AGENTS)
  const [activeTabCenter, setActiveTabCenter] = useState('timeline') // timeline | graph
  const [audioMuted, setAudioMuted] = useState(true)
  const [liveClock, setLiveClock] = useState(new Date())
  const [streamRate, setStreamRate] = useState(48.2)
  const [newEventFlash, setNewEventFlash] = useState(null)

  const streamEndRef = useRef(null)
  const poolIndexRef = useRef(0)

  // Clock ticker
  useEffect(() => {
    const timer = setInterval(() => setLiveClock(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Simulated live event ingestion
  useEffect(() => {
    if (!isPlaying) return

    const intervalTime = Math.max(3500 / playbackSpeed, 800)
    const interval = setInterval(() => {
      // Pick next event from streaming pool or generate synthetic event
      const template = STREAMING_POOL[poolIndexRef.current % STREAMING_POOL.length]
      poolIndexRef.current += 1

      const now = new Date()
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

      const newEvt = {
        id: `evt-${Date.now().toString().slice(-4)}`,
        time: timeStr,
        source: template.source,
        sourceCategory: template.sourceCategory,
        icon: template.icon,
        label: template.label,
        detail: template.detail,
        severity: template.severity,
        correlated: template.correlated,
        correlationIndex: null,
        confidence: template.confidence,
        payload: template.payload
      }

      setEvents(prev => [...prev, newEvt])
      setNewEventFlash(newEvt.id)
      setStreamRate(r => +(40 + Math.random() * 20).toFixed(1))

      // Periodically update agent load metrics
      setAgents(prev => prev.map(a => {
        if (a.statusType === 'waiting') return a
        const delta = Math.floor((Math.random() - 0.5) * 8)
        const newLoad = Math.min(Math.max(a.load + delta, 30), 99)
        return { ...a, load: newLoad }
      }))
    }, intervalTime)

    return () => clearInterval(interval)
  }, [isPlaying, playbackSpeed])

  // Clear flash
  useEffect(() => {
    if (!newEventFlash) return
    const timer = setTimeout(() => setNewEventFlash(null), 1500)
    return () => clearInterval(timer)
  }, [newEventFlash])

  // Filtered events
  const filteredEvents = events.filter(e => {
    if (filterSeverity !== 'all' && e.severity !== filterSeverity) return false
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase()
      return (
        e.label.toLowerCase().includes(q) ||
        e.source.toLowerCase().includes(q) ||
        e.detail.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Correlated events count
  const correlatedCount = events.filter(e => e.correlated).length

  // Restart Stream
  const handleReset = () => {
    setEvents(INITIAL_EVENTS)
    poolIndexRef.current = 0
    setSelectedEvent(null)
  }

  // Trigger manual event
  const handleInjectAnomaly = () => {
    const now = new Date()
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    const anomaly = {
      id: `evt-manual-${Date.now().toString().slice(-4)}`,
      time: timeStr,
      source: 'Threat Intel Feed',
      sourceCategory: 'network',
      icon: ShieldAlert,
      label: 'C2 Beaconing detected matching LockBit / CobaltStrike profile',
      detail: 'Periodic heartbeat packet pattern (jitter 8%) transmitted over DNS/HTTPS to bulletproof hosting block.',
      severity: 'critical',
      correlated: true,
      correlationIndex: events.filter(e => e.correlated).length + 1,
      confidence: '97%',
      payload: { beaconInterval: '45s', jitter: '8%', profile: 'CobaltStrike v4.8' }
    }
    setEvents(prev => [...prev, anomaly])
    setNewEventFlash(anomaly.id)
  }

  return (
    <div className="live-inv-root">

      {/* ══════════════════════════════════════════
          TOP COMMAND HEADER
      ══════════════════════════════════════════ */}
      <header className="live-header">
        <div className="live-header-top">
          
          {/* Case Identity & Live Indicator */}
          <div className="live-case-badge-wrap">
            <div className="live-pulse-badge">
              <span className="live-red-dot" />
              <span className="live-badge-text">LIVE CASE</span>
            </div>
            <div className="live-case-id-chip">
              <span className="case-num">CASE-2026-001</span>
              <span className="case-title-mini">Suspected Data Exfiltration</span>
            </div>
            <span className="live-tlp-tag">TLP:RED</span>
            <span className="live-class-tag">CONFIDENTIAL // LAW ENFORCEMENT ADVISORY</span>
          </div>

          {/* Center: Live Engine Status */}
          <div className="live-engine-status">
            <div className="engine-status-pill">
              <span className="engine-dot pulse" />
              <span className="engine-label">AI Monitoring Active</span>
            </div>
            <div className="engine-telemetry">
              <span className="telem-item"><Activity size={12} className="telem-icon" /> Rate: <strong>{streamRate} ev/s</strong></span>
              <span className="telem-sep">|</span>
              <span className="telem-item"><Zap size={12} className="telem-icon" /> Latency: <strong>14ms</strong></span>
              <span className="telem-sep">|</span>
              <span className="telem-item"><Clock size={12} className="telem-icon" /> {liveClock.toTimeString().split(' ')[0]} UTC</span>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="live-controls">
            <button 
              className={`ctrl-btn ${isPlaying ? 'ctrl-btn--playing' : 'ctrl-btn--paused'}`}
              onClick={() => setIsPlaying(!isPlaying)}
              title={isPlaying ? 'Pause live ingestion' : 'Resume live ingestion'}
              id="live-play-pause-btn"
            >
              {isPlaying ? <><Pause size={14} /> Pause Stream</> : <><Play size={14} /> Resume Stream</>}
            </button>

            <div className="speed-selector">
              {[1, 2, 5].map(s => (
                <button
                  key={s}
                  className={`speed-chip ${playbackSpeed === s ? 'speed-chip--active' : ''}`}
                  onClick={() => setPlaybackSpeed(s)}
                >
                  {s}x
                </button>
              ))}
            </div>

            <button 
              className="ctrl-btn-ghost" 
              onClick={handleInjectAnomaly}
              title="Simulate incoming threat detection event"
              id="live-inject-btn"
            >
              <Zap size={13} /> Inject Anomaly
            </button>

            <button 
              className="ctrl-btn-ghost" 
              onClick={handleReset}
              title="Reset stream to initial state"
            >
              <RotateCcw size={13} />
            </button>

            <button 
              className="ctrl-btn-icon"
              onClick={() => setAudioMuted(!audioMuted)}
              title={audioMuted ? 'Unmute alerts' : 'Mute alerts'}
            >
              {audioMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>
          </div>
        </div>
      </header>

      {/* ══════════════════════════════════════════
          MAIN THREE-COLUMN LAYOUT
      ══════════════════════════════════════════ */}
      <div className="live-grid-three">

        {/* ───────────────────────────────────────
            LEFT COLUMN: Live Event Stream
        ─────────────────────────────────────── */}
        <section className="live-col live-col--stream">
          <div className="col-header">
            <div className="col-title-wrap">
              <div className="col-title-icon-box"><Radio size={14} className="spin-slow" /></div>
              <div>
                <h2 className="col-title">Live Event Stream</h2>
                <span className="col-subtitle">{filteredEvents.length} events logged · Ingestion active</span>
              </div>
            </div>
            <span className="live-counter-pill">{events.length} Total</span>
          </div>

          {/* Search & Severity Filter Tabs */}
          <div className="stream-filter-bar">
            <div className="stream-search-wrap">
              <Search size={12} className="stream-search-icon" />
              <input 
                type="text" 
                placeholder="Filter event feed..." 
                className="stream-search-input"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="stream-clear-btn" onClick={() => setSearchQuery('')}>×</button>
              )}
            </div>

            <div className="severity-filter-chips">
              {['all', 'critical', 'suspicious', 'normal'].map(sev => (
                <button
                  key={sev}
                  className={`sev-chip sev-chip--${sev} ${filterSeverity === sev ? 'sev-chip--active' : ''}`}
                  onClick={() => setFilterSeverity(sev)}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Event Feed */}
          <div className="stream-feed-scroll">
            {filteredEvents.length === 0 ? (
              <div className="stream-empty">
                <Filter size={20} />
                <span>No events match current filter</span>
              </div>
            ) : (
              filteredEvents.map((evt, idx) => {
                const Icon = evt.icon
                const isSelected = selectedEvent?.id === evt.id
                const isFlash = newEventFlash === evt.id
                return (
                  <article
                    key={evt.id}
                    className={`stream-card stream-card--${evt.severity} ${isSelected ? 'stream-card--selected' : ''} ${isFlash ? 'stream-card--flash' : ''}`}
                    onClick={() => setSelectedEvent(evt)}
                    id={`stream-event-${evt.id}`}
                  >
                    <div className="stream-card-left">
                      <span className="stream-card-time">{evt.time}</span>
                      <div className={`stream-card-icon-box stream-card-icon-box--${evt.sourceCategory}`}>
                        <Icon size={12} strokeWidth={2} />
                      </div>
                    </div>

                    <div className="stream-card-body">
                      <div className="stream-card-top-row">
                        <span className={`stream-source-tag stream-source-tag--${evt.sourceCategory}`}>
                          {evt.source}
                        </span>
                        <span className={`stream-sev-badge stream-sev-badge--${evt.severity}`}>
                          {evt.severity}
                        </span>
                        {evt.correlated && (
                          <span className="stream-corr-tag" title="Part of correlated exfiltration sequence">
                            Seq #{evt.correlationIndex || '★'}
                          </span>
                        )}
                      </div>

                      <h4 className="stream-card-title">{evt.label}</h4>
                      <p className="stream-card-detail">{evt.detail}</p>

                      {evt.payload && (
                        <div className="stream-card-meta-preview">
                          {Object.entries(evt.payload).map(([k, v]) => (
                            <span key={k} className="meta-pair">
                              <span className="meta-key">{k}:</span>
                              <span className="meta-val">{String(v)}</span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <ChevronRight size={13} className="stream-card-arrow" />
                  </article>
                )
              })
            )}
            <div ref={streamEndRef} />
          </div>
        </section>

        {/* ───────────────────────────────────────
            CENTER COLUMN: Live Investigation Timeline
        ─────────────────────────────────────── */}
        <section className="live-col live-col--timeline">
          <div className="col-header">
            <div className="col-title-wrap">
              <div className="col-title-icon-box"><Layers size={14} /></div>
              <div>
                <h2 className="col-title">Investigation Timeline</h2>
                <span className="col-subtitle">Chronological sequence reconstruction & correlation</span>
              </div>
            </div>
            <div className="timeline-view-tabs">
              <button 
                className={`view-tab ${activeTabCenter === 'timeline' ? 'view-tab--active' : ''}`}
                onClick={() => setActiveTabCenter('timeline')}
              >
                Timeline View
              </button>
              <button 
                className={`view-tab ${activeTabCenter === 'graph' ? 'view-tab--active' : ''}`}
                onClick={() => setActiveTabCenter('graph')}
              >
                Chain View
              </button>
            </div>
          </div>

          {/* Timeline Controls & Key */}
          <div className="timeline-meta-bar">
            <div className="timeline-legend">
              <span className="legend-item"><span className="legend-dot legend-dot--crit" /> Critical Correlation</span>
              <span className="legend-item"><span className="legend-dot legend-dot--susp" /> Anomaly</span>
              <span className="legend-item"><span className="legend-dot legend-dot--norm" /> Baseline</span>
            </div>
            <span className="timeline-span-badge">Window: 10:02:14 → 10:09:20 (07m 06s)</span>
          </div>

          {/* Main Visual Vertical Timeline */}
          {activeTabCenter === 'timeline' ? (
            <div className="live-timeline-canvas">
              <div className="timeline-vertical-line" />

              {events.map((evt, idx) => {
                const Icon = evt.icon
                const isSelected = selectedEvent?.id === evt.id
                return (
                  <div 
                    key={evt.id} 
                    className={`timeline-node-wrap timeline-node-wrap--${evt.severity} ${isSelected ? 'timeline-node-wrap--selected' : ''}`}
                    onClick={() => setSelectedEvent(evt)}
                  >
                    {/* Node Dot / Glyph */}
                    <div className={`timeline-glyph timeline-glyph--${evt.severity}`}>
                      {evt.correlated ? (
                        <span className="timeline-glyph-num">{evt.correlationIndex || '★'}</span>
                      ) : (
                        <Icon size={11} strokeWidth={2} />
                      )}
                      <div className="timeline-glyph-ping" />
                    </div>

                    {/* Node Card */}
                    <div className="timeline-node-card">
                      <div className="timeline-card-header">
                        <div className="timeline-card-time-group">
                          <span className="timeline-node-time">{evt.time}</span>
                          <span className={`timeline-node-source source--${evt.sourceCategory}`}>{evt.source}</span>
                        </div>
                        <div className="timeline-card-badges">
                          {evt.confidence && (
                            <span className="conf-badge">Conf: {evt.confidence}</span>
                          )}
                          <span className={`sev-pill sev-pill--${evt.severity}`}>{evt.severity}</span>
                        </div>
                      </div>

                      <h4 className="timeline-node-label">{evt.label}</h4>
                      <p className="timeline-node-desc">{evt.detail}</p>

                      {evt.correlated && (
                        <div className="timeline-correlation-flag">
                          <Brain size={11} />
                          <span>Correlated in Sequence Cluster #1 (Data Exfiltration Vector)</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            /* Chain View: Horizontal Sequence Flow */
            <div className="live-chain-view">
              <div className="chain-view-intro">
                <span className="chain-tag">AI Correlated Causal Chain</span>
                <h3>Attribution Sequence Path</h3>
                <p>Identified chronological escalation sequence across Physical, Identity, Endpoint, and Network domains.</p>
              </div>

              <div className="chain-flow-track">
                {events.filter(e => e.correlated).map((evt, idx, arr) => (
                  <div key={evt.id} className="chain-flow-step">
                    <div className="chain-step-card">
                      <div className="chain-step-num">0{idx + 1}</div>
                      <span className="chain-step-time">{evt.time}</span>
                      <span className="chain-step-source">{evt.source}</span>
                      <p className="chain-step-text">{evt.label}</p>
                    </div>
                    {idx < arr.length - 1 && (
                      <div className="chain-flow-arrow">
                        <ArrowRight size={16} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* ───────────────────────────────────────
            RIGHT COLUMN: AI Agent Activity Panel
        ─────────────────────────────────────── */}
        <section className="live-col live-col--agents">
          <div className="col-header">
            <div className="col-title-wrap">
              <div className="col-title-icon-box"><Bot size={14} /></div>
              <div>
                <h2 className="col-title">AI Agent Activity Panel</h2>
                <span className="col-subtitle">6 Autonomous Intelligence Agents active</span>
              </div>
            </div>
            <span className="agent-online-pill">
              <span className="online-dot" /> 5 / 6 Running
            </span>
          </div>

          {/* Agents List Cards */}
          <div className="agents-list-scroll">
            {agents.map(agent => (
              <div key={agent.id} className={`agent-card agent-card--${agent.statusType}`}>
                <div className="agent-card-header">
                  <div className="agent-info-left">
                    <div className={`agent-avatar agent-avatar--${agent.color}`}>
                      <Cpu size={14} />
                    </div>
                    <div>
                      <h4 className="agent-name">{agent.name}</h4>
                      <span className="agent-telemetry-text">{agent.telemetry}</span>
                    </div>
                  </div>

                  <div className={`agent-status-badge agent-status-badge--${agent.statusType}`}>
                    {agent.statusType === 'analyzing' || agent.statusType === 'processing' || agent.statusType === 'running' ? (
                      <RefreshCw size={10} className="spin-fast" />
                    ) : agent.statusType === 'active' ? (
                      <Activity size={10} />
                    ) : (
                      <Clock size={10} />
                    )}
                    <span>{agent.status}</span>
                  </div>
                </div>

                <p className="agent-task-desc">{agent.task}</p>

                {/* Progress / Resource Load Bar */}
                <div className="agent-load-wrap">
                  <div className="load-label-row">
                    <span className="load-lbl">Processing Load</span>
                    <span className="load-val">{agent.load}%</span>
                  </div>
                  <div className="load-track">
                    <div 
                      className={`load-fill load-fill--${agent.color}`}
                      style={{ width: `${agent.load}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}

            {/* Live Terminal Mini Console */}
            <div className="agent-terminal-box">
              <div className="terminal-header">
                <Terminal size={11} />
                <span>SynapseX Orchestrator Live Stream</span>
                <span className="terminal-live-tag">LIVE STDOUT</span>
              </div>
              <div className="terminal-logs">
                <p className="log-line"><span className="log-t">[10:09:20]</span> [NEXUS-7] Correlating network socket 185.220.101.47:443 with PCAP EVD-006</p>
                <p className="log-line"><span className="log-t">[10:09:22]</span> [CIPHER-3] High entropy verified (7.98 bits/byte) - payload encrypted</p>
                <p className="log-line"><span className="log-t">[10:09:24]</span> [ARGUS-5] NTP synchronization aligned: 6 events within 426s window</p>
                <p className="log-line"><span className="log-t">[10:09:25]</span> [CORRELATION] Formed Hypothesis #1 with confidence 0.89</p>
                <p className="log-line log-line--active"><span className="log-t">[10:09:28]</span> [REASONING] Awaiting analyst confirmation for legal disclosure package...</p>
              </div>
            </div>
          </div>
        </section>

      </div>

      {/* ══════════════════════════════════════════
          BOTTOM BAR: AI CORRELATION STATUS & ADVISORY
      ══════════════════════════════════════════ */}
      <footer className="live-bottom-bar">
        <div className="correlation-status-block">
          
          <div className="corr-status-left">
            <div className="corr-icon-glow">
              <Sparkles size={20} className="glow-icon" />
            </div>
            <div>
              <div className="corr-header-row">
                <span className="corr-title">AI Correlation Status</span>
                <span className="corr-count-badge">{correlatedCount} related events detected</span>
              </div>
              <p className="corr-summary">
                Sequence pattern identified: Physical Access &rarr; Credentialed Login &rarr; Removable Storage &rarr; File Staging &rarr; Encrypted Egress
              </p>
            </div>
          </div>

          <div className="corr-status-metrics">
            <div className="metric-chip">
              <span className="metric-title">Correlation Confidence</span>
              <div className="metric-bar-group">
                <span className="metric-score">89%</span>
                <div className="metric-mini-bar">
                  <div className="metric-mini-fill" style={{ width: '89%' }} />
                </div>
              </div>
            </div>

            <div className="metric-chip">
              <span className="metric-title">Hypothesis Model</span>
              <span className="metric-val-text">SynapseX-Forge-v3 (Multi-Modal)</span>
            </div>

            <div className="metric-chip">
              <span className="metric-title">Human Verification</span>
              <span className="metric-val-status">Awaiting Investigator Review</span>
            </div>
          </div>

        </div>

        {/* Responsible AI Disclaimer Banner */}
        <div className="live-legal-disclaimer">
          <Info size={13} className="disclaimer-icon" />
          <span>
            <strong>AI-Assisted Investigation Advisory:</strong> SynapseX provides probabilistic evidence correlation and telemetry synthesis to support authorized digital investigators. Automated models identify potential chronological patterns and anomalous correlations, but do not make autonomous criminal culpability determinations. All findings require independent human verification.
          </span>
        </div>
      </footer>

    </div>
  )
}
