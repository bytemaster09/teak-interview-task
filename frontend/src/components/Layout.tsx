import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  function handleLogout() {
    logout();
    nav("/");
  }

  return (
    <>
      <nav className="nav">
        <Link to="/" className="nav-brand">Inkwell</Link>
        <div className="nav-links">
          {user ? (
            <>
              {user.role === "author" && (
                <Link to="/dashboard" className="nav-link">Dashboard</Link>
              )}
              <span className="nav-username">{user.username}</span>
              <button onClick={handleLogout} className="btn btn-outline btn-sm">Sign out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">Sign in</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Register</Link>
            </>
          )}
        </div>
      </nav>
      <main className="page">{children}</main>
    </>
  );
}
