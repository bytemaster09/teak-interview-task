import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import Layout from "../components/Layout";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      nav("/");
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div style={{ maxWidth: 400, margin: "0 auto" }}>
        <div className="card" style={{ padding: "2rem" }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Sign in</h1>

          {error && <p className="error-msg">{error}</p>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label className="label">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input"
              />
            </div>
            <div className="field">
              <label className="label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input"
              />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary btn-wide">
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-muted" style={{ fontSize: 14, marginTop: 16 }}>
            Don't have an account?{" "}
            <Link to="/register" style={{ color: "var(--text)", fontWeight: 600 }}>Register</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
}
