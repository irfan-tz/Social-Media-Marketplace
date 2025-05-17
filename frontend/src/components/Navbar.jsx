import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../assets/styles/NavBar.css';

function Navbar() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">SocialApp</Link>
      </div>
      <div className="navbar-links">
        {user ? (
          <>
            <span
              className="navbar-greeting"
              style={{
                background: 'linear-gradient(45deg,rgb(87, 218, 170),rgb(109, 69, 255))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 'bold',
                padding: '4px 10px',
                marginRight: '10px'
              }}
            >
              Hello, {user.username}
            </span>
            <Link to="/home" className={location.pathname === '/home' ? 'active' : ''}>
              Home
            </Link>
            <Link to="/messages" className={location.pathname === '/messages' ? 'active' : ''}>
              Messages
            </Link>
            <Link to="/groups" className={location.pathname === '/groups' ? 'active' : ''}>
              Groups
            </Link>
            <Link to="/market" className={location.pathname === '/market' ? 'active' : ''}>
              Marketplace
            </Link>
            <Link to="/profile" className={location.pathname === '/profile' ? 'active' : ''}>
              Profile
            </Link>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className={location.pathname === '/login' ? 'active' : ''}>
              Login
            </Link>
            <Link to="/register" className={location.pathname === '/register' ? 'active' : ''}>
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
