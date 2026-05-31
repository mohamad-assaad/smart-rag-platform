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

type Customer = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

type DocumentItem = {
  id: string;
  customer_id: string;
  file_name: string;
  content: string;
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

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerName, setCustomerName] = useState("");
  const [customerDescription, setCustomerDescription] = useState("");

  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedDocuments, setUploadedDocuments] = useState<DocumentItem[]>(
    []
  );

  const [message, setMessage] = useState("");
  const [dashboardMessage, setDashboardMessage] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCustomersLoading, setIsCustomersLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  function getAuthHeaders(savedToken: string) {
    return {
      Authorization: `Bearer ${savedToken}`,
    };
  }

  async function fetchCurrentUser(savedToken: string) {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders(savedToken),
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

  async function fetchCustomers(savedToken: string) {
    setIsCustomersLoading(true);
    setDashboardMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/customers`, {
        headers: getAuthHeaders(savedToken),
      });

      const data = await response.json();

      if (!response.ok) {
        setDashboardMessage(data.detail || "Could not load customers.");
        return;
      }

      setCustomers(data);

      if (data.length > 0 && !selectedCustomerId) {
        setSelectedCustomerId(data[0].id);
      }
    } catch {
      setDashboardMessage("Could not connect to the backend.");
    } finally {
      setIsCustomersLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      fetchCurrentUser(token);
      fetchCustomers(token);
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
      await fetchCustomers(data.access_token);
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
    setCustomers([]);
    setUploadedDocuments([]);
    setMessage("Logged out.");
  }

  async function handleCreateCustomer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setDashboardMessage("You must be logged in.");
      return;
    }

    if (!customerName.trim()) {
      setDashboardMessage("Customer name is required.");
      return;
    }

    setDashboardMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/customers`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(token),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: customerName,
          description: customerDescription || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setDashboardMessage(data.detail || "Could not create customer.");
        return;
      }

      setCustomers((currentCustomers) => [data, ...currentCustomers]);
      setSelectedCustomerId(data.id);
      setCustomerName("");
      setCustomerDescription("");
      setDashboardMessage("Customer created successfully.");
    } catch {
      setDashboardMessage("Could not connect to the backend.");
    }
  }

  async function handleUploadDocument(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setUploadMessage("You must be logged in.");
      return;
    }

    if (!selectedCustomerId) {
      setUploadMessage("Please select a customer.");
      return;
    }

    if (!selectedFile) {
      setUploadMessage("Please choose a .txt file.");
      return;
    }

    if (!selectedFile.name.endsWith(".txt")) {
      setUploadMessage("Only .txt files are supported right now.");
      return;
    }

    setIsUploading(true);
    setUploadMessage("Uploading document...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const uploadResponse = await fetch(
        `${API_BASE_URL}/customers/${selectedCustomerId}/documents/upload`,
        {
          method: "POST",
          headers: getAuthHeaders(token),
          body: formData,
        }
      );

      const uploadedDocument = await uploadResponse.json();

      if (!uploadResponse.ok) {
        setUploadMessage(uploadedDocument.detail || "Upload failed.");
        return;
      }

      setUploadMessage("Document uploaded. Creating chunks...");

      const chunksResponse = await fetch(
        `${API_BASE_URL}/documents/${uploadedDocument.id}/chunks`,
        {
          method: "POST",
          headers: getAuthHeaders(token),
        }
      );

      if (!chunksResponse.ok) {
        const errorData = await chunksResponse.json();
        setUploadMessage(
          errorData.detail || "Document uploaded, but chunking failed."
        );
        return;
      }

      setUploadMessage("Chunks created. Storing vectors...");

      const vectorsResponse = await fetch(
        `${API_BASE_URL}/documents/${uploadedDocument.id}/vectors`,
        {
          method: "POST",
          headers: getAuthHeaders(token),
        }
      );

      if (!vectorsResponse.ok) {
        const errorData = await vectorsResponse.json();
        setUploadMessage(
          errorData.detail || "Chunks created, but vector storage failed."
        );
        return;
      }

      setUploadedDocuments((currentDocuments) => [
        uploadedDocument,
        ...currentDocuments,
      ]);
      setSelectedFile(null);
      setUploadMessage("Document uploaded, chunked, and indexed successfully.");
    } catch {
      setUploadMessage("Could not connect to the backend.");
    } finally {
      setIsUploading(false);
    }
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

          <div className="dashboard-section">
            <div className="section-header">
              <div>
                <h2>Customers</h2>
                <p>
                  Create and manage customer accounts before uploading
                  documents.
                </p>
              </div>

              <button
                className="secondary-button"
                type="button"
                onClick={() => token && fetchCustomers(token)}
              >
                Refresh
              </button>
            </div>

            <form className="customer-form" onSubmit={handleCreateCustomer}>
              <input
                value={customerName}
                onChange={(event) => setCustomerName(event.target.value)}
                placeholder="Customer name"
              />
              <input
                value={customerDescription}
                onChange={(event) =>
                  setCustomerDescription(event.target.value)
                }
                placeholder="Customer description"
              />
              <button className="primary-button" type="submit">
                Add Customer
              </button>
            </form>

            {dashboardMessage && (
              <p className="message-box">{dashboardMessage}</p>
            )}

            {isCustomersLoading ? (
              <p className="muted-text">Loading customers...</p>
            ) : (
              <div className="customer-list">
                {customers.length === 0 ? (
                  <p className="muted-text">No customers yet.</p>
                ) : (
                  customers.map((customer) => (
                    <article className="customer-card" key={customer.id}>
                      <div>
                        <h3>{customer.name}</h3>
                        <p>{customer.description || "No description"}</p>
                      </div>
                      <code>{customer.id}</code>
                    </article>
                  ))
                )}
              </div>
            )}
          </div>

          <div className="dashboard-section">
            <div className="section-header">
              <div>
                <h2>Upload Document</h2>
                <p>
                  Upload a text file, then the app automatically creates chunks
                  and stores vectors in Qdrant.
                </p>
              </div>
            </div>

            <form className="upload-form" onSubmit={handleUploadDocument}>
              <select
                value={selectedCustomerId}
                onChange={(event) => setSelectedCustomerId(event.target.value)}
              >
                <option value="">Select customer</option>
                {customers.map((customer) => (
                  <option value={customer.id} key={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>

              <input
                type="file"
                accept=".txt,text/plain"
                onChange={(event) =>
                  setSelectedFile(event.target.files?.[0] || null)
                }
              />

              <button
                className="primary-button"
                type="submit"
                disabled={isUploading}
              >
                {isUploading ? "Processing..." : "Upload + Index"}
              </button>
            </form>

            {uploadMessage && <p className="message-box">{uploadMessage}</p>}

            <div className="document-list">
              {uploadedDocuments.length === 0 ? (
                <p className="muted-text">No uploaded documents this session.</p>
              ) : (
                uploadedDocuments.map((document) => (
                  <article className="document-card" key={document.id}>
                    <div>
                      <h3>{document.file_name}</h3>
                      <p>
                        Ready for Ask AI. Uploaded at{" "}
                        {new Date(document.created_at).toLocaleString()}.
                      </p>
                    </div>
                    <code>{document.id}</code>
                  </article>
                ))
              )}
            </div>
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
            Next step: we will add Ask AI directly inside this dashboard.
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