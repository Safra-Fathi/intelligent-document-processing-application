import {
    useEffect,
    useRef,
    useState,
} from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

interface User {
    id: number;
    email: string;
    is_active: boolean;
}

interface Document {
    id: number;
    original_filename: string;
    mime_type: string;
    size_bytes: number;
    processing_status: string;
    predicted_type: string | null;
    classification_confidence: number | null;
    review_status: string | null;
    created_at: string;
}

export default function Dashboard() {
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [user, setUser] = useState<User | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");

    const loadDashboard = async () => {
        try {
            const [userResponse, documentsResponse] =
                await Promise.all([
                    api.get("/auth/me"),
                    api.get("/documents"),
                ]);

            setUser(userResponse.data);
            setDocuments(documentsResponse.data);
        } catch {
            localStorage.removeItem("access_token");
            navigate("/login");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDashboard();
    }, []);

    const handleFileChange = async (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setError("");

        const allowedTypes = [
            "application/pdf",
            "image/png",
            "image/jpeg",
        ];

        if (!allowedTypes.includes(file.type)) {
            setError("Please select a PDF, PNG, JPG or JPEG file.");
            event.target.value = "";
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            setError("The selected file exceeds the 10 MB limit.");
            event.target.value = "";
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();
            formData.append("file", file);

            // Step 1: secure upload
            const uploadResponse = await api.post(
                "/documents/upload",
                formData
            );

            const documentId = uploadResponse.data.id;

            // Step 2: run OCR + ML + extraction + validation
            await api.post(
                `/documents/${documentId}/process`
            );

            // Step 3: reload current user's history
            const documentsResponse = await api.get("/documents");
            setDocuments(documentsResponse.data);

        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                "Unable to process the document."
            );
        } finally {
            setUploading(false);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        navigate("/login");
    };

    const formatConfidence = (
        confidence: number | null
    ) => {
        if (confidence === null) {
            return "—";
        }

        return `${(confidence * 100).toFixed(1)}%`;
    };

    const formatDate = (value: string) => {
        return new Date(value).toLocaleString();
    };

    if (loading) {
        return (
            <div className="page-message">
                Loading dashboard...
            </div>
        );
    }

    return (
        <div className="dashboard">
            <header className="topbar">
                <div className="brand">
                    <span className="brand-mark">DI</span>

                    <div>
                        <h1>Document Intelligence</h1>
                    </div>
                </div>

                <div className="user-area">
                    <span>{user?.email}</span>

                    <button
                        className="secondary-button"
                        onClick={logout}
                    >
                        Sign out
                    </button>
                </div>
            </header>

            <main className="dashboard-content">
                <div>
                    <p className="eyebrow">DASHBOARD</p>

                    <h2>Document processing</h2>

                    <p className="muted">
                        Upload invoices, quotations, and receipts for
                        intelligent extraction and validation.
                    </p>
                </div>

                <div className="upload-card">
                    <h3>Upload document</h3>

                    <p>
                        PDF, PNG, JPG or JPEG. Maximum file size 10 MB.
                    </p>

                    {error && (
                        <div className="error-box">{error}</div>
                    )}

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={handleFileChange}
                        style={{ display: "none" }}
                    />

                    <button
                        className="primary-button"
                        disabled={uploading}
                        onClick={() =>
                            fileInputRef.current?.click()
                        }
                    >
                        {uploading
                            ? "Processing document..."
                            : "Select document"}
                    </button>

                    {uploading && (
                        <p className="processing-message">
                            Running OCR, classification, extraction and
                            validation. Please wait...
                        </p>
                    )}
                </div>

                <section className="history-section">
                    <div className="section-heading">
                        <div>
                            <h3>Recent documents</h3>
                            <p className="muted">
                                Documents uploaded by your account.
                            </p>
                        </div>
                    </div>

                    {documents.length === 0 ? (
                        <div className="empty-state">
                            <h4>No documents yet</h4>
                            <p>
                                Upload your first document to begin
                                processing.
                            </p>
                        </div>
                    ) : (
                        <div className="document-table-wrapper">
                            <table className="document-table">
                                <thead>
                                    <tr>
                                        <th>Document</th>
                                        <th>Type</th>
                                        <th>Confidence</th>
                                        <th>Processing</th>
                                        <th>Review</th>
                                        <th>Uploaded</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {documents.map((document) => (
                                        <tr
                                            key={document.id}
                                            className="clickable-row"
                                            onClick={() =>
                                                navigate(`/documents/${document.id}`)
                                            }
                                        >
                                            <td>
                                                <strong>
                                                    {document.original_filename}
                                                </strong>
                                            </td>

                                            <td>
                                                {document.predicted_type || "—"}
                                            </td>

                                            <td>
                                                {formatConfidence(
                                                    document.classification_confidence
                                                )}
                                            </td>

                                            <td>
                                                <span className="status-badge">
                                                    {document.processing_status}
                                                </span>
                                            </td>

                                            <td>
                                                {document.review_status || "—"}
                                            </td>

                                            <td>
                                                {formatDate(document.created_at)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}