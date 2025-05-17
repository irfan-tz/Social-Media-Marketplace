import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function DashboardLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleProfile = () => {
    navigate("/profile"); // Redirect to profile page
  };

  return (
    <div className="dashboard">
      <nav className="top-nav">
        <div className="nav-content">
          <h1>Dashboard</h1>
          <div className="user-controls">
            {user && <span className="user-email">{user.email}</span>}
            <button onClick={handleProfile} className="profile-btn">
              Profile
            </button>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="dashboard-content">{children}</main>
    </div>
  );
}