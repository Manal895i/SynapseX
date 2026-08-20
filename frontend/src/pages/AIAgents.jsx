import { useState, useEffect } from 'react'
import {
  Bot, Cpu, Play, Pause, RefreshCw,
  HardDrive, GitBranch, Video, Network,
  Share2, Brain, FileText, AlertCircle,
  CheckCircle2, Clock, Activity, Zap,
  Layers, ArrowRight, ArrowDown, ChevronRight,
  SlidersHorizontal, Terminal, Shield, Sparkles,
  Search, Eye, HelpCircle, FileCheck, Check
} from 'lucide-react'
import './AIAgents.css'

/* ═══════════════════════════════════════════════════
   MULTI-AGENT FLEET DATASET
═══════════════════════════════════════════════════ */
const AGENTS_DATA = [
  {
    id: 'chief',
    name: 'Chief Investigator Agent',
    tier: 'orchestration',
    role: 'Central Autonomous Supervisor & Task Orchestrator',
    status: 'Active',
    statusType: 'active',
    task: 'Coordinating multi-agent workflow & synthesizing investigative hypothesis',
    evidenceProcessed: 'All 10 Agent Telemetry Feeds',
    lastActivity: '1s ago',
    model: 'SynapseX-Orchestrator-v3',
    confidence: 96,
    color: 'blue',
    icon: Bot,
    cpuLoad: 88,
    memory: '14.2 GB',
    throughput: '340 tok/s',
    logs: [
      '[10:09:20] Dispatched Deep Packet Inspection task to Network Agent',
      '[10:09:22] Acknowledged 6-stage causal chain from Correlation Agent',
      '[10:09:25] Triggered Missing Evidence Agent gap evaluation for Door DR-B02',
      '[10:09:28] Synthesizing executive briefing package for human investigator'
    ]
  },
  {
    id: 'evidence',
    name: 'Evidence Agent',
    tier: 'ingestion',
    role: 'Artifact Ingestion & Cryptographic Integrity',
    status: 'Active',
    statusType: 'active',
    task: 'Processing Windows Logs & Hash Verification',
    evidenceProcessed: '1,248 Items (23.2 GB sealed)',
    lastActivity: '2s ago',
    model: 'Forge-Evidence-Parser-v2',
    confidence: 99,
    color: 'blue',
    icon: HardDrive,
    cpuLoad: 76,
    memory: '4.8 GB',
    throughput: '124 files/s',
    logs: [
      '[10:05:30] Computed SHA-256 for windows_event_logs.evtx: b8c3e1f4...',
      '[10:05:32] Parsed 4,812 Security Event IDs (Logon, Kerberos, Privilege)',
      '[10:08:00] Ingested usb_activity_log.csv from CrowdStrike EDR connector',
      '[10:08:02] Integrity sealed into SynapseX immutable vault ledger'
    ]
  },
  {
    id: 'timeline',
    name: 'Timeline Agent',
    tier: 'synthesis',
    role: 'Cross-Source Chronological Synchronization',
    status: 'Complete',
    statusType: 'complete',
    task: 'Reconstructing event sequence & correcting clock skew',
    evidenceProcessed: '10 Events Synchronized (±14ms NTP)',
    lastActivity: '42s ago',
    model: 'Forge-Temporal-Reconstructor',
    confidence: 98,
    color: 'cyan',
    icon: GitBranch,
    cpuLoad: 24,
    memory: '2.1 GB',
    throughput: '0 ev/s (Idle)',
    logs: [
      '[10:03:00] Aligned CCTV CAM-07 timestamps with access control server',
      '[10:05:00] Clock offset normalized: -14ms across terminal WKST-041',
      '[10:09:30] Complete incident window sequence generated (10:02 to 10:09 UTC)',
      '[10:09:32] Chronological ordering locked and passed to Correlation Agent'
    ]
  },
  {
    id: 'cctv',
    name: 'CCTV Agent',
    tier: 'ingestion',
    role: 'Computer Vision & Physical Access Tracking',
    status: 'Active',
    statusType: 'active',
    task: 'Analyzing CAM-07 physical access feeds & badge verification',
    evidenceProcessed: '4 Video Streams (30 FPS Real-time)',
    lastActivity: 'Just now',
    model: 'Forge-Vision-OCR-v4',
    confidence: 86,
    color: 'purple',
    icon: Video,
    cpuLoad: 92,
    memory: '8.4 GB',
    throughput: '30 FPS',
    logs: [
      '[10:02:14] Object detected: Person entered restricted Server Room B corridor',
      '[10:02:18] Facial bounding box logged; subject unverified against whitelist',
      '[10:09:33] Visual confirmation: Subject departed carrying removable storage',
      '[10:14:05] Movement tracked to North perimeter exit door'
    ]
  },
  {
    id: 'network',
    name: 'Network Agent',
    tier: 'ingestion',
    role: 'Deep Packet Inspection & Threat Intel Correlator',
    status: 'Analyzing',
    statusType: 'analyzing',
    task: 'Detecting suspicious traffic & TOR exit node telemetry',
    evidenceProcessed: '4.8 GB PCAP (14.2k pkts/s)',
    lastActivity: 'Just now',
    model: 'Forge-NetDPI-Classifier',
    confidence: 95,
    color: 'red',
    icon: Network,
    cpuLoad: 84,
    memory: '6.2 GB',
    throughput: '18.4 MB/s',
    logs: [
      '[10:09:20] Alert: 1.8 GB high-entropy burst to 185.220.101.47:443',
      '[10:09:21] Threat Intel match: 185.220.101.47 confirmed TOR Exit Node',
      '[10:09:22] Protocol confirmed TLS 1.3 encrypted tunnel session',
      '[10:09:24] IP reputation score: 99/100 (Malicious Egress Proxy)'
    ]
  },
  {
    id: 'graph',
    name: 'Knowledge Graph Agent',
    tier: 'synthesis',
    role: 'Multi-Modal Entity Extraction & Link Analysis',
    status: 'Active',
    statusType: 'active',
    task: 'Graphing cross-modal entity connections & relational links',
    evidenceProcessed: '9 Entities · 10 Discovered Relations',
    lastActivity: '4s ago',
    model: 'Forge-Entity-Linker',
    confidence: 94,
    color: 'green',
    icon: Share2,
    cpuLoad: 68,
    memory: '3.6 GB',
    throughput: '42 links/s',
    logs: [
      '[10:04:10] Extracted node: LAPTOP-07 (Device)',
      '[10:05:32] Established relationship: LAPTOP-07 -> connected to -> USB-123',
      '[10:07:45] Established relationship: LAPTOP-07 -> accessed -> Confidential_File.pdf',
      '[10:09:20] Established relationship: LAPTOP-07 -> communicated with -> 185.220.101.47'
    ]
  },
  {
    id: 'correlation',
    name: 'Correlation Agent',
    tier: 'intelligence',
    role: 'Multi-Vector Causal Pattern Matching',
    status: 'Running',
    statusType: 'running',
    task: 'Correlating physical and digital evidence into causal chain',
    evidenceProcessed: '6 Sequential Event Clusters',
    lastActivity: '1s ago',
    model: 'Forge-Causal-Matcher-v3',
    confidence: 89,
    color: 'purple',
    icon: Brain,
    cpuLoad: 94,
    memory: '7.8 GB',
    throughput: '88 hyps/s',
    logs: [
      '[10:04:15] Correlated CCTV entry (10:02) with door unlock (10:03) and login (10:04)',
      '[10:08:00] Correlated USB insert (10:05) with file staging (10:07)',
      '[10:09:25] Formed composite hypothesis: Insider Data Exfiltration (Score: 0.89)',
      '[10:09:28] Forwarded validated causal chain to Reasoning Agent'
    ]
  },
  {
    id: 'reasoning',
    name: 'Reasoning Agent',
    tier: 'intelligence',
    role: 'Investigative Narrative & Intent Deduction',
    status: 'Waiting',
    statusType: 'waiting',
    task: 'Awaiting correlated findings from Correlation Agent',
    evidenceProcessed: 'Prompt Buffer Loaded · Ready',
    lastActivity: '8s ago',
    model: 'SynapseX-Reasoning-LLM',
    confidence: 91,
    color: 'gray',
    icon: Zap,
    cpuLoad: 12,
    memory: '18.4 GB',
    throughput: '0 tok/s (Standby)',
    logs: [
      '[10:09:20] Loaded investigative context into active working memory',
      '[10:09:25] Received causal graph from Correlation Agent',
      '[10:09:28] In standby: Ready to generate investigator reasoning summary on user trigger'
    ]
  },
  {
    id: 'missing',
    name: 'Missing Evidence Agent',
    tier: 'synthesis',
    role: 'Blind Spot & Telemetry Gap Identification',
    status: 'Active',
    statusType: 'active',
    task: 'Flagging missing telemetry & investigation blind spots',
    evidenceProcessed: '2 Critical Gaps Identified',
    lastActivity: '5s ago',
    model: 'Forge-Gap-Detector',
    confidence: 92,
    color: 'amber',
    icon: AlertCircle,
    cpuLoad: 58,
    memory: '2.8 GB',
    throughput: '18 checks/s',
    logs: [
      '[10:04:00] Gap flagged: DR-B02 badge reader lacks secondary biometric factor',
      '[10:07:00] Gap flagged: USB Mass Storage Write audit policy disabled on WKST-041',
      '[10:09:25] Recommendation: Acquire full memory dump of WKST-041 before reboot',
      '[10:09:28] Forwarded gap report to Chief Investigator Agent'
    ]
  },
  {
    id: 'report',
    name: 'Report Agent',
    tier: 'delivery',
    role: 'Court-Admissible Brief & STIX 2.1 Manifest Export',
    status: 'Reviewing',
    statusType: 'reviewing',
    task: 'Drafting STIX 2.1 forensic brief & executive disclosure package',
    evidenceProcessed: 'Court Manifest Package Ready',
    lastActivity: '12s ago',
    model: 'Forge-Legal-Exporter',
    confidence: 97,
    color: 'blue',
    icon: FileText,
    cpuLoad: 42,
    memory: '3.1 GB',
    throughput: '1 doc/s',
    logs: [
      '[10:09:25] Generated cryptographic chain of custody seal for 6 primary artifacts',
      '[10:09:26] Formatted STIX 2.1 Threat Intelligence Bundle with IOC indicators',
      '[10:09:28] Drafted court-admissible PDF forensic summary for lead investigator review'
    ]
  }
]

