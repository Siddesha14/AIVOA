import ChatPanel from './components/CoPilot/ChatPanel'
import InvestigationForm from './components/Form/InvestigationForm'
import './App.css'

function App() {
  return (
    <main className="app-shell">
      <header className="app-topbar">
        <a className="brand" href="/" aria-label="AIVOA RCA Co-Pilot home">
          <span className="brand-mark">A</span>
          <span>AIVOA <strong>QUALITY</strong></span>
        </a>
        <span className="workspace-label">API MANUFACTURING · RCA WORKSPACE</span>
      </header>

      <div className="workspace">
        <InvestigationForm />
        <ChatPanel />
      </div>
    </main>
  )
}

export default App