import { useEffect, useMemo, useState, type FormEvent } from "react";
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

type AnswerSource = {
  chunk_id: string;
  chunk_index: number;
  score: number;
  content: string;
  source_type: string;
};

type AnswerResponse = {
  question: string;
  answer: string;
  sources: AnswerSource[];
};

type AuthMode = "login" | "register";
type ActiveSection = "overview" | "customers" | "documents" | "upload" | "ask";

type SearchOption = {
  label: string;
  description: string;
  section: ActiveSection;
};

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [activeSection, setActiveSection] = useState<ActiveSection>("overview");
  const [searchQuery, setSearchQuery] = useState("");

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
  const [uploadedDocuments, setUploadedDocuments] = useState<DocumentItem[]>([]);

  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [question, setQuestion] = useState(
    "What should the account manager do before renewal?"
  );
  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [showSources, setShowSources] = useState(false);

  const [message, setMessage] = useState("");
  const [dashboardMessage, setDashboardMessage] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const [answerMessage, setAnswerMessage] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [isCustomersLoading, setIsCustomersLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnswerLoading, setIsAnswerLoading] = useState(false);

  const selectedDocument = useMemo(
    () => uploadedDocuments.find((document) => document.id === selectedDocumentId),
    [uploadedDocuments, selectedDocumentId]
  );

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.id === selectedCustomerId),
    [customers, selectedCustomerId]
  );

  const searchOptions = useMemo<SearchOption[]>(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) {
      return [];
    }

    const pageOptions: Array<SearchOption & { keywords: string[] }> = [
      {
        label: "Overview",
        description: "Open the main dashboard overview.",
        section: "overview",
        keywords: ["overview", "home", "dashboard", "main"],
      },
      {
        label: "Customers",
        description: "Create and manage customer records.",
        section: "customers",
        keywords: ["customers", "customer", "client", "clients", "cu"],
      },
      {
        label: "Documents",
        description: "View uploaded documents.",
        section: "documents",
        keywords: ["documents", "document", "docs", "files", "file", "do"],
      },
      {
        label: "Upload knowledge",
        description: "Upload and index a customer text file.",
        section: "upload",
        keywords: ["upload", "knowledge", "index", "file upload", "up"],
      },
      {
        label: "Ask AI",
        description: "Ask questions against indexed documents.",
        section: "ask",
        keywords: ["ask", "ai", "answer", "question", "rag"],
      },
    ];

    const matchingPages = pageOptions.filter((option) => {
      const searchableText = `${option.label} ${
        option.description
      } ${option.keywords.join(" ")}`.toLowerCase();

      return searchableText.includes(query);
    });

    const matchingCustomers: SearchOption[] = customers
      .filter((customer) =>
        `${customer.name} ${customer.description || ""}`
          .toLowerCase()
          .includes(query)
      )
      .slice(0, 3)
      .map((customer) => ({
        label: customer.name,
        description: "Customer record",
        section: "customers",
      }));

    const matchingDocuments: SearchOption[] = uploadedDocuments
      .filter((document) => document.file_name.toLowerCase().includes(query))
      .slice(0, 3)
      .map((document) => ({
        label: document.file_name,
        description: "Uploaded document",
        section: "documents",
      }));

    return [...matchingPages, ...matchingCustomers, ...matchingDocuments].slice(
      0,
      6
    );
  }, [searchQuery, customers, uploadedDocuments]);

  function getAuthHeaders(savedToken: string) {
    return {
      Authorization: `Bearer ${savedToken}`,
    };
  }

  function handleSearchSelect(option: SearchOption) {
    setActiveSection(option.section);
    setSearchQuery("");
    setDashboardMessage("");
    setUploadMessage("");
    setAnswerMessage("");
  }

  function handleGlobalSearch() {
    const firstOption = searchOptions[0];

    if (firstOption) {
      handleSearchSelect(firstOption);
      return;
    }

    const query = searchQuery.trim();

    if (!query) {
      return;
    }

    setActiveSection("overview");
    setDashboardMessage(`No result found for "${query}".`);
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
    setAnswerResult(null);
    setShowSources(false);
    setSearchQuery("");
    setActiveSection("overview");
    setMessage("Logged out.");
  }

  async function handleCreateCustomer(event: FormEvent<HTMLFormElement>) {
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

  async function handleUploadDocument(event: FormEvent<HTMLFormElement>) {
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
      setSelectedDocumentId(uploadedDocument.id);
      setSelectedFile(null);
      setUploadMessage("Document uploaded, chunked, and indexed successfully.");
      setActiveSection("ask");
    } catch {
      setUploadMessage("Could not connect to the backend.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAskAi(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setAnswerMessage("You must be logged in.");
      return;
    }

    if (!selectedDocumentId) {
      setAnswerMessage("Please select an uploaded document.");
      return;
    }

    if (!question.trim()) {
      setAnswerMessage("Please enter a question.");
      return;
    }

    setIsAnswerLoading(true);
    setAnswerMessage("Asking AI...");
    setAnswerResult(null);
    setShowSources(false);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/answer`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(token),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document_id: selectedDocumentId,
          question,
          search_mode: "hybrid",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAnswerMessage(data.detail || "Could not generate answer.");
        return;
      }

      setAnswerResult(data);
      setAnswerMessage("Answer generated successfully.");
    } catch {
      setAnswerMessage("Could not connect to the backend.");
    } finally {
      setIsAnswerLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (authMode === "login") {
      await handleLogin();
    } else {
      await handleRegister();
    }
  }

  function renderMainContent() {
    if (activeSection === "overview") {
      return (
        <section className="admin-card">
          <div className="section-heading">
            <h2>Overview</h2>
            <p>
              Monitor customers, indexed documents, and AI answer activity from
              one admin workspace.
            </p>
          </div>

          {dashboardMessage && <p className="message-box">{dashboardMessage}</p>}

          <div className="admin-summary-grid">
            <article>
              <span>Total customers</span>
              <strong>{customers.length}</strong>
              <p>Customer workspaces available in the system.</p>
            </article>

            <article>
              <span>Indexed this session</span>
              <strong>{uploadedDocuments.length}</strong>
              <p>Documents uploaded and prepared for retrieval.</p>
            </article>

            <article>
              <span>AI answers</span>
              <strong>{answerResult ? 1 : 0}</strong>
              <p>Generated answers with source tracking.</p>
            </article>
          </div>

          <div className="admin-empty-state">
            <div className="empty-icon">✦</div>
            <h2>Create your customer intelligence workflow.</h2>
            <p>
              Add a customer, upload a knowledge file, index the document, and
              ask AI questions grounded in your content.
            </p>
            <div className="empty-actions">
              <button
                className="primary-button"
                type="button"
                onClick={() => setActiveSection("upload")}
              >
                Upload knowledge
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => setActiveSection("ask")}
              >
                Ask AI
              </button>
            </div>
          </div>
        </section>
      );
    }

    if (activeSection === "customers") {
      return (
        <section className="admin-card">
          <div className="section-toolbar">
            <div className="section-heading">
              <h2>Customers</h2>
              <p>Create and manage customer records used for document uploads.</p>
            </div>

            <button
              className="secondary-button"
              type="button"
              onClick={() => token && fetchCustomers(token)}
            >
              Refresh
            </button>
          </div>

          <form className="admin-form-grid" onSubmit={handleCreateCustomer}>
            <input
              value={customerName}
              onChange={(event) => setCustomerName(event.target.value)}
              placeholder="Customer name"
            />
            <input
              value={customerDescription}
              onChange={(event) => setCustomerDescription(event.target.value)}
              placeholder="Customer description"
            />
            <button className="primary-button" type="submit">
              Add customer
            </button>
          </form>

          {dashboardMessage && <p className="message-box">{dashboardMessage}</p>}

          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Description</th>
                  <th>Created</th>
                  <th>ID</th>
                </tr>
              </thead>
              <tbody>
                {isCustomersLoading ? (
                  <tr>
                    <td colSpan={4}>Loading customers...</td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No customers yet.</td>
                  </tr>
                ) : (
                  customers.map((customer) => (
                    <tr key={customer.id}>
                      <td className="table-title">{customer.name}</td>
                      <td>{customer.description || "No description"}</td>
                      <td>{new Date(customer.created_at).toLocaleDateString()}</td>
                      <td>
                        <code>{customer.id}</code>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      );
    }

    if (activeSection === "documents") {
      return (
        <section className="admin-card">
          <div className="section-heading">
            <h2>Documents</h2>
            <p>View documents uploaded during this browser session.</p>
          </div>

          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>File name</th>
                  <th>Customer ID</th>
                  <th>Uploaded</th>
                  <th>Document ID</th>
                </tr>
              </thead>
              <tbody>
                {uploadedDocuments.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No uploaded documents this session.</td>
                  </tr>
                ) : (
                  uploadedDocuments.map((document) => (
                    <tr key={document.id}>
                      <td className="table-title">{document.file_name}</td>
                      <td>
                        <code>{document.customer_id}</code>
                      </td>
                      <td>{new Date(document.created_at).toLocaleString()}</td>
                      <td>
                        <code>{document.id}</code>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      );
    }

    if (activeSection === "upload") {
      return (
        <section className="admin-card">
          <div className="section-heading">
            <h2>Upload knowledge</h2>
            <p>
              Upload a text file to a customer. The system will create chunks and
              store vectors automatically.
            </p>
          </div>

          <form className="upload-modern-card" onSubmit={handleUploadDocument}>
            <div className="upload-modern-banner">
              <span className="upload-banner-label">Selected customer</span>
              <strong>{selectedCustomer?.name || "No customer selected"}</strong>
            </div>

            <div className="upload-modern-grid">
              <div className="upload-field">
                <label>Customer</label>
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
              </div>

              <div className="upload-field">
                <label>Document file</label>
                <input
                  type="file"
                  accept=".txt,text/plain"
                  onChange={(event) =>
                    setSelectedFile(event.target.files?.[0] || null)
                  }
                />
              </div>

              <div className="upload-action">
                <button
                  className="primary-button"
                  type="submit"
                  disabled={isUploading}
                >
                  {isUploading ? "Processing..." : "Upload + index"}
                </button>
              </div>
            </div>
          </form>

          {uploadMessage && <p className="message-box">{uploadMessage}</p>}

          <div className="admin-empty-state compact">
            <div className="empty-icon">⇧</div>
            <h2>Uploaded documents appear here.</h2>
            <p>
              After upload, the document is chunked, embedded, indexed, and made
              available for Ask AI.
            </p>
          </div>
        </section>
      );
    }

    return (
      <section className="admin-card">
        <div className="section-heading">
          <h2>Ask AI</h2>
          <p>
            Ask questions against indexed customer documents using hybrid
            retrieval and source tracking.
          </p>
        </div>

        <form className="ask-form" onSubmit={handleAskAi}>
          <select
            value={selectedDocumentId}
            onChange={(event) => setSelectedDocumentId(event.target.value)}
          >
            <option value="">Select uploaded document</option>
            {uploadedDocuments.map((document) => (
              <option value={document.id} key={document.id}>
                {document.file_name}
              </option>
            ))}
          </select>

          {selectedDocument && (
            <div className="selected-document">
              Selected document: <strong>{selectedDocument.file_name}</strong>
            </div>
          )}

          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about the uploaded document..."
            rows={4}
          />

          <button
            className="primary-button"
            type="submit"
            disabled={isAnswerLoading}
          >
            {isAnswerLoading ? "Asking..." : "Ask AI"}
          </button>
        </form>

        {answerMessage && <p className="message-box">{answerMessage}</p>}

        {answerResult && (
          <div className="answer-panel">
            <div className="answer-header">
              <p className="eyebrow">Generated answer</p>
              <h3>AI response</h3>
            </div>

            <p className="answer-text">{answerResult.answer}</p>

            <div className="sources-toggle-row">
              <span>
                Sources used: {answerResult.sources.length}{" "}
                {answerResult.sources.length === 1 ? "chunk" : "chunks"}
              </span>

              <button
                className="secondary-button"
                type="button"
                onClick={() => setShowSources((current) => !current)}
              >
                {showSources ? "Hide sources" : "Show sources"}
              </button>
            </div>

            {showSources && (
              <div className="source-list">
                {answerResult.sources.length === 0 ? (
                  <p className="muted-text">No sources returned.</p>
                ) : (
                  answerResult.sources.map((source) => (
                    <article className="source-card" key={source.chunk_id}>
                      <div className="source-meta">
                        <span>{source.source_type}</span>
                        <span>Chunk {source.chunk_index}</span>
                        <span>Score {source.score.toFixed(4)}</span>
                      </div>
                      <p>{source.content}</p>
                    </article>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </section>
    );
  }

  if (!token || !currentUser) {
    return (
      <main className="auth-page">
        <section className="auth-hero">
          <div className="auth-logo">SR</div>
          <p className="eyebrow">Smart RAG Platform</p>
          <h1>AI customer intelligence for support and renewal teams.</h1>
          <p className="subtitle">
            Upload customer notes, index them with vector search, and ask AI
            questions with trusted source tracking.
          </p>

          <div className="auth-proof-grid">
            <div>
              <strong>Hybrid Retrieval</strong>
              <span>Keyword + vector search</span>
            </div>
            <div>
              <strong>Secure Access</strong>
              <span>JWT authentication</span>
            </div>
            <div>
              <strong>Production Stack</strong>
              <span>FastAPI, Qdrant, Redis</span>
            </div>
          </div>
        </section>

        <section className="auth-card">
          <div className="brand-block">
            <p className="eyebrow">Account access</p>
            <h2>{authMode === "login" ? "Welcome back" : "Create account"}</h2>
            <p>
              Sign in to manage customers, upload documents, and ask AI
              questions.
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

  return (
    <main className="admin-shell">
      <aside className="icon-rail">
        <div className="rail-logo">SR</div>

        <button
          className={activeSection === "overview" ? "active" : ""}
          onClick={() => setActiveSection("overview")}
          title="Home"
        >
          ⌂
        </button>

        <button
          className={activeSection === "customers" ? "active" : ""}
          onClick={() => setActiveSection("customers")}
          title="Customers"
        >
          ◎
        </button>

        <button
          className={activeSection === "documents" ? "active" : ""}
          onClick={() => setActiveSection("documents")}
          title="Documents"
        >
          ▣
        </button>

        <button
          className={activeSection === "upload" ? "active" : ""}
          onClick={() => setActiveSection("upload")}
          title="Upload"
        >
          ⇧
        </button>

        <button
          className={activeSection === "ask" ? "active" : ""}
          onClick={() => setActiveSection("ask")}
          title="Ask AI"
        >
          □
        </button>
      </aside>

      <aside className="admin-nav">
        <div className="admin-brand">
          <h1>Smart RAG</h1>
          <p>Customer AI</p>
        </div>

        <h2>Manage</h2>

        <nav>
          <button
            className={activeSection === "overview" ? "active" : ""}
            onClick={() => setActiveSection("overview")}
          >
            Overview
          </button>

          <button
            className={activeSection === "customers" ? "active" : ""}
            onClick={() => setActiveSection("customers")}
          >
            Customers
          </button>

          <button
            className={activeSection === "documents" ? "active" : ""}
            onClick={() => setActiveSection("documents")}
          >
            Documents
          </button>

          <button
            className={activeSection === "upload" ? "active" : ""}
            onClick={() => setActiveSection("upload")}
          >
            Upload knowledge
          </button>

          <button
            className={activeSection === "ask" ? "active" : ""}
            onClick={() => setActiveSection("ask")}
          >
            Ask AI
          </button>
        </nav>

        <div className="admin-user-card">
          <span>Signed in as</span>
          <strong>{currentUser.email}</strong>
          <button className="secondary-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </aside>

      <section className="admin-main">
        <header className="admin-topbar">
          <div className="global-search-wrap">
            <span className="search-icon">⌕</span>

            <input
              className="global-search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleGlobalSearch();
                }

                if (event.key === "Escape") {
                  setSearchQuery("");
                }
              }}
              placeholder="Search pages, customers, or documents"
            />

            {searchOptions.length > 0 && (
              <div className="search-suggestions">
                {searchOptions.map((option) => (
                  <button
                    type="button"
                    key={`${option.section}-${option.label}`}
                    onClick={() => handleSearchSelect(option)}
                  >
                    <strong>{option.label}</strong>
                    <span>{option.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </header>

        <div className="command-bar">
          <button type="button" onClick={() => setActiveSection("customers")}>
            + New customer
          </button>

          <button type="button" onClick={() => setActiveSection("upload")}>
            ⇧ Upload
          </button>

          <button type="button" onClick={() => setActiveSection("ask")}>
            □ Ask AI
          </button>

          <button type="button" onClick={() => token && fetchCustomers(token)}>
            ↻ Refresh
          </button>
        </div>

        <section className="page-header">
          <h1>
            {activeSection === "overview" && "Overview"}
            {activeSection === "customers" && "Customers"}
            {activeSection === "documents" && "Documents"}
            {activeSection === "upload" && "Upload knowledge"}
            {activeSection === "ask" && "Ask AI"}
          </h1>

          <p>
            {activeSection === "overview" &&
              "Manage your customer intelligence workspace."}
            {activeSection === "customers" &&
              "Create and manage customer records."}
            {activeSection === "documents" &&
              "Review uploaded documents available in this session."}
            {activeSection === "upload" &&
              "Upload text files and index them for retrieval."}
            {activeSection === "ask" &&
              "Generate grounded answers from indexed documents."}
          </p>
        </section>

        {renderMainContent()}
      </section>
    </main>
  );
}

export default App;