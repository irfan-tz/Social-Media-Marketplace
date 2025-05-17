import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './src/context/AuthContext';

const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  // Optionally, you can display a loading spinner while checking auth status
  if (loading) {
    return <div>Loading...</div>;
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;
