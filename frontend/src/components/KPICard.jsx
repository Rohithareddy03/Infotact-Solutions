function KPICard({ title, value, description, icon }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card-top">
        <span className="kpi-icon">{icon}</span>
      </div>

      <h3>{title}</h3>

      <div className="kpi-value">{value}</div>

      <p className="kpi-description">{description}</p>
    </div>
  );
}

export default KPICard;
