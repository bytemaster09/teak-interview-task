import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import Layout from "../components/Layout";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"reader" | "author">("reader");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, username, password, role);
      nav(role === "author" ? "/dashboard" : "/");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div style={{ maxWidth: 400, margin: "0 auto" }}>
        <div className="card" style={{ padding: "2rem" }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Create account</h1>

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
              <label className="label">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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
            <div className="field">
              <label className="label">I want to…</label>
              <div style={{ display: "flex", gap: 16, marginTop: 4 }}>
                {(["reader", "author"] as const).map((r) => (
                  <label
                    key={r}
                    style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 14 }}
                  >
                    <input
                      type="radio"
                      value={r}
                      checked={role === r}
                      onChange={() => setRole(r)}
                    />
                    {r === "reader" ? "Read posts" : "Write posts"}
                  </label>
                ))}
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary btn-wide">
              {loading ? "Creating…" : "Create account"}
            </button>
          </form>

          <p className="text-muted" style={{ fontSize: 14, marginTop: 16 }}>
            Already have an account?{" "}
            <Link to="/login" style={{ color: "var(--text)", fontWeight: 600 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </Layout>
  );
}
