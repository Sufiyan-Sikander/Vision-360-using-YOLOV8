import { Navigate, Outlet } from 'react-router-dom';

export default function ProtectedRoute() {
  const token = localStorage.getItem('access');
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}