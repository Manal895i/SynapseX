import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  HardDrive, Brain, ShieldAlert, Bot,
  Clock, Wifi, AlertTriangle, ChevronRight,
  Usb, Monitor, Lock, Video, FileSearch,
  Network, CheckCircle2, CircleDot, Zap,
  TrendingUp, Eye, Search, Activity,
  FlaskConical, Link2, ListChecks
} from 'lucide-react'
import './Dashboard.css'

/* ─────────────────────────────────────────
   MOCK DATA
───────────────────────────────────────── */
const CASE = {
  id: 'CASE-2026-001',
  name: 'Suspected Data Exfiltration',
  classification: 'CONFIDENTIAL',
  tlp: 'TLP:RED',
  opened: '2026-08-20T08:00:00Z',
  lead: 'Sr. Analyst',
  status: 'active',
}

const SUMMARY_CARDS = [
  {
    id: 'active-evidence',
    label: 'Active Evidence',
    value: '1,248',
    unit: 'Items',
    icon: HardDrive,
    color: 'blue',
    delta: '+14 today',
    trend: 'up',
  },
  {
    id: 'ai-findings',
    label: 'AI Findings',
    value: '12',
    unit: 'Findings',
    icon: Brain,
    color: 'cyan',
    delta: '+3 new',
    trend: 'up',
  },
  {
    id: 'risk-level',
    label: 'Investigation Risk',
    value: 'Medium',
    unit: '',
    icon: ShieldAlert,
    color: 'medium',
    delta: 'Escalating',
    trend: 'up',
  },
  {
    id: 'agent-status',
    label: 'Agent Status',
    value: '8 / 10',
    unit: 'Active',
    icon: Bot,
    color: 'green',
    delta: '2 idle',
    trend: 'flat',
  },
]

const TIMELINE_EVENTS = [
  {
    id: 'e1',
    time: '10:02',
    source: 'CCTV',
    label: 'Person entered restricted area',
    icon: Video,
    type: 'suspicious',
    detail: 'CAM-07 · Server Room B · Badge ID not matched',
  },
  {
    id: 'e2',
    time: '10:03',
    source: 'Access Control',
    label: 'Door opened — Server Room B',
    icon: Lock,
    type: 'suspicious',
    detail: 'Credential: EMP-4421 · Tailgating alert triggered',
  },
  {
    id: 'e3',
    time: '10:04',
    source: 'System',
    label: 'User login on WKST-041',
    icon: Monitor,
    type: 'normal',
    detail: 'User: jsmith@corp.int · IP: 10.4.12.41',
  },
  {
    id: 'e4',
    time: '10:05',
    source: 'USB',
    label: 'External device connected',
    icon: Usb,
    type: 'critical',
    detail: 'Device: SanDisk Ultra 128GB · S/N: SDCZ48-128G · Unregistered',
  },
  {
    id: 'e5',
    time: '10:07',
    source: 'File Activity',
    label: 'Sensitive files accessed',
    icon: FileSearch,
    type: 'critical',
    detail: '34 files · /Finance/Q2-Projections/ · 2.1 GB read',
  },
  {
    id: 'e6',
    time: '10:09',
    source: 'Network',
    label: 'Large outbound data transfer',
    icon: Network,
    type: 'critical',
    detail: '1.8 GB → 185.220.101.47 (TOR Exit Node) · Protocol: HTTPS',
  },
]

const AI_FINDINGS = [
  { label: 'Correlated sequence detected',      icon: Link2,      color: 'blue',   value: 'Physical → Digital → Exfil' },
  { label: 'Confidence Level',                  icon: FlaskConical, color: 'medium', value: 'Medium (67%)' },
  { label: 'Supporting Evidence',               icon: CheckCircle2, color: 'green',  value: '5 artifacts correlated' },
  { label: 'Alternative Explanations',          icon: CircleDot,  color: 'gray',   value: '2 hypotheses flagged' },
  { label: 'Missing Evidence Recommendations',  icon: ListChecks, color: 'cyan',   value: '3 gaps identified' },
]

const RECENT_ALERTS = [
  { severity: 'critical', msg: 'TOR exit node detected in outbound traffic', time: '10:09' },
  { severity: 'high',     msg: 'Unregistered USB device write operation',    time: '10:05' },
  { severity: 'medium',   msg: 'Tailgating detected at access control point',time: '10:03' },
]

/* ─────────────────────────────────────────
   LIVE CLOCK
───────────────────────────────────────── */
function LiveClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <span className="case-clock">
      <Clock size={11} />
      {now.toUTCString().slice(5, 25)} UTC
    </span>
  )
}

