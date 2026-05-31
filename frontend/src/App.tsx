import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type User = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

type AuthMode = "login" | "register";

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin12345");
  const [fullName, setFullName] = useState("Admin User");
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("access_token")
  );
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function fetchCurrentUser(savedToken: string) {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${savedToken}`,
      },
    });

    if (!response.ok) {
      localStorage.removeItem("access_token");
      setToken(null);
      setCurrentUser(null);
      return;
    }

    const data: User = await response.json();
    setCurrentUser(data);
  }

  useEffect(() => {
    if (token) {
      fetchCurrentUser(token);
    }
  }, [token]);

  async function handleRegister() {
    setIsLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Registration failed.");
        return;
      }

      setMessage("Account created. You can now log in.");
      setAuthMode("login");
    } catch {
      setMessage("Could not connect to the backend.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLogin() {
    setIsLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Login failed.");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
      setMessage("Login successful.");
      await fetchCurrentUser(data.access_token);
    } catch {
      setMessage("Could not connect to the backend.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    setToken(null);
    setCurrentUser(null);
    setMessage("Logged out.");
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (authMode === "login") {
      await handleLogin();
    } else {
      await handleRegister();
    }
  }

  if (token && currentUser) {
    return (
      <main className="app-shell">
        <section className="dashboard-card">
          <div className="dashboard-header">
            <div>
              <p className="eyebrow">Smart RAG Platform</p>
              <h1>AI Customer Intelligence Dashboard</h1>
              <p className="subtitle">
                Upload customer documents, generate embeddings, search with
                hybrid retrieval, and ask AI questions with source tracking.
              </p>
            </div>

            <button className="secondary-button" onClick={handleLogout}>
              Logout
            </button>
          </div>

          <div className="user-panel">
            <h2>Signed in</h2>
            <p>
              <strong>Email:</strong> {currentUser.email}
            </p>
            <p>
              <strong>Name:</strong> {currentUser.full_name || "Not provided"}
            </p>
            <p>
              <strong>Status:</strong>{" "}
              {currentUser.is_active ? "Active" : "Disabled"}
            </p>
          </div>

          <div className="feature-grid">
            <div className="feature-card">
              <h3>Documents</h3>
              <p>Upload customer notes and knowledge files.</p>
            </div>

            <div className="feature-card">
              <h3>Vector Search</h3>
              <p>Store embeddings in Qdrant and search semantically.</p>
            </div>

            <div className="feature-card">
              <h3>Ask AI</h3>
              <p>Use hybrid retrieval to answer questions with sources.</p>
            </div>
          </div>

          <p className="next-note">
            Next step: we will add real dashboard actions for customers,
            uploads, and Ask AI.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <section className="auth-card">
        <div className="brand-block">
          <p className="eyebrow">Smart RAG Platform</p>
          <h1>{authMode === "login" ? "Welcome back" : "Create account"}</h1>
          <p className="subtitle">
            Sign in to access your AI-powered customer document intelligence
            dashboard.
          </p>
        </div>

        <div className="mode-switch">
          <button
            className={authMode === "login" ? "active" : ""}
            onClick={() => setAuthMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={authMode === "register" ? "active" : ""}
            onClick={() => setAuthMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {authMode === "register" && (
            <label>
              Full name
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Admin User"
              />
            </label>
          )}

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@example.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="admin12345"
              required
            />
          </label>

          <button className="primary-button" type="submit" disabled={isLoading}>
            {isLoading
              ? "Please wait..."
              : authMode === "login"
              ? "Login"
              : "Create account"}
          </button>
        </form>

        {message && <p className="message-box">{message}</p>}
      </section>
    </main>
  );
}

export default App;