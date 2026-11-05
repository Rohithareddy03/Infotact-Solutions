import Header from "../components/Header";
import KPICard from "../components/KPICard";

function Dashboard() {
  const metrics = [
    {
      title: "Total Commits",
      value: "1,248",
      description: "Developer commit events",
      icon: "💻",
    },
    {
      title: "IDE Activity",
      value: "126 hrs",
      description: "Recorded IDE activity",
      icon: "⌨️",
    },
    {
      title: "Average Session",
      value: "52 min",
      description: "Average recorded session",
      icon: "⏱️",
    },
    {
      title: "Coding Sessions",
      value: "186",
      description: "Detected coding sessions",
      icon: "📊",
    },
    {
      title: "Context Switches",
      value: "342",
      description: "Detected activity transitions",
      icon: "🔄",
    },
    {
      title: "Potential Interruptions",
      value: "78",
      description: "Activity-based interruption indicators",
      icon: "🔔",
    },
  ];

  return (
    <div className="dashboard-page" id="dashboard">
      <Header />

      <section className="filter-section">
        <div>
          <h2>Overview</h2>
          <p>Summary of developer activity metrics</p>
        </div>

        <select aria-label="Select reporting period">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
        </select>
      </section>

      <section className="kpi-grid">
        {metrics.map((metric) => (
          <KPICard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            description={metric.description}
            icon={metric.icon}
          />
        ))}
      </section>

      <section className="dashboard-note">
        <h3>Analytics Overview</h3>
        <p>
          Activity charts, flow-state timelines, and interruption
          analysis will be added in upcoming development tasks.
        </p>
        <small>
          Preview values are sample data, not actual developer measurements.
        </small>
      </section>
    </div>
  );
}

export default Dashboard;
