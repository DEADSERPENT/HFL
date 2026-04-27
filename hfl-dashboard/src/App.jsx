import { useState } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  LayoutDashboard, FlaskConical, Wrench, Settings, Rocket, Cpu, BarChart3,
  Menu, X, FileText, Database, Sparkles, Layers, Network, Brain
} from 'lucide-react'
import Phase1 from './pages/Phase1.jsx'
import Phase2 from './pages/Phase2.jsx'
import Phase3 from './pages/Phase3.jsx'
import Phase4 from './pages/Phase4.jsx'
import Phase5 from './pages/Phase5.jsx'
import Phase6 from './pages/Phase6.jsx'
import Overview from './pages/Overview.jsx'
import ProjectReport from './pages/ProjectReport.jsx'
import Datasets from './pages/Datasets.jsx'
import PhantomFL from './pages/PhantomFL.jsx'
import ModelDesign from './pages/ModelDesign.jsx'
import NS3Integration from './pages/NS3Integration.jsx'
import IPNovelty from './pages/IPNovelty.jsx'

const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } }
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const closeSidebar = () => setSidebarOpen(false)

  return (
    <div className="app-layout">
      {/* Mobile Menu */}
      <button className="mobile-menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle menu">
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>
      <div className={`mobile-overlay ${sidebarOpen ? 'active' : ''}`} onClick={closeSidebar} />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <NavLink to="/" className="sidebar-logo" onClick={closeSidebar}>
            <div className="sidebar-logo-icon">HFL</div>
            <div className="sidebar-logo-text">
              <h1>HFL Research</h1>
              <span>Dashboard</span>
            </div>
          </NavLink>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Navigation</div>
          <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><LayoutDashboard size={18} /></span>
            Overview
          </NavLink>
          <NavLink to="/report" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><FileText size={18} /></span>
            Project Report
          </NavLink>

          <div className="nav-section-title">Research Phases</div>
          <NavLink to="/phase1" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><FlaskConical size={18} /></span>
            Phase 1 — Research & Planning
            <span className="nav-badge">Done</span>
          </NavLink>
          <NavLink to="/phase2" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Wrench size={18} /></span>
            Phase 2 — Simulator Design
            <span className="nav-badge">Done</span>
          </NavLink>
          <NavLink to="/phase3" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Settings size={18} /></span>
            Phase 3 — Environment Setup
            <span className="nav-badge">Done</span>
          </NavLink>
          <NavLink to="/phase4" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Rocket size={18} /></span>
            Phase 4 — Implementation
            <span className="nav-badge">Done</span>
          </NavLink>
          <NavLink to="/phase5" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Cpu size={18} /></span>
            Phase 5 — Healthcare Model
            <span className="nav-badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B' }}>In Progress</span>
          </NavLink>
          <NavLink to="/phase6" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><BarChart3 size={18} /></span>
            Phase 6 — Evaluation & Paper
            <span className="nav-badge" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }}>Planned</span>
          </NavLink>

          <div className="nav-section-title">Documentation</div>
          <NavLink to="/datasets" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Database size={18} /></span>
            Datasets Guide
          </NavLink>
          <NavLink to="/model-design" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Layers size={18} /></span>
            Model Design
          </NavLink>
          <NavLink to="/phantom-fl" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Sparkles size={18} /></span>
            PHANTOM-FL Model
          </NavLink>
          <NavLink to="/ns3-integration" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Network size={18} /></span>
            NS-3 & CloudSim
          </NavLink>
          <NavLink to="/ip-novelty" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={closeSidebar}>
            <span className="nav-icon"><Brain size={18} /></span>
            IP & Novelty Register
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-footer-info">
            <strong>Samartha H V</strong><br />
            MIT Bengaluru · 251580130019<br />
            Guide: Dr. Shreyas J
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <Routes location={location}>
              <Route path="/" element={<Overview />} />
              <Route path="/report" element={<ProjectReport />} />
              <Route path="/phase1" element={<Phase1 />} />
              <Route path="/phase2" element={<Phase2 />} />
              <Route path="/phase3" element={<Phase3 />} />
              <Route path="/phase4" element={<Phase4 />} />
              <Route path="/phase5" element={<Phase5 />} />
              <Route path="/phase6" element={<Phase6 />} />
              <Route path="/datasets" element={<Datasets />} />
              <Route path="/model-design" element={<ModelDesign />} />
              <Route path="/phantom-fl" element={<PhantomFL />} />
              <Route path="/ns3-integration" element={<NS3Integration />} />
              <Route path="/ip-novelty" element={<IPNovelty />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}

export default App
