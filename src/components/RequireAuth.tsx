import { Navigate, useLocation } from "react-router-dom";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || '') : '';
  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}


