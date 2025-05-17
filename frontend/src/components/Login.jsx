import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import '../assets/styles/Auth.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();
  
  const allowedUsernameRegex = /^[A-Za-z0-9_.-]*$/;

  // Auto-redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate("/home");
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!allowedUsernameRegex.test(username)) {
      setError("Invalid username format");
      return;
    }

    try {
      // Attempt to get JWT tokens
      await axios.post(
        '/api/token/',
        {
          username: username.trim(),
          password,
        },
        { 
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      // Fetch user profile
      await login();
      navigate("/home");
    } catch (error) {
      const message = error.response?.data?.detail || 
                      error.response?.data?.error || 
                      'Login failed';
      setError(message);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Welcome Back</h2>
        {error && <div className="error-message">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group password-group">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <i
              onClick={() => setShowPassword(!showPassword)}
              className={`fas fa-eye${showPassword ? '-slash' : ''}`}
            />
          </div>
          <button type="submit" disabled={!!error}>
            Sign In
          </button>
          <p className="auth-link">
            New user? <Link to="/register">Register here</Link>
          </p>
          <p className="auth-link" style={{ border: "1px solid red", color: "blue" }}>
          Forgot password? <Link to="/forgot-password">Reset here</Link>
        </p>
        </form>
      </div>
    </div>
  );
}
