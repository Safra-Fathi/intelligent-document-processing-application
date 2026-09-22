import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

export default function Register() {
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (
        event: React.FormEvent<HTMLFormElement>
    ) => {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            await api.post("/auth/register", {
                email,
                password,
            });

            navigate("/login");
        } catch (error: any) {
            setError(
                error.response?.data?.detail ||
                "Unable to create account."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="brand">
                    <span className="brand-mark">DI</span>

                    <div>
                        <h1>Document Intelligence</h1>
                        <p>AI-powered document processing</p>
                    </div>
                </div>

                <h2>Create account</h2>

                <p className="muted">
                    Create an account to upload and analyze documents.
                </p>

                {error && <div className="error-box">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <label>Email address</label>

                    <input
                        type="email"
                        value={email}
                        onChange={(event) =>
                            setEmail(event.target.value)
                        }
                        placeholder="you@example.com"
                        required
                    />

                    <label>Password</label>

                    <input
                        type="password"
                        value={password}
                        onChange={(event) =>
                            setPassword(event.target.value)
                        }
                        placeholder="Minimum 8 characters"
                        minLength={8}
                        required
                    />

                    <button
                        className="primary-button"
                        disabled={loading}
                        type="submit"
                    >
                        {loading
                            ? "Creating account..."
                            : "Create account"}
                    </button>
                </form>

                <p className="auth-switch">
                    Already have an account?{" "}
                    <Link to="/login">Sign in</Link>
                </p>
            </div>
        </div>
    );
}