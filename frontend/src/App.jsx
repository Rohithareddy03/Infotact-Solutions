import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import "./index.css";

function App() {
  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
