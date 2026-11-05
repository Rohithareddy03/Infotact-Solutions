
import "./index.css";

function App() {
  return (
    <div className="app">
      <header className="dashboard-header">
        <h1>CogniStream</h1>
        <p>Developer Flow-State & Cognitive Load Analytics</p>
      </header>

      <main className="dashboard-content">
        <section className="welcome-section">
          <h2>Developer Analytics Dashboard</h2>
          <p>
            Monitor developer activity, coding sessions,
            context switching, and interruption patterns.
          </p>
        </section>

        <section className="dashboard-placeholder">
          <h3>Dashboard Components</h3>
          <p>
            KPI cards and analytics charts will be
            implemented in upcoming tasks.
          </p>
        </section>
      </main>
    </div>
  );
}

export default App;