/* ─────────────────────────────────────────
   SUMMARY CARD
───────────────────────────────────────── */
function SummaryCard({ card }) {
  const Icon = card.icon
  return (
    <div className={`dash-summary-card dash-summary-card--${card.color}`} id={`card-${card.id}`}>
      <div className="dsc-top">
        <div className="dsc-label-row">
          <span className="dsc-label">{card.label}</span>
        </div>
        <div className={`dsc-icon dsc-icon--${card.color}`}>
          <Icon size={18} strokeWidth={1.6} />
        </div>
      </div>
      <div className="dsc-value">
        {card.value}
        {card.unit && <span className="dsc-unit"> {card.unit}</span>}
      </div>
      <div className="dsc-footer">
        <span className={`dsc-delta dsc-delta--${card.color === 'medium' ? 'warn' : card.trend === 'up' ? 'up' : 'flat'}`}>
          {card.trend === 'up' ? '↑' : '—'} {card.delta}
        </span>
      </div>
      <div className="dsc-glow-bar" />
    </div>
  )
}

/* ─────────────────────────────────────────
   TIMELINE EVENT
───────────────────────────────────────── */
function TimelineEvent({ event, index }) {
  const [expanded, setExpanded] = useState(false)
  const Icon = event.icon

  return (
    <div
      className={`tl-event tl-event--${event.type} ${expanded ? 'tl-event--expanded' : ''}`}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={() => setExpanded(e => !e)}
      id={`event-${event.id}`}
    >
      <div className="tl-time-col">
        <span className="tl-time">{event.time}</span>
        <div className={`tl-dot tl-dot--${event.type}`} />
      </div>

      <div className="tl-connector">
        <div className="tl-line" />
      </div>

      <div className="tl-body">
        <div className="tl-row">
          <div className={`tl-source-badge tl-source-badge--${event.type}`}>
            <Icon size={11} strokeWidth={2} />
            {event.source}
          </div>
          {event.type === 'critical' && (
            <span className="tl-flag tl-flag--critical">
              <AlertTriangle size={9} /> SUSPICIOUS
            </span>
          )}
          {event.type === 'suspicious' && (
            <span className="tl-flag tl-flag--suspicious">
              <AlertTriangle size={9} /> FLAGGED
            </span>
          )}
        </div>
        <p className="tl-label">{event.label}</p>
        {expanded && (
          <div className="tl-detail">
            <span className="tl-detail-text">{event.detail}</span>
          </div>
        )}
        {!expanded && (
          <span className="tl-expand-hint">Click to expand ›</span>
        )}
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────
   MAIN DASHBOARD
───────────────────────────────────────── */
export default function Dashboard() {
  const navigate = useNavigate()
  const [pulse, setPulse] = useState(0)

  // Simulate live pulse counter
  useEffect(() => {
    const t = setInterval(() => setPulse(p => p + 1), 4000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="dash-root">

      {/* ═══════════════════════════════
          PAGE HEADER
      ═══════════════════════════════ */}
      <div className="dash-page-header">
        <div className="dash-header-left">
          <div className="dash-header-eyebrow">
            <Zap size={12} className="eyebrow-icon" />
            <span>Intelligence Dashboard</span>
            <span className="eyebrow-sep" />
            <Activity size={11} />
            <span className="eyebrow-live">Live Monitoring Active</span>
          </div>
          <h1 className="dash-page-title">
            Investigation Intelligence Dashboard
          </h1>
          <p className="dash-page-sub">
            Real-time analysis and AI-assisted correlation for active digital investigation
          </p>
        </div>
        <div className="dash-header-right">
          <LiveClock />
          <div className="dash-live-indicator">
            <span className="pulse-dot" />
            <span>Auto-refresh</span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════
          CASE BANNER
      ═══════════════════════════════ */}
      <div className="case-banner">
        <div className="case-banner-left">
          <div className="case-id-row">
            <span className="case-id-badge">{CASE.id}</span>
            <span className="case-tlp">{CASE.tlp}</span>
            <span className="case-class">{CASE.classification}</span>
          </div>
          <div className="case-name">{CASE.name}</div>
          <div className="case-meta-row">
            <span className="case-meta-item">
              <Eye size={11} /> Lead: {CASE.lead}
            </span>
            <span className="case-meta-sep" />
            <span className="case-meta-item">
              <Clock size={11} /> Opened: 2026-08-20 08:00 UTC
            </span>
          </div>
        </div>
        <div className="case-banner-right">
          <div className="case-status-wrap">
            <span className="badge badge--active">
              <span className="pulse-dot" style={{ width: 6, height: 6 }} />
              ACTIVE
            </span>
          </div>
          <div className="case-alerts-mini">
            {RECENT_ALERTS.map((a, i) => (
              <div key={i} className={`case-alert-mini case-alert-mini--${a.severity}`}>
                <AlertTriangle size={10} />
                <span>{a.msg}</span>
                <span className="cam-time">{a.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════
          SUMMARY CARDS
      ═══════════════════════════════ */}
      <div className="dash-cards-grid">
        {SUMMARY_CARDS.map(card => (
          <SummaryCard key={card.id} card={card} />
        ))}
      </div>

      {/* ═══════════════════════════════
          MAIN CONTENT — TIMELINE + AI
      ═══════════════════════════════ */}
      <div className="dash-main-grid">

        {/* ─── LEFT: TIMELINE ─── */}
        <div className="dash-panel dash-panel--timeline">
          <div className="panel-header">
            <div className="panel-title">
              <Activity size={15} />
              Live Investigation Timeline
            </div>
            <div className="panel-header-right">
              <span className="badge badge--active" style={{ fontSize: 9 }}>
                <span className="pulse-dot" style={{ width: 5, height: 5 }} />
                Live
              </span>
              <span className="panel-event-count">{TIMELINE_EVENTS.length} events</span>
            </div>
          </div>

          <div className="tl-legend">
            <span className="tl-legend-item tl-legend-item--normal">● Normal</span>
            <span className="tl-legend-item tl-legend-item--suspicious">● Flagged</span>
            <span className="tl-legend-item tl-legend-item--critical">● Suspicious</span>
          </div>

          <div className="tl-scroll-area">
            <div className="tl-track">
              {TIMELINE_EVENTS.map((evt, i) => (
                <TimelineEvent key={evt.id} event={evt} index={i} />
              ))}
            </div>
          </div>

          <div className="tl-footer">
            <TrendingUp size={11} />
            <span>Showing events 10:02 – 10:09 · Case window: 7 minutes</span>
          </div>
        </div>

        {/* ─── RIGHT: AI PANEL ─── */}
        <div className="dash-panel dash-panel--ai">
          <div className="panel-header">
            <div className="panel-title">
              <Brain size={15} />
              AI Investigation Summary
            </div>
            <span className="badge badge--info">NEXUS-7</span>
          </div>

          {/* Confidence meter */}
          <div className="ai-confidence-block">
            <div className="ai-conf-header">
              <span className="ai-conf-label">Overall Confidence</span>
              <span className="ai-conf-value ai-conf-value--medium">Medium — 67%</span>
            </div>
            <div className="ai-conf-bar-wrap">
              <div className="ai-conf-bar ai-conf-bar--medium" style={{ width: '67%' }} />
            </div>
            <p className="ai-conf-desc">
              NEXUS-7 has identified a high-probability correlated event sequence
              consistent with an <strong>insider data exfiltration attempt</strong>.
              Correlation anchored on physical access → system access → data transfer.
            </p>
          </div>

          {/* Findings list */}
          <div className="ai-findings-list">
            {AI_FINDINGS.map((f, i) => {
              const Icon = f.icon
              return (
                <div key={i} className={`ai-finding ai-finding--${f.color}`}>
                  <div className={`ai-finding-icon ai-finding-icon--${f.color}`}>
                    <Icon size={13} strokeWidth={1.8} />
                  </div>
                  <div className="ai-finding-body">
                    <span className="ai-finding-label">{f.label}</span>
                    <span className="ai-finding-value">{f.value}</span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Sequence visual */}
          <div className="ai-sequence">
            <span className="ai-seq-label">Detected Sequence</span>
            <div className="ai-seq-chain">
              {['Physical Access', 'System Login', 'USB Device', 'File Access', 'Exfiltration'].map((s, i) => (
                <div key={i} className="ai-seq-chain-item">
                  <div className={`ai-seq-node ${i >= 2 ? 'ai-seq-node--alert' : ''}`}>{i + 1}</div>
                  <span className="ai-seq-step">{s}</span>
                  {i < 4 && <ChevronRight size={12} className="ai-seq-arrow" />}
                </div>
              ))}
            </div>
          </div>

          {/* IOC summary */}
          <div className="ai-ioc-block">
            <span className="ai-ioc-title">Key IOCs Identified</span>
            <div className="ai-ioc-list">
              <div className="ai-ioc-item">
                <span className="ai-ioc-type">IP</span>
                <span className="ai-ioc-val">185.220.101.47</span>
                <span className="badge badge--critical" style={{ fontSize: 9 }}>TOR</span>
              </div>
              <div className="ai-ioc-item">
                <span className="ai-ioc-type">USER</span>
                <span className="ai-ioc-val">jsmith@corp.int</span>
                <span className="badge badge--high" style={{ fontSize: 9 }}>HIGH RISK</span>
              </div>
              <div className="ai-ioc-item">
                <span className="ai-ioc-type">DEVICE</span>
                <span className="ai-ioc-val">SDCZ48-128G</span>
                <span className="badge badge--medium" style={{ fontSize: 9 }}>UNREGISTERED</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="ai-actions">
            <button className="ai-btn ai-btn--primary" id="view-investigation-btn"
              onClick={() => navigate('/investigations/CASE-2026-001/workspace')}>
              <Eye size={14} />
              View Investigation
            </button>
            <button className="ai-btn ai-btn--secondary" id="review-findings-btn"
              onClick={() => navigate('/investigations/CASE-2026-001')}>
              <Search size={14} />
              Review Findings
            </button>
          </div>

          <div className="ai-disclaimer">
            <Brain size={10} />
            Analysis generated by NEXUS-7 · Last run: {new Date().toLocaleTimeString()} · Model: SynapseX-Forge-v3
          </div>
        </div>

      </div>
    </div>
  )
}
