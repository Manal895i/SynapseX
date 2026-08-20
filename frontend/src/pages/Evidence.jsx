import { useState, useRef, useCallback } from 'react'
import {
  Upload, HardDrive, Shield, CheckCircle2,
  Clock, Search, Filter, Download, X,
  FileVideo, FileText, Network, Usb,
  AlertTriangle, ChevronRight, Eye,
  Hash, Database, GitBranch, Brain,
  Loader2, Lock, SlidersHorizontal,
  FileBadge, CloudUpload, Activity,
  ArrowUpDown, ChevronDown, ChevronUp,
  MoreHorizontal, Clipboard, Star,
} from 'lucide-react'
import './Evidence.css'

/* ═══════════════════════════════════════
   MOCK DATA
═══════════════════════════════════════ */
const EVIDENCE_ITEMS = [
  {
    id: 'E-001',
    fileName: 'cctv_camera_01.mp4',
    type: 'Video Evidence',
    typeKey: 'video',
    source: 'Security Camera CAM-07',
    caseId: 'CASE-2026-001',
    sha256: 'a3f1d82c4b7e9f20c1d456a8b3e7f1d9a2c4b6e8f0d2a4c6b8e0f2a4c6b8e0f2',
    size: '2.1 GB',
    uploadTime: '2026-08-20 10:00:14 UTC',
    collectedBy: 'Demo Investigator',
    collectionMethod: 'Physical extraction',
    processingStatus: 'verified',
    flagged: true,
    custodyChain: [
      { action: 'Collected',   by: 'Demo Investigator', time: '2026-08-20 09:55 UTC', note: 'Retrieved from CAM-07 DVR' },
      { action: 'Uploaded',    by: 'Demo Investigator', time: '2026-08-20 10:00 UTC', note: 'Ingested into SynapseX vault' },
      { action: 'Hashed',      by: 'SynapseX System',   time: '2026-08-20 10:01 UTC', note: 'SHA-256 computed and sealed' },
      { action: 'Analyzed',    by: 'NEXUS-7 Agent',     time: '2026-08-20 10:14 UTC', note: 'AI frame analysis complete' },
    ],
    aiEvents: [
      { time: '10:02:14', label: 'Person entered server room — unrecognized face', type: 'critical' },
      { time: '10:02:47', label: 'Tail-gate event — second person follows without badge scan', type: 'suspicious' },
      { time: '10:09:33', label: 'Person exits with external storage device visible', type: 'critical' },
    ],
  },
  {
    id: 'E-002',
    fileName: 'windows_event_logs.evtx',
    type: 'System Logs',
    typeKey: 'logs',
    source: 'Workstation WKST-041',
    caseId: 'CASE-2026-001',
    sha256: 'b8c3e1f4d7a0b2e5f8c1d4a7b0e3f6c9d2a5b8e1f4c7d0a3b6e9f2c5d8a1b4e7',
    size: '48 MB',
    uploadTime: '2026-08-20 10:05:30 UTC',
    collectedBy: 'J. Ramirez',
    collectionMethod: 'Remote acquisition',
    processingStatus: 'verified',
    flagged: false,
    custodyChain: [
      { action: 'Collected',   by: 'J. Ramirez',        time: '2026-08-20 10:02 UTC', note: 'Pulled via remote forensic agent' },
      { action: 'Uploaded',    by: 'J. Ramirez',        time: '2026-08-20 10:05 UTC', note: 'Transferred to evidence vault' },
      { action: 'Hashed',      by: 'SynapseX System',   time: '2026-08-20 10:05 UTC', note: 'SHA-256 verified' },
      { action: 'Analyzed',    by: 'ARGUS-5 Agent',     time: '2026-08-20 10:20 UTC', note: '4,812 events parsed' },
    ],
    aiEvents: [
      { time: '10:04:02', label: 'User jsmith@corp.int authenticated — Event ID 4624', type: 'normal' },
      { time: '10:04:18', label: 'Privilege escalation attempt — Event ID 4672', type: 'suspicious' },
      { time: '10:07:44', label: 'Bulk file read operation initiated — 34 files', type: 'critical' },
    ],
  },
  {
    id: 'E-003',
    fileName: 'firewall_egress_logs.csv',
    type: 'Network Evidence',
    typeKey: 'network',
    source: 'Palo Alto FW-CORE-01',
    caseId: 'CASE-2026-001',
    sha256: 'c9d4f2a6b8e1c3d5f7a9b2e4c6d8f0a2b4e6c8d0f2a4b6e8c0d2f4a6b8e0c2d4',
    size: '8.3 MB',
    uploadTime: '2026-08-20 10:12:00 UTC',
    collectedBy: 'SynapseX System',
    collectionMethod: 'Automated SIEM export',
    processingStatus: 'processing',
    flagged: true,
    custodyChain: [
      { action: 'Collected',   by: 'SIEM Connector',    time: '2026-08-20 10:10 UTC', note: 'Auto-exported via SIEM API' },
      { action: 'Uploaded',    by: 'SynapseX System',   time: '2026-08-20 10:12 UTC', note: 'Ingested to evidence vault' },
      { action: 'Hashing',     by: 'SynapseX System',   time: '2026-08-20 10:12 UTC', note: 'SHA-256 computation in progress' },
    ],
    aiEvents: [
      { time: '10:09:12', label: '1.8 GB outbound to 185.220.101.47 — TOR exit node', type: 'critical' },
      { time: '10:09:33', label: 'DNS query for .onion domain resolved', type: 'critical' },
    ],
  },
  {
    id: 'E-004',
    fileName: 'usb_activity_log.csv',
    type: 'Device Activity',
    typeKey: 'device',
    source: 'Endpoint WKST-041',
    caseId: 'CASE-2026-001',
    sha256: 'd0e5a3c7b9f2d4e6a8c0b2d4f6a8c0b2d4f6a8c0b2d4f6a8c0b2d4f6a8c0b2d4',
    size: '124 KB',
    uploadTime: '2026-08-20 10:08:00 UTC',
    collectedBy: 'Demo Investigator',
    collectionMethod: 'EDR platform export',
    processingStatus: 'verified',
    flagged: true,
    custodyChain: [
      { action: 'Collected',   by: 'Demo Investigator', time: '2026-08-20 10:06 UTC', note: 'Exported from CrowdStrike EDR' },
      { action: 'Uploaded',    by: 'Demo Investigator', time: '2026-08-20 10:08 UTC', note: 'Uploaded to SynapseX vault' },
      { action: 'Hashed',      by: 'SynapseX System',   time: '2026-08-20 10:08 UTC', note: 'Integrity hash sealed' },
      { action: 'Analyzed',    by: 'CIPHER-3 Agent',    time: '2026-08-20 10:22 UTC', note: 'USB device fingerprinting complete' },
    ],
    aiEvents: [
      { time: '10:05:06', label: 'Unregistered USB device inserted — SDCZ48-128G', type: 'critical' },
      { time: '10:05:22', label: '2.1 GB write operation started', type: 'critical' },
      { time: '10:08:54', label: 'USB device safely removed', type: 'suspicious' },
    ],
  },
  {
    id: 'E-005',
    fileName: 'memory_dump_wkst041.raw',
    type: 'Memory Dump',
    typeKey: 'memory',
    source: 'Workstation WKST-041',
    caseId: 'CASE-2026-001',
    sha256: 'e1f6b4d8c2a5e7f9b3d5a7c9e1b3d5f7a9c1e3b5d7f9a1c3e5b7d9f1a3c5e7b9',
    size: '16 GB',
    uploadTime: '2026-08-20 11:30:00 UTC',
    collectedBy: 'J. Ramirez',
    collectionMethod: 'Live memory acquisition',
    processingStatus: 'queued',
    flagged: false,
    custodyChain: [
      { action: 'Collected',   by: 'J. Ramirez',        time: '2026-08-20 11:00 UTC', note: 'Live RAM dump via Rekall' },
      { action: 'Uploaded',    by: 'J. Ramirez',        time: '2026-08-20 11:30 UTC', note: 'Transferred to vault' },
      { action: 'Queued',      by: 'SynapseX System',   time: '2026-08-20 11:31 UTC', note: 'Awaiting analysis queue' },
    ],
    aiEvents: [],
  },
  {
    id: 'E-006',
    fileName: 'network_capture.pcap',
    type: 'PCAP Capture',
    typeKey: 'network',
    source: 'Network TAP — Switch-Core',
    caseId: 'CASE-2026-001',
    sha256: 'f2a7c5e9d3b6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8',
    size: '4.7 GB',
    uploadTime: '2026-08-20 10:30:00 UTC',
    collectedBy: 'SynapseX System',
    collectionMethod: 'Network TAP continuous capture',
    processingStatus: 'verified',
    flagged: true,
    custodyChain: [
      { action: 'Collected',   by: 'Network TAP',       time: '2026-08-20 09:00 UTC', note: 'Continuous capture during window' },
      { action: 'Uploaded',    by: 'SynapseX System',   time: '2026-08-20 10:30 UTC', note: 'Trimmed to incident window' },
      { action: 'Hashed',      by: 'SynapseX System',   time: '2026-08-20 10:31 UTC', note: 'SHA-256 sealed' },
      { action: 'Analyzed',    by: 'CIPHER-3 Agent',    time: '2026-08-20 11:00 UTC', note: 'TLS session analysis complete' },
    ],
    aiEvents: [
      { time: '10:09:10', label: 'TLS 1.3 session to 185.220.101.47:443 established', type: 'critical' },
      { time: '10:09:15', label: '1.8 GB payload transferred in encrypted stream', type: 'critical' },
      { time: '10:11:02', label: 'Session terminated from remote side', type: 'suspicious' },
    ],
  },
]

