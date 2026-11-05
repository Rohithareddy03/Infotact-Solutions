function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h2>CogniStream</h2>
        <p>Developer Analytics</p>
      </div>

      <nav className="sidebar-nav">
        <a className="active" href="#dashboard">
          Dashboard
        </a>

        <a href="#activity">Developer Activity</a>
        <a href="#flow">Flow-State Analysis</a>
        <a href="#context">Context Switching</a>
        <a href="#interruptions">Interruptions</a>
      </nav>

      <div className="sidebar-footer">
        <p>CogniStream Project</p>
        <small>Analytics Dashboard</small>
      </div>
    </aside>
  );
}

export default Sidebar;
