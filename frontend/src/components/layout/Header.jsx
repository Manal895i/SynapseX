import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Menu,
  PanelLeftClose,
  PanelLeft,
  Bell,
  Search,
  ChevronDown,
  Clock,
  Wifi,
  Shield,
  AlertTriangle,
} from 'lucide-react'
import './Header.css'

const PAGE_TITLES = {
  '/dashboard':           { title: 'Dashboard',           subtitle: 'System overview & active intelligence' },
  '/investigations':      { title: 'Investigations',      subtitle: 'Active & archived case management' },
  '/evidence':            { title: 'Evidence',            subtitle: 'Digital evidence repository & chain of custody' },
  '/live-investigation':  { title: 'Live Investigation',  subtitle: 'Real-time monitoring & active session', live: true },
  '/timeline':            { title: 'Timeline',            subtitle: 'Chronological event reconstruction' },
  '/knowledge-graph':     { title: 'Knowledge Graph',     subtitle: 'Entity relationship visualization' },
  '/ai-agents':           { title: 'AI Agents',           subtitle: 'Autonomous analysis agent fleet' },
  '/ai-findings':         { title: 'AI Findings & Reasoning', subtitle: 'Explainable evidence-backed hypothesis synthesis' },
  '/intelligence-chat':   { title: 'Intelligence Chat',   subtitle: 'AI-assisted investigation dialogue' },
  '/reports':             { title: 'Reports',             subtitle: 'Forensic reports & export management' },
  '/chain-of-custody':    { title: 'Chain of Custody',    subtitle: 'Evidence integrity & custody log' },
  '/settings':            { title: 'Settings',            subtitle: 'Platform configuration & preferences' },
}

// Mock alerts for the notification badge
const ALERT_COUNT = 3

function LiveClock() {
  const [time, setTime] = useState(() => new Date())

  useState(() => {
    const interval = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(interval)
  })

  return (
    <div className="header-clock">
      <Clock size={12} />
      <span>{time.toUTCString().slice(17, 25)}</span>
      <span className="clock-label">UTC</span>
    </div>
  )
}

export default function Header({ collapsed, onToggleSidebar, onMobileMenu, onOpenSearch }) {
  const { pathname } = useLocation()
  const page = PAGE_TITLES[pathname] || { title: 'SynapseX', subtitle: 'Autonomous Digital Evidence Intelligence Platform' }
  const [searchFocused, setSearchFocused] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)

  return (
    <header className="app-header">
      {/* ── Left: toggle + page title ── */}
      <div className="header-left">
        {/* Desktop collapse toggle */}
        <button
          className="header-btn header-toggle desktop-only"
          onClick={onToggleSidebar}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
        </button>

        {/* Mobile hamburger */}
        <button
          className="header-btn header-toggle mobile-only"
          onClick={onMobileMenu}
          aria-label="Open navigation"
        >
          <Menu size={16} />
        </button>

        <div className="header-divider" />

        <div className="header-page-info">
          <div className="header-page-title-row">
            <h1 className="header-page-title">{page.title}</h1>
            {page.live && (
              <span className="header-live-badge">
                <span className="pulse-dot pulse-dot--alert" />
                LIVE
              </span>
            )}
          </div>
          <p className="header-page-subtitle">{page.subtitle}</p>
        </div>
      </div>

      {/* ── Center: Search ── */}
      <div 
        className={`header-search-wrap ${searchFocused ? 'focused' : ''}`}
        onClick={onOpenSearch}
      >
        <Search size={13} className="search-icon" />
        <input
          id="global-search"
          type="text"
          placeholder="Search cases, evidence, entities... (⌘K)"
          className="header-search"
          readOnly
          onClick={onOpenSearch}
          aria-label="Global search (Press ⌘K to search)"
        />
        <span className="search-kbd" onClick={onOpenSearch}>⌘K</span>
      </div>

      {/* ── Right: status + actions ── */}
      <div className="header-right">
        {/* System status indicators */}
        <div className="header-indicators desktop-only">
          <div className="indicator" title="Network connected">
            <Wifi size={13} className="indicator-icon indicator-icon--green" />
          </div>
          <div className="indicator" title="TLS Encrypted">
            <Shield size={13} className="indicator-icon indicator-icon--blue" />
          </div>
          <div className="indicator indicator--alert" title="3 active alerts">
            <AlertTriangle size={13} className="indicator-icon indicator-icon--alert" />
            <span className="indicator-count">3</span>
          </div>
        </div>

        <div className="header-divider desktop-only" />

        {/* Clock */}
        <LiveClock />

        <div className="header-divider desktop-only" />

        {/* Notifications */}
        <div className="header-notif-wrap">
          <button
            className="header-btn header-notif-btn"
            onClick={() => setNotifOpen(o => !o)}
            aria-label="Notifications"
            id="notifications-btn"
          >
            <Bell size={15} />
            {ALERT_COUNT > 0 && (
              <span className="notif-badge">{ALERT_COUNT}</span>
            )}
          </button>

          {notifOpen && (
            <div className="notif-dropdown">
              <div className="notif-header">
                <span className="notif-title">Alerts</span>
                <span className="badge badge--critical">{ALERT_COUNT} active</span>
              </div>
              {[
                { level: 'critical', msg: 'Anomalous exfiltration pattern detected in CASE-2024-0047', time: '2m ago' },
                { level: 'high',    msg: 'New entity correlation found — suspect network node', time: '14m ago' },
                { level: 'medium',  msg: 'Evidence hash mismatch on artifact EVD-0821', time: '1h ago' },
              ].map((n, i) => (
                <div key={i} className={`notif-item notif-item--${n.level}`}>
                  <div className="notif-dot" />
                  <div className="notif-body">
                    <p className="notif-msg">{n.msg}</p>
                    <span className="notif-time">{n.time}</span>
                  </div>
                </div>
              ))}
              <div className="notif-footer">View all alerts →</div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <button className="header-user-btn" id="user-menu-btn" aria-label="User menu">
          <div className="header-avatar">SA</div>
          <div className="header-user-info desktop-only">
            <span className="header-user-name">Sr. Analyst</span>
            <span className="header-user-role">TS/SCI</span>
          </div>
          <ChevronDown size={12} className="desktop-only" style={{ color: 'var(--gray-500)' }} />
        </button>
      </div>
    </header>
  )
}