const FILE_TYPE_ICONS = {
  video:   FileVideo,
  logs:    FileText,
  network: Network,
  device:  Usb,
  memory:  Database,
  default: HardDrive,
}

const STATUS_META = {
  verified:   { label: 'Verified',   cls: 'verified',   icon: CheckCircle2 },
  processing: { label: 'Processing', cls: 'processing', icon: Loader2      },
  queued:     { label: 'Queued',     cls: 'queued',     icon: Clock        },
  failed:     { label: 'Failed',     cls: 'failed',     icon: AlertTriangle},
}

const SUPPORTED_TYPES = [
  'Disk Images (.E01, .dd)',
  'PCAP Files (.pcap, .pcapng)',
  'System Logs (.evtx, .log)',
  'Documents (.pdf, .docx)',
  'Spreadsheets (.csv, .xlsx)',
  'Video (.mp4, .avi, .mkv)',
  'Memory Dumps (.raw, .mem)',
  'JSON / XML / YAML',
]

/* ═══════════════════════════════════════
   DRAG-DROP UPLOAD ZONE
═══════════════════════════════════════ */
function UploadZone({ onUpload }) {
  const [dragging, setDragging]   = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress]   = useState(0)
  const inputRef = useRef()

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const files = [...e.dataTransfer.files]
    if (files.length) simulateUpload(files)
  }, [])

  const handleFileSelect = (e) => {
    const files = [...e.target.files]
    if (files.length) simulateUpload(files)
  }

  function simulateUpload(files) {
    setUploading(true)
    setProgress(0)
    let p = 0
    const t = setInterval(() => {
      p += Math.random() * 18
      if (p >= 100) {
        p = 100
        clearInterval(t)
        setTimeout(() => { setUploading(false); setProgress(0) }, 800)
      }
      setProgress(Math.min(Math.round(p), 100))
    }, 180)
  }

  return (
    <div
      className={`ev-upload-zone ${dragging ? 'ev-upload-zone--drag' : ''} ${uploading ? 'ev-upload-zone--uploading' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      id="evidence-upload-zone"
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        className="ev-upload-input"
        onChange={handleFileSelect}
        accept=".pcap,.pcapng,.evtx,.log,.csv,.json,.xml,.mp4,.avi,.E01,.dd,.raw,.mem,.pdf,.docx,.xlsx"
      />

      {/* Animated grid bg */}
      <div className="ev-upload-grid" />

      {uploading ? (
        <div className="ev-upload-progress-wrap">
          <div className="ev-upload-spinner"><Loader2 size={28} className="ev-spin"/></div>
          <p className="ev-upload-prog-title">Processing Evidence</p>
          <p className="ev-upload-prog-sub">Computing SHA-256 · Cataloguing artifact · Sealing chain of custody</p>
          <div className="ev-upload-bar-wrap">
            <div className="ev-upload-bar" style={{ width: `${progress}%` }} />
          </div>
          <span className="ev-upload-pct">{progress}%</span>
        </div>
      ) : (
        <>
          <div className={`ev-upload-icon-wrap ${dragging ? 'ev-upload-icon-wrap--drag' : ''}`}>
            <CloudUpload size={40} strokeWidth={1.4} className="ev-upload-icon" />
            <div className="ev-upload-icon-ring" />
          </div>
          <div className="ev-upload-text">
            <h3 className="ev-upload-title">
              {dragging ? 'Release to Upload Evidence' : 'Upload Investigation Evidence'}
            </h3>
            <p className="ev-upload-sub">
              Drag & drop files here, or <span className="ev-upload-link">browse to select</span>
            </p>
          </div>
          <div className="ev-upload-types">
            {SUPPORTED_TYPES.map(t => (
              <span key={t} className="ev-upload-type-chip">{t}</span>
            ))}
          </div>
          <div className="ev-upload-footer">
            <Lock size={11} />
            <span>All uploads are SHA-256 hashed, encrypted at rest, and sealed with chain of custody</span>
          </div>
        </>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════
   SIDE PANEL
═══════════════════════════════════════ */
function EvidencePanel({ item, onClose }) {
  const [copiedHash, setCopiedHash] = useState(false)
  const TypeIcon = FILE_TYPE_ICONS[item.typeKey] || FILE_TYPE_ICONS.default
  const st = STATUS_META[item.processingStatus] || STATUS_META.queued
  const StatusIcon = st.icon

  function copyHash() {
    navigator.clipboard.writeText(item.sha256).catch(() => {})
    setCopiedHash(true)
    setTimeout(() => setCopiedHash(false), 2000)
  }

  return (
    <div className="ev-panel" id="evidence-side-panel">
      {/* Panel header */}
      <div className="ev-panel-header">
        <div className="ev-panel-title-row">
          <div className={`ev-panel-type-icon ev-panel-type-icon--${item.typeKey}`}>
            <TypeIcon size={18} strokeWidth={1.6} />
          </div>
          <div className="ev-panel-title-text">
            <span className="ev-panel-id">{item.id}</span>
            <h3 className="ev-panel-filename">{item.fileName}</h3>
          </div>
        </div>
        <button className="ev-panel-close" onClick={onClose} aria-label="Close panel">
          <X size={16} />
        </button>
      </div>

      <div className="ev-panel-body">

        {/* Status + flags */}
        <div className="ev-panel-status-row">
          <span className={`ev-status-badge ev-status-badge--${st.cls}`}>
            <StatusIcon size={11} className={item.processingStatus === 'processing' ? 'ev-spin' : ''} />
            {st.label}
          </span>
          {item.flagged && (
            <span className="ev-panel-flagged">
              <AlertTriangle size={11}/> Flagged — Contains suspicious activity
            </span>
          )}
        </div>

        {/* File Info */}
        <div className="ev-panel-section">
          <span className="ev-panel-section-title"><HardDrive size={13}/> File Information</span>
          <div className="ev-panel-grid">
            {[
              { label: 'Evidence Type', value: item.type },
              { label: 'File Size',     value: item.size },
              { label: 'Source',        value: item.source },
              { label: 'Collection',    value: item.collectionMethod },
              { label: 'Collected By',  value: item.collectedBy },
              { label: 'Upload Time',   value: item.uploadTime },
            ].map(m => (
              <div key={m.label} className="ev-panel-meta">
                <span className="ev-panel-meta-label">{m.label}</span>
                <span className="ev-panel-meta-value">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Hash */}
        <div className="ev-panel-section">
          <span className="ev-panel-section-title"><Hash size={13}/> Integrity Hash</span>
          <div className="ev-hash-block">
            <div className="ev-hash-label-row">
              <span className="ev-hash-algo">SHA-256</span>
              <span className={`ev-hash-status ${item.processingStatus === 'verified' ? 'ev-hash-status--ok' : ''}`}>
                {item.processingStatus === 'verified' ? <><CheckCircle2 size={11}/> Verified</> : 'Pending'}
              </span>
            </div>
            <div className="ev-hash-val-row">
              <code className="ev-hash-val">{item.sha256}</code>
              <button className="ev-hash-copy" onClick={copyHash} title="Copy hash">
                {copiedHash ? <CheckCircle2 size={13}/> : <Clipboard size={13}/>}
              </button>
            </div>
          </div>
        </div>

        {/* Chain of Custody */}
        <div className="ev-panel-section">
          <span className="ev-panel-section-title"><GitBranch size={13}/> Chain of Custody</span>
          <div className="ev-custody-list">
            {item.custodyChain.map((c, i) => (
              <div key={i} className="ev-custody-item">
                <div className="ev-custody-left">
                  <div className={`ev-custody-dot ${i === 0 ? 'ev-custody-dot--first' : ''}`} />
                  {i < item.custodyChain.length - 1 && <div className="ev-custody-line" />}
                </div>
                <div className="ev-custody-body">
                  <div className="ev-custody-action-row">
                    <span className="ev-custody-action">{c.action}</span>
                    <span className="ev-custody-by">— {c.by}</span>
                  </div>
                  <p className="ev-custody-note">{c.note}</p>
                  <span className="ev-custody-time">{c.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Extracted Events */}
        <div className="ev-panel-section">
          <span className="ev-panel-section-title"><Brain size={13}/> AI Extracted Events</span>
          {item.aiEvents.length === 0 ? (
            <div className="ev-ai-empty">
              <Clock size={14}/>
              <span>Analysis queued — no events extracted yet</span>
            </div>
          ) : (
            <div className="ev-ai-events">
              {item.aiEvents.map((ev, i) => (
                <div key={i} className={`ev-ai-event ev-ai-event--${ev.type}`}>
                  <div className={`ev-ai-dot ev-ai-dot--${ev.type}`} />
                  <div className="ev-ai-body">
                    <span className="ev-ai-time">{ev.time}</span>
                    <p className="ev-ai-label">{ev.label}</p>
                  </div>
                  {ev.type === 'critical' && (
                    <span className="ev-ai-flag"><AlertTriangle size={9}/> SUSPICIOUS</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="ev-panel-actions">
          <button className="ev-panel-btn ev-panel-btn--primary" id={`download-ev-${item.id}`}>
            <Download size={13}/> Download Evidence
          </button>
          <button className="ev-panel-btn ev-panel-btn--ghost" id={`analyze-ev-${item.id}`}>
            <Brain size={13}/> Run AI Analysis
          </button>
        </div>

      </div>
    </div>
  )
}

/* ═══════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════ */
export default function Evidence() {
  const [search,      setSearch]      = useState('')
  const [statusFilter, setStatus]     = useState('all')
  const [typeFilter,   setType]       = useState('all')
  const [selectedItem, setSelected]   = useState(null)
  const [sortField,    setSortField]  = useState('id')
  const [sortDir,      setSortDir]    = useState('asc')

  function toggleSort(field) {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(field); setSortDir('asc') }
  }

  const filtered = EVIDENCE_ITEMS
    .filter(e => {
      const q = search.toLowerCase()
      if (q && !e.id.toLowerCase().includes(q) &&
               !e.fileName.toLowerCase().includes(q) &&
               !e.source.toLowerCase().includes(q) &&
               !e.type.toLowerCase().includes(q)) return false
      if (statusFilter !== 'all' && e.processingStatus !== statusFilter) return false
      if (typeFilter !== 'all' && e.typeKey !== typeFilter) return false
      return true
    })
    .sort((a, b) => {
      let va = a[sortField], vb = b[sortField]
      if (va < vb) return sortDir === 'asc' ? -1 : 1
      if (va > vb) return sortDir === 'asc' ?  1 : -1
      return 0
    })

  function SortIcon({ field }) {
    if (sortField !== field) return <ArrowUpDown size={11} className="ev-sort-idle" />
    return sortDir === 'asc' ? <ChevronUp size={11} className="ev-sort-active" /> : <ChevronDown size={11} className="ev-sort-active" />
  }

  return (
    <div className={`ev-root ${selectedItem ? 'ev-root--panel-open' : ''}`}>

      {/* ── Page header ── */}
      <div className="ev-page-header">
        <div className="ev-header-left">
          <div className="ev-eyebrow"><HardDrive size={12}/> Evidence Management</div>
          <h1 className="ev-page-title">Evidence Vault</h1>
          <p className="ev-page-sub">
            CASE-2026-001 · {EVIDENCE_ITEMS.length} artifacts · {EVIDENCE_ITEMS.filter(e=>e.processingStatus==='verified').length} verified
          </p>
        </div>
        <div className="ev-header-right">
          <button className="ev-hdr-btn ev-hdr-btn--ghost"><Download size={14}/> Export Manifest</button>
          <button className="ev-hdr-btn ev-hdr-btn--primary"><Upload size={14}/> Upload Evidence</button>
        </div>
      </div>

      {/* ── Drag-drop upload ── */}
      <UploadZone />

      {/* ── Stats row ── */}
      <div className="ev-stats-row">
        {[
          { label: 'Total Evidence',   value: EVIDENCE_ITEMS.length, color: 'blue'  },
          { label: 'Verified',         value: EVIDENCE_ITEMS.filter(e=>e.processingStatus==='verified').length, color: 'green' },
          { label: 'Processing',       value: EVIDENCE_ITEMS.filter(e=>e.processingStatus==='processing').length, color: 'amber' },
          { label: 'Queued',           value: EVIDENCE_ITEMS.filter(e=>e.processingStatus==='queued').length, color: 'gray' },
          { label: 'Flagged',          value: EVIDENCE_ITEMS.filter(e=>e.flagged).length, color: 'red' },
          { label: 'Total Size',       value: '23.2 GB', color: 'cyan' },
        ].map(s => (
          <div key={s.label} className={`ev-stat ev-stat--${s.color}`}>
            <span className="ev-stat-value">{s.value}</span>
            <span className="ev-stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      {/* ── Inventory section ── */}
      <div className="ev-inventory">

        {/* Toolbar */}
        <div className="ev-toolbar">
          <div className="ev-search-wrap">
            <Search size={13} className="ev-search-icon"/>
            <input
              id="evidence-search"
              type="text"
              placeholder="Search by ID, filename, source, type…"
              className="ev-search"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && <button className="ev-search-clear" onClick={() => setSearch('')}><X size={11}/></button>}
          </div>

          <div className="ev-filter-tabs">
            {['all','verified','processing','queued'].map(s => (
              <button
                key={s}
                id={`status-tab-${s}`}
                className={`ev-filter-tab ${statusFilter === s ? 'ev-filter-tab--active' : ''}`}
                onClick={() => setStatus(s)}
              >
                {s === 'all' ? 'All' : STATUS_META[s]?.label || s}
              </button>
            ))}
          </div>

          <select id="type-filter" className="ev-select" value={typeFilter} onChange={e=>setType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="video">Video</option>
            <option value="logs">System Logs</option>
            <option value="network">Network</option>
            <option value="device">Device Activity</option>
            <option value="memory">Memory Dump</option>
          </select>

          <span className="ev-result-count">{filtered.length} items</span>
        </div>

        {/* Table */}
        <div className="ev-table-wrap">
          <table className="ev-table">
            <thead>
              <tr>
                <th onClick={()=>toggleSort('id')}          className="ev-th-sort">Evidence ID <SortIcon field="id"/></th>
                <th onClick={()=>toggleSort('fileName')}    className="ev-th-sort">File Name <SortIcon field="fileName"/></th>
                <th>Type</th>
                <th onClick={()=>toggleSort('source')}      className="ev-th-sort">Source <SortIcon field="source"/></th>
                <th>SHA-256 Integrity</th>
                <th onClick={()=>toggleSort('uploadTime')}  className="ev-th-sort">Upload Time <SortIcon field="uploadTime"/></th>
                <th>Processing Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="ev-empty-row">
                    <Search size={18}/> No evidence matches your filters
                  </td>
                </tr>
              )}
              {filtered.map((item, idx) => {
                const TypeIcon = FILE_TYPE_ICONS[item.typeKey] || FILE_TYPE_ICONS.default
                const st = STATUS_META[item.processingStatus] || STATUS_META.queued
                const StatusIcon = st.icon
                const isSelected = selectedItem?.id === item.id

                return (
                  <tr
                    key={item.id}
                    className={`ev-row ${isSelected ? 'ev-row--selected' : ''} ${item.flagged ? 'ev-row--flagged' : ''}`}
                    onClick={() => setSelected(isSelected ? null : item)}
                    id={`ev-row-${item.id}`}
                    style={{ animationDelay: `${idx * 40}ms` }}
                  >
                    <td>
                      <div className="ev-cell-id">
                        <span className="ev-item-id">{item.id}</span>
                        {item.flagged && <AlertTriangle size={11} className="ev-flagged-icon"/>}
                      </div>
                    </td>
                    <td>
                      <div className="ev-cell-file">
                        <div className={`ev-file-icon ev-file-icon--${item.typeKey}`}>
                          <TypeIcon size={13} strokeWidth={1.8}/>
                        </div>
                        <div className="ev-file-name-wrap">
                          <span className="ev-file-name">{item.fileName}</span>
                          <span className="ev-file-size">{item.size}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`ev-type-chip ev-type-chip--${item.typeKey}`}>{item.type}</span>
                    </td>
                    <td>
                      <span className="ev-source">{item.source}</span>
                    </td>
                    <td>
                      <div className="ev-hash-cell">
                        <Hash size={11} className="ev-hash-icon"/>
                        <code className="ev-hash-short">{item.sha256.slice(0, 16)}…</code>
                        {item.processingStatus === 'verified' && (
                          <CheckCircle2 size={11} className="ev-hash-ok"/>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="ev-time-cell">
                        <Clock size={11}/>
                        <span>{item.uploadTime.slice(0, 16)}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`ev-status ev-status--${st.cls}`}>
                        <StatusIcon size={10} className={item.processingStatus === 'processing' ? 'ev-spin' : ''}/>
                        {st.label}
                      </span>
                    </td>
                    <td>
                      <div className="ev-row-actions">
                        <button className="ev-row-btn" onClick={e=>{e.stopPropagation();setSelected(item)}} title="View details">
                          <Eye size={13}/>
                        </button>
                        <ChevronRight size={13} className={`ev-row-arrow ${isSelected ? 'ev-row-arrow--open' : ''}`}/>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

      </div>

      {/* ── Side Panel ── */}
      {selectedItem && (
        <EvidencePanel item={selectedItem} onClose={() => setSelected(null)} />
      )}

    </div>
  )
}