const TIERS = [
  { id: 'all', label: 'All Fleet Agents (10)' },
  { id: 'orchestration', label: 'Orchestration (1)' },
  { id: 'ingestion', label: 'Ingestion & Sensing (3)' },
  { id: 'synthesis', label: 'Synthesis & Gap Analysis (3)' },
  { id: 'intelligence', label: 'Causal Intelligence & Reasoning (2)' },
  { id: 'delivery', label: 'Reporting & Compliance (1)' }
]

export default function AIAgents() {
  const [agents, setAgents] = useState(AGENTS_DATA)
  const [selectedAgent, setSelectedAgent] = useState(AGENTS_DATA[0]) // Default Chief Investigator
  const [activeTier, setActiveTier] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSimulating, setIsSimulating] = useState(true)
  const [simulationTick, setSimulationTick] = useState(0)

  // Simulation loop for live telemetry updates
  useEffect(() => {
    if (!isSimulating) return
    const interval = setInterval(() => {
      setSimulationTick(t => t + 1)
      setAgents(prev => prev.map(a => {
        if (a.statusType === 'waiting') return a
        const cpuDelta = Math.floor((Math.random() - 0.5) * 6)
        const newCpu = Math.min(Math.max(a.cpuLoad + cpuDelta, 20), 99)
        return { ...a, cpuLoad: newCpu }
      }))
    }, 2500)
    return () => clearInterval(interval)
  }, [isSimulating])

  // Filtered agent list
  const filteredAgents = agents.filter(a => {
    if (activeTier !== 'all' && a.tier !== activeTier) return false
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase()
      return (
        a.name.toLowerCase().includes(q) ||
        a.task.toLowerCase().includes(q) ||
        a.role.toLowerCase().includes(q) ||
        a.status.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Quick stats
  const activeCount = agents.filter(a => a.statusType === 'active' || a.statusType === 'analyzing' || a.statusType === 'running').length

  return (
    <div className="agents-page-root">

      {/* ══════════════════════════════════════════
          PAGE HEADER
      ══════════════════════════════════════════ */}
      <header className="agents-page-header">
        <div className="agents-header-left">
          <div className="agents-eyebrow">
            <Bot size={13} className="agents-eyebrow-icon" />
            <span>Autonomous Multi-Agent Investigation Architecture</span>
          </div>
          <h1 className="agents-page-title">AI Agents Fleet Monitoring</h1>
          <p className="agents-page-sub">
            CASE-2026-001 · Decentralized specialized intelligence agents collaborating under autonomous supervision for multi-modal evidence ingestion, chronological reconstruction, and causal correlation.
          </p>
        </div>

        <div className="agents-header-actions">
          <div className="fleet-status-pill">
            <span className="fleet-pulse-dot" />
            <span className="fleet-status-text">{activeCount} / 10 Agents Active</span>
          </div>

          <button 
            className={`agents-ctrl-btn ${isSimulating ? 'agents-ctrl-btn--active' : ''}`}
            onClick={() => setIsSimulating(!isSimulating)}
            title="Toggle simulated agent telemetry stream"
          >
            {isSimulating ? <><Pause size={13} /> Live Telemetry ON</> : <><Play size={13} /> Resume Stream</>}
          </button>

          <button 
            className="agents-ctrl-btn-ghost"
            onClick={() => {
              setAgents(AGENTS_DATA)
              setSelectedAgent(AGENTS_DATA[0])
            }}
            title="Re-synchronize agent state"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </header>

      {/* ══════════════════════════════════════════
          TOP SECTION: VISUAL MULTI-AGENT WORKFLOW
          (Explaining architecture to judges & sponsors)
      ══════════════════════════════════════════ */}
      <section className="workflow-card">
        <div className="workflow-header">
          <div className="workflow-title-wrap">
            <div className="wf-icon-box"><Sparkles size={14} /></div>
            <div>
              <h2 className="workflow-title">Multi-Agent Investigation Workflow</h2>
              <span className="workflow-sub">Hierarchical orchestration & data flow from raw telemetry to court-admissible synthesis</span>
            </div>
          </div>
          <span className="wf-tag">SYNAPSEX ORCHESTRATION PIPELINE</span>
        </div>

        <div className="workflow-diagram">

          {/* APEX: Chief Investigator Agent */}
          <div className="wf-tier wf-tier--apex">
            <div 
              className={`wf-node wf-node--chief ${selectedAgent.id === 'chief' ? 'wf-node--selected' : ''}`}
              onClick={() => setSelectedAgent(AGENTS_DATA[0])}
            >
              <div className="wf-node-top">
                <div className="wf-node-icon wf-node-icon--chief"><Bot size={16} /></div>
                <div className="wf-node-status wf-node-status--active">
                  <span className="pulse-dot-mini" /> Supervisor
                </div>
              </div>
              <strong className="wf-node-title">Chief Investigator Agent</strong>
              <span className="wf-node-sub">Multi-Agent Task Orchestrator & Hypothesis Director</span>
              <div className="wf-node-metrics">
                <span>Model: SynapseX-Orchestrator-v3</span>
                <span>Confidence: 96%</span>
              </div>
            </div>
          </div>

          {/* Connecting Trunk Line */}
          <div className="wf-trunk-line">
            <div className="trunk-pulse" />
          </div>

          {/* MIDDLE TIER: 9 Specialized Sub-Agents */}
          <div className="wf-grid-subagents">

            {/* Ingestion Stream */}
            <div className="wf-column-group">
              <span className="wf-group-label">1. SENSING & INGESTION</span>
              <div className="wf-subnodes">
                {[AGENTS_DATA[1], AGENTS_DATA[3], AGENTS_DATA[4]].map(agent => (
                  <div 
                    key={agent.id}
                    className={`wf-mini-card wf-mini-card--${agent.statusType} ${selectedAgent.id === agent.id ? 'wf-mini-card--selected' : ''}`}
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <agent.icon size={13} className="wf-mini-icon" />
                    <div className="wf-mini-text">
                      <strong>{agent.name}</strong>
                      <span>{agent.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Synthesis Stream */}
            <div className="wf-column-group">
              <span className="wf-group-label">2. SYNTHESIS & LINKING</span>
              <div className="wf-subnodes">
                {[AGENTS_DATA[2], AGENTS_DATA[5], AGENTS_DATA[8]].map(agent => (
                  <div 
                    key={agent.id}
                    className={`wf-mini-card wf-mini-card--${agent.statusType} ${selectedAgent.id === agent.id ? 'wf-mini-card--selected' : ''}`}
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <agent.icon size={13} className="wf-mini-icon" />
                    <div className="wf-mini-text">
                      <strong>{agent.name}</strong>
                      <span>{agent.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Intelligence & Reasoning Stream */}
            <div className="wf-column-group">
              <span className="wf-group-label">3. REASONING & ATTRIBUTION</span>
              <div className="wf-subnodes">
                {[AGENTS_DATA[6], AGENTS_DATA[7], AGENTS_DATA[9]].map(agent => (
                  <div 
                    key={agent.id}
                    className={`wf-mini-card wf-mini-card--${agent.statusType} ${selectedAgent.id === agent.id ? 'wf-mini-card--selected' : ''}`}
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <agent.icon size={13} className="wf-mini-icon" />
                    <div className="wf-mini-text">
                      <strong>{agent.name}</strong>
                      <span>{agent.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Flow Pipeline Indicator */}
          <div className="wf-pipeline-flow-bar">
            <span className="flow-step">Raw Telemetry</span>
            <ArrowRight size={13} className="flow-arr" />
            <span className="flow-step">Integrity & CV</span>
            <ArrowRight size={13} className="flow-arr" />
            <span className="flow-step">Timeline Sync</span>
            <ArrowRight size={13} className="flow-arr" />
            <span className="flow-step">Knowledge Graph</span>
            <ArrowRight size={13} className="flow-arr" />
            <span className="flow-step">Causal Correlation</span>
            <ArrowRight size={13} className="flow-arr" />
            <span className="flow-step">Reasoning & Brief</span>
          </div>

        </div>
      </section>

      {/* ══════════════════════════════════════════
          TOOLBAR & FILTER
      ══════════════════════════════════════════ */}
      <div className="agents-toolbar-card">
        <div className="agents-search-wrap">
          <Search size={13} className="agents-search-icon" />
          <input 
            type="text"
            placeholder="Search agents, active tasks, or telemetry..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="agents-search-input"
          />
          {searchQuery && (
            <button className="agents-clear-btn" onClick={() => setSearchQuery('')}>×</button>
          )}
        </div>

        <div className="tier-filter-chips">
          {TIERS.map(t => (
            <button
              key={t.id}
              className={`tier-chip ${activeTier === t.id ? 'tier-chip--active' : ''}`}
              onClick={() => setActiveTier(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ══════════════════════════════════════════
          AGENT CARDS GRID & ACTIVE INSPECTION DRAWER
      ══════════════════════════════════════════ */}
      <div className="agents-main-grid">

        {/* 10 Agent Cards Grid */}
        <div className="agents-cards-grid">
          {filteredAgents.map(agent => {
            const Icon = agent.icon
            const isSelected = selectedAgent.id === agent.id

            return (
              <article
                key={agent.id}
                className={`agent-box agent-box--${agent.statusType} ${isSelected ? 'agent-box--selected' : ''}`}
                onClick={() => setSelectedAgent(agent)}
              >
                {/* Top Row: Name & Status */}
                <div className="agent-box-header">
                  <div className="agent-box-avatar-group">
                    <div className={`agent-box-icon agent-box-icon--${agent.color}`}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <h3 className="agent-box-name">{agent.name}</h3>
                      <span className="agent-box-role">{agent.role}</span>
                    </div>
                  </div>

                  {/* Animated Status Indicator */}
                  <div className={`agent-box-status agent-box-status--${agent.statusType}`}>
                    {agent.statusType === 'active' || agent.statusType === 'analyzing' || agent.statusType === 'running' ? (
                      <span className="status-dot-active spin-fast" />
                    ) : agent.statusType === 'complete' ? (
                      <CheckCircle2 size={11} />
                    ) : (
                      <Clock size={11} />
                    )}
                    <span>{agent.status}</span>
                  </div>
                </div>

                {/* Current Task */}
                <div className="agent-box-task-wrap">
                  <span className="agent-box-lbl">Current Task:</span>
                  <p className="agent-box-task-text">{agent.task}</p>
                </div>

                {/* Evidence Processed & Last Activity */}
                <div className="agent-box-metrics-row">
                  <div className="agent-box-metric">
                    <span className="agent-box-lbl">Evidence Processed</span>
                    <strong className="agent-box-val">{agent.evidenceProcessed}</strong>
                  </div>
                  <div className="agent-box-metric agent-box-metric--right">
                    <span className="agent-box-lbl">Last Activity</span>
                    <strong className="agent-box-val agent-box-val--time">{agent.lastActivity}</strong>
                  </div>
                </div>

                {/* CPU / Load Bar */}
                <div className="agent-box-load-wrap">
                  <div className="load-row">
                    <span className="load-k">Processing Load</span>
                    <span className="load-v">{agent.cpuLoad}% · {agent.throughput}</span>
                  </div>
                  <div className="load-bar-bg">
                    <div 
                      className={`load-bar-fill load-bar-fill--${agent.color}`}
                      style={{ width: `${agent.cpuLoad}%` }}
                    />
                  </div>
                </div>
              </article>
            )
          })}
        </div>

        {/* Selected Agent Inspector & Real-time Log Stream */}
        <aside className="agent-inspect-panel">
          <div className="inspect-header">
            <div className="inspect-title-group">
              <div className={`inspect-avatar inspect-avatar--${selectedAgent.color}`}>
                <selectedAgent.icon size={18} />
              </div>
              <div>
                <span className="inspect-tag">{selectedAgent.tier.toUpperCase()} TIER</span>
                <h3 className="inspect-name">{selectedAgent.name}</h3>
              </div>
            </div>
            <span className={`inspect-status-badge inspect-status-badge--${selectedAgent.statusType}`}>
              {selectedAgent.status}
            </span>
          </div>

          <div className="inspect-body">

            {/* Telemetry Grid */}
            <div className="inspect-meta-grid">
              <div className="inspect-cell">
                <span className="inspect-k">Foundation Model</span>
                <span className="inspect-v">{selectedAgent.model}</span>
              </div>
              <div className="inspect-cell">
                <span className="inspect-k">Accuracy / Confidence</span>
                <span className="inspect-v inspect-v--green">{selectedAgent.confidence}%</span>
              </div>
              <div className="inspect-cell">
                <span className="inspect-k">Active Memory</span>
                <span className="inspect-v">{selectedAgent.memory}</span>
              </div>
              <div className="inspect-cell">
                <span className="inspect-k">Current Output Rate</span>
                <span className="inspect-v">{selectedAgent.throughput}</span>
              </div>
            </div>

            {/* Active Operation Details */}
            <div className="inspect-section">
              <h4 className="inspect-section-title"><Activity size={12} /> Active Task Scope</h4>
              <p className="inspect-desc-box">{selectedAgent.task}</p>
            </div>

            {/* Evidence Processed Summary */}
            <div className="inspect-section">
              <h4 className="inspect-section-title"><HardDrive size={12} /> Verified Forensic Scope</h4>
              <div className="inspect-scope-card">
                <HardDrive size={13} className="scope-icon" />
                <span>{selectedAgent.evidenceProcessed}</span>
              </div>
            </div>

            {/* Real-time Agent Log Stream */}
            <div className="inspect-section">
              <div className="inspect-section-hdr-row">
                <h4 className="inspect-section-title"><Terminal size={12} /> Real-Time Decision Stream</h4>
                <span className="live-pill-mini">STDOUT</span>
              </div>

              <div className="inspect-terminal">
                {selectedAgent.logs.map((log, idx) => (
                  <p key={idx} className="inspect-log-line">
                    <span className="log-arrow">&gt;</span> {log}
                  </p>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="inspect-actions">
              <button className="inspect-btn inspect-btn--primary">
                <RefreshCw size={13} /> Re-run Agent Task
              </button>
              <button className="inspect-btn inspect-btn--ghost">
                <Eye size={13} /> View Memory State
              </button>
            </div>

          </div>
        </aside>

      </div>

    </div>
  )
}
