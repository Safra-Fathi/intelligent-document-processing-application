import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

export default function Register() {
    const navigate = useNavigate();

    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] =
        useState("");

    const [showPassword, setShowPassword] =
        useState(false);

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (
        event: React.FormEvent<HTMLFormElement>
    ) => {
        event.preventDefault();

        setError("");

        const trimmedName = fullName.trim();
        const trimmedEmail = email.trim();

        if (trimmedName.length < 2) {
            setError(
                "Please enter your full name."
            );
            return;
        }

        if (password.length < 8) {
            setError(
                "Password must contain at least 8 characters."
            );
            return;
        }

        if (password !== confirmPassword) {
            setError(
                "Passwords do not match."
            );
            return;
        }

        setLoading(true);

        try {
            await api.post("/auth/register", {
                full_name: trimmedName,
                email: trimmedEmail,
                password,
            });

            navigate("/login", {
                state: {
                    registrationSuccess: true,
                },
            });
        } catch (error: any) {
            const detail =
                error.response?.data?.detail;

            if (typeof detail === "string") {
                setError(detail);
            } else {
                setError(
                    "Unable to create account. Please check your details and try again."
                );
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="brand">
                    <span className="brand-mark">
                        DI
                    </span>

                    <div>
                        <h1>
                            Document Intelligence
                        </h1>

                        <p>
                            AI-powered document
                            processing
                        </p>
                    </div>
                </div>

                <h2>Create account</h2>

                <p className="muted">
                    Create an account to securely
                    upload, process, and review
                    documents.
                </p>

                {error && (
                    <div
                        className="error-box"
                        role="alert"
                    >
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <label htmlFor="full-name">
                        Full name
                    </label>

                    <input
                        id="full-name"
                        type="text"
                        value={fullName}
                        onChange={(event) =>
                            setFullName(
                                event.target.value
                            )
                        }
                        placeholder="Enter your full name"
                        autoComplete="name"
                        maxLength={100}
                        required
                        disabled={loading}
                    />

                    <label htmlFor="email">
                        Email address
                    </label>

                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) =>
                            setEmail(
                                event.target.value
                            )
                        }
                        placeholder="you@example.com"
                        autoComplete="email"
                        required
                        disabled={loading}
                    />

                    <label htmlFor="password">
                        Password
                    </label>

                    <input
                        id="password"
                        type={
                            showPassword
                                ? "text"
                                : "password"
                        }
                        value={password}
                        onChange={(event) =>
                            setPassword(
                                event.target.value
                            )
                        }
                        placeholder="Minimum 8 characters"
                        autoComplete="new-password"
                        minLength={8}
                        maxLength={128}
                        required
                        disabled={loading}
                    />

                    <label htmlFor="confirm-password">
                        Confirm password
                    </label>

                    <input
                        id="confirm-password"
                        type={
                            showPassword
                                ? "text"
                                : "password"
                        }
                        value={confirmPassword}
                        onChange={(event) =>
                            setConfirmPassword(
                                event.target.value
                            )
                        }
                        placeholder="Re-enter your password"
                        autoComplete="new-password"
                        minLength={8}
                        maxLength={128}
                        required
                        disabled={loading}
                    />

                    <label
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            cursor: "pointer",
                            marginTop: "4px",
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={showPassword}
                            onChange={(event) =>
                                setShowPassword(
                                    event.target.checked
                                )
                            }
                            disabled={loading}
                            style={{
                                width: "auto",
                                margin: 0,
                            }}
                        />

                        <span>
                            Show passwords
                        </span>
                    </label>

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
                    <Link to="/login">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}