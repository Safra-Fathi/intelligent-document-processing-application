import {
    Fragment,
    useEffect,
    useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api";

interface DocumentData {
    id: number;
    original_filename: string;
    mime_type: string;
    size_bytes: number;
    processing_status: string;
    predicted_type: string | null;
    classification_confidence: number | null;
    review_status: string | null;
    pipeline_version: string | null;
    classifier_version: string | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

interface ExtractedField {
    id: number;
    field_name: string;
    original_value: string | null;
    confidence: number | null;

    // Latest human correction returned by the backend.
    corrected_value: string | null;
    correction_reason: string | null;
    corrected_at: string | null;
    corrected_by_user_id: number | null;
}

interface ValidationIssue {
    id: number;
    field_name: string | null;
    issue_code: string;
    severity: string;
    message: string;
}

interface AuditEvent {
    id: number;
    document_id: number;
    user_id: number | null;
    event_type: string;
    details: string | null;
    created_at: string;
}

interface ProcessingResult {
    document: DocumentData;
    fields: ExtractedField[];
    validation_issues: ValidationIssue[];
}

export default function DocumentDetails() {
    const { documentId } = useParams();
    const navigate = useNavigate();

    const [result, setResult] =
        useState<ProcessingResult | null>(null);

    const [auditEvents, setAuditEvents] =
        useState<AuditEvent[]>([]);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");

    // Preview state.
    const [previewUrl, setPreviewUrl] =
        useState<string | null>(null);

    const [previewLoading, setPreviewLoading] =
        useState(true);

    const [previewError, setPreviewError] =
        useState("");

    // Correction state.
    const [editingFieldId, setEditingFieldId] =
        useState<number | null>(null);

    const [correctedValue, setCorrectedValue] =
        useState("");

    const [correctionReason, setCorrectionReason] =
        useState("");

    const [savingCorrection, setSavingCorrection] =
        useState(false);

    const [correctionMessage, setCorrectionMessage] =
        useState("");

    const loadData = async () => {
        try {
            setError("");

            const [resultResponse, auditResponse] =
                await Promise.all([
                    api.get(
                        `/documents/${documentId}/result`
                    ),
                    api.get(
                        `/documents/${documentId}/audit`
                    ),
                ]);

            setResult(resultResponse.data);
            setAuditEvents(auditResponse.data);
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                "Unable to load document result."
            );
        } finally {
            setLoading(false);
        }
    };

    const loadPreview = async () => {
        try {
            setPreviewLoading(true);
            setPreviewError("");

            const response = await api.get(
                `/documents/${documentId}/file`,
                {
                    responseType: "blob",
                }
            );

            const objectUrl = URL.createObjectURL(
                response.data
            );

            setPreviewUrl(objectUrl);
        } catch (err: any) {
            setPreviewError(
                err.response?.data?.detail ||
                "Unable to load document preview."
            );
        } finally {
            setPreviewLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        loadPreview();

        return () => {
            // Cleanup is also performed when previewUrl changes
            // in the dedicated effect below.
        };
    }, [documentId]);

    useEffect(() => {
        return () => {
            if (previewUrl) {
                URL.revokeObjectURL(previewUrl);
            }
        };
    }, [previewUrl]);

    const formatConfidence = (
        value: number | null
    ) => {
        if (value === null) {
            return "—";
        }

        return `${(value * 100).toFixed(1)}%`;
    };

    const readableFieldName = (
        value: string
    ) => {
        return value
            .split("_")
            .map(
                (word) =>
                    word.charAt(0).toUpperCase() +
                    word.slice(1)
            )
            .join(" ");
    };

    const formatDate = (
        value: string
    ) => {
        return new Date(value).toLocaleString();
    };

    const getConfidenceLevel = (
        confidence: number | null
    ) => {
        const value = confidence ?? 0;

        if (value >= 0.9) {
            return "High";
        }

        if (value >= 0.7) {
            return "Medium";
        }

        return "Low";
    };

    const startCorrection = (
        field: ExtractedField
    ) => {
        setEditingFieldId(field.id);

        // If this field was already corrected, start from
        // the latest human-reviewed value rather than the
        // original model output.
        setCorrectedValue(
            field.corrected_value ??
            field.original_value ??
            ""
        );

        setCorrectionReason(
            field.correction_reason ?? ""
        );

        setCorrectionMessage("");
    };

    const cancelCorrection = () => {
        setEditingFieldId(null);
        setCorrectedValue("");
        setCorrectionReason("");
        setCorrectionMessage("");
    };

    const saveCorrection = async (
        fieldId: number
    ) => {
        if (!correctedValue.trim()) {
            setCorrectionMessage(
                "Corrected value is required."
            );

            return;
        }

        try {
            setSavingCorrection(true);
            setCorrectionMessage("");

            await api.post(
                `/documents/${documentId}/fields/${fieldId}/corrections`,
                {
                    corrected_value:
                        correctedValue.trim(),

                    reason:
                        correctionReason.trim() ||
                        null,
                }
            );

            setEditingFieldId(null);
            setCorrectedValue("");
            setCorrectionReason("");

            await loadData();

            setCorrectionMessage(
                "Correction saved successfully."
            );
        } catch (err: any) {
            setCorrectionMessage(
                err.response?.data?.detail ||
                "Unable to save correction."
            );
        } finally {
            setSavingCorrection(false);
        }
    };

    if (loading) {
        return (
            <div className="page-message">
                Loading document result...
            </div>
        );
    }

    if (error || !result) {
        return (
            <div className="page-message">
                <div className="error-box">
                    {error ||
                        "Document not found."}
                </div>

                <button
                    className="secondary-button"
                    onClick={() =>
                        navigate("/")
                    }
                >
                    Back to dashboard
                </button>
            </div>
        );
    }

    const document = result.document;

    const isProcessed =
        document.processing_status ===
        "COMPLETED";

    const isPdf =
        document.mime_type ===
        "application/pdf";

    const isImage =
        document.mime_type.startsWith(
            "image/"
        );

    return (
        <div className="details-page">
            <header className="topbar">
                <div className="brand">
                    <span className="brand-mark">
                        DI
                    </span>

                    <div>
                        <h1>
                            Document Intelligence
                        </h1>
                    </div>
                </div>

                <button
                    className="secondary-button"
                    onClick={() =>
                        navigate("/")
                    }
                >
                    Back to dashboard
                </button>
            </header>

            <main className="details-content">
                <div className="details-heading">
                    <p className="eyebrow">
                        DOCUMENT RESULT
                    </p>

                    <h2>
                        {document.original_filename}
                    </h2>

                    <p className="muted">
                        Processing, extraction,
                        validation and human-review
                        results.
                    </p>
                </div>

                {/* Summary */}

                <section className="summary-grid">
                    <div className="summary-card">
                        <span>
                            Document type
                        </span>

                        <strong>
                            {document.predicted_type ||
                                "—"}
                        </strong>
                    </div>

                    <div className="summary-card">
                        <span>
                            Classification confidence
                        </span>

                        <strong>
                            {formatConfidence(
                                document.classification_confidence
                            )}
                        </strong>
                    </div>

                    <div className="summary-card">
                        <span>
                            Processing status
                        </span>

                        <strong>
                            {
                                document.processing_status
                            }
                        </strong>
                    </div>

                    <div className="summary-card">
                        <span>
                            Review status
                        </span>

                        <strong>
                            {document.review_status ||
                                "—"}
                        </strong>
                    </div>
                </section>

                {/* Document preview */}

                <section className="result-section">
                    <div className="section-heading">
                        <div>
                            <h3>
                                Document preview
                            </h3>

                            <p className="muted">
                                Original document uploaded
                                for processing.
                            </p>
                        </div>
                    </div>

                    {previewLoading && (
                        <div className="empty-state">
                            Loading document preview...
                        </div>
                    )}

                    {!previewLoading &&
                        previewError && (
                            <div className="error-box">
                                {previewError}
                            </div>
                        )}

                    {!previewLoading &&
                        !previewError &&
                        previewUrl && (
                            <div className="document-preview">
                                {isPdf && (
                                    <iframe
                                        src={previewUrl}
                                        title={`Preview of ${document.original_filename}`}
                                        className="pdf-preview"
                                    />
                                )}

                                {isImage && (
                                    <img
                                        src={previewUrl}
                                        alt={`Preview of ${document.original_filename}`}
                                        className="image-preview"
                                    />
                                )}

                                {!isPdf &&
                                    !isImage && (
                                        <div className="empty-state">
                                            Preview is not
                                            available for this
                                            file type.
                                        </div>
                                    )}
                            </div>
                        )}
                </section>

                {/* Processing errors */}

                {document.processing_status ===
                    "FAILED" && (
                        <section className="result-section">
                            <div className="error-box">
                                {document.error_message ||
                                    "Document processing failed."}
                            </div>
                        </section>
                    )}

                {/* Unprocessed state */}

                {document.processing_status ===
                    "UPLOADED" && (
                        <section className="result-section">
                            <div className="unprocessed-box">
                                This document has been
                                uploaded but has not been
                                processed yet.
                            </div>
                        </section>
                    )}

                {/* Extracted fields */}

                {isProcessed && (
                    <section className="result-section">
                        <div className="section-heading">
                            <div>
                                <h3>
                                    Extracted fields
                                </h3>

                                <p className="muted">
                                    The original model output
                                    is preserved separately
                                    from human corrections.
                                </p>
                            </div>
                        </div>

                        {correctionMessage && (
                            <div className="correction-status">
                                {correctionMessage}
                            </div>
                        )}

                        {result.fields.length ===
                            0 ? (
                            <div className="empty-state">
                                No fields were extracted.
                            </div>
                        ) : (
                            <div className="document-table-wrapper">
                                <table className="document-table">
                                    <thead>
                                        <tr>
                                            <th>Field</th>

                                            <th>
                                                Original value
                                            </th>

                                            <th>
                                                Current value
                                            </th>

                                            <th>
                                                Confidence
                                            </th>

                                            <th>
                                                Review
                                            </th>

                                            <th>
                                                Action
                                            </th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {result.fields.map(
                                            (field) => {
                                                const level =
                                                    getConfidenceLevel(
                                                        field.confidence
                                                    );

                                                const hasCorrection =
                                                    field.corrected_value !==
                                                    null;

                                                const currentValue =
                                                    field.corrected_value ??
                                                    field.original_value;

                                                return (
                                                    <Fragment
                                                        key={field.id}
                                                    >
                                                        <tr>
                                                            <td>
                                                                <strong>
                                                                    {readableFieldName(
                                                                        field.field_name
                                                                    )}
                                                                </strong>
                                                            </td>

                                                            <td>
                                                                {field.original_value ||
                                                                    "Not found"}
                                                            </td>

                                                            <td>
                                                                <div className="current-value-cell">
                                                                    <span>
                                                                        {currentValue ||
                                                                            "Not found"}
                                                                    </span>

                                                                    {hasCorrection && (
                                                                        <span className="corrected-badge">
                                                                            Corrected
                                                                        </span>
                                                                    )}

                                                                    {hasCorrection &&
                                                                        field.correction_reason && (
                                                                            <small className="correction-note">
                                                                                Reason:{" "}
                                                                                {
                                                                                    field.correction_reason
                                                                                }
                                                                            </small>
                                                                        )}

                                                                    {hasCorrection &&
                                                                        field.corrected_at && (
                                                                            <small className="correction-note">
                                                                                Corrected:{" "}
                                                                                {formatDate(
                                                                                    field.corrected_at
                                                                                )}
                                                                            </small>
                                                                        )}
                                                                </div>
                                                            </td>

                                                            <td>
                                                                {formatConfidence(
                                                                    field.confidence
                                                                )}
                                                            </td>

                                                            <td>
                                                                <span
                                                                    className={`confidence-badge confidence-${level.toLowerCase()}`}
                                                                >
                                                                    {level}
                                                                </span>
                                                            </td>

                                                            <td>
                                                                <button
                                                                    type="button"
                                                                    className="small-button"
                                                                    onClick={() =>
                                                                        startCorrection(
                                                                            field
                                                                        )
                                                                    }
                                                                >
                                                                    {hasCorrection
                                                                        ? "Correct again"
                                                                        : "Correct"}
                                                                </button>
                                                            </td>
                                                        </tr>

                                                        {editingFieldId ===
                                                            field.id && (
                                                                <tr>
                                                                    <td
                                                                        colSpan={
                                                                            6
                                                                        }
                                                                        className="correction-cell"
                                                                    >
                                                                        <div className="correction-form">
                                                                            <div>
                                                                                <label>
                                                                                    Corrected
                                                                                    value
                                                                                </label>

                                                                                <input
                                                                                    type="text"
                                                                                    value={
                                                                                        correctedValue
                                                                                    }
                                                                                    onChange={(
                                                                                        e
                                                                                    ) =>
                                                                                        setCorrectedValue(
                                                                                            e
                                                                                                .target
                                                                                                .value
                                                                                        )
                                                                                    }
                                                                                    placeholder="Enter corrected value"
                                                                                />
                                                                            </div>

                                                                            <div>
                                                                                <label>
                                                                                    Reason
                                                                                    (optional)
                                                                                </label>

                                                                                <input
                                                                                    type="text"
                                                                                    value={
                                                                                        correctionReason
                                                                                    }
                                                                                    onChange={(
                                                                                        e
                                                                                    ) =>
                                                                                        setCorrectionReason(
                                                                                            e
                                                                                                .target
                                                                                                .value
                                                                                        )
                                                                                    }
                                                                                    placeholder="Why is this value being corrected?"
                                                                                />
                                                                            </div>

                                                                            <div className="correction-actions">
                                                                                <button
                                                                                    type="button"
                                                                                    className="small-button"
                                                                                    disabled={
                                                                                        savingCorrection
                                                                                    }
                                                                                    onClick={() =>
                                                                                        saveCorrection(
                                                                                            field.id
                                                                                        )
                                                                                    }
                                                                                >
                                                                                    {savingCorrection
                                                                                        ? "Saving..."
                                                                                        : "Save correction"}
                                                                                </button>

                                                                                <button
                                                                                    type="button"
                                                                                    className="secondary-button"
                                                                                    disabled={
                                                                                        savingCorrection
                                                                                    }
                                                                                    onClick={
                                                                                        cancelCorrection
                                                                                    }
                                                                                >
                                                                                    Cancel
                                                                                </button>
                                                                            </div>
                                                                        </div>
                                                                    </td>
                                                                </tr>
                                                            )}
                                                    </Fragment>
                                                );
                                            }
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                )}

                {/* Validation */}

                {isProcessed && (
                    <section className="result-section">
                        <div className="section-heading">
                            <div>
                                <h3>
                                    Validation issues
                                </h3>

                                <p className="muted">
                                    Business-rule and
                                    confidence checks
                                    requiring attention.
                                </p>
                            </div>
                        </div>

                        {result.validation_issues
                            .length === 0 ? (
                            <div className="success-box">
                                No validation issues were
                                detected.
                            </div>
                        ) : (
                            <div className="issue-list">
                                {result.validation_issues.map(
                                    (issue) => (
                                        <div
                                            className="issue-card"
                                            key={issue.id}
                                        >
                                            <div>
                                                <span
                                                    className={`severity severity-${issue.severity.toLowerCase()}`}
                                                >
                                                    {issue.severity}
                                                </span>

                                                <strong>
                                                    {
                                                        issue.issue_code
                                                    }
                                                </strong>
                                            </div>

                                            <p>
                                                {issue.message}
                                            </p>

                                            {issue.field_name && (
                                                <small>
                                                    Field:{" "}
                                                    {readableFieldName(
                                                        issue.field_name
                                                    )}
                                                </small>
                                            )}
                                        </div>
                                    )
                                )}
                            </div>
                        )}
                    </section>
                )}

                {/* Audit history */}

                <section className="result-section">
                    <div className="section-heading">
                        <div>
                            <h3>
                                Audit history
                            </h3>

                            <p className="muted">
                                Processing and human-review
                                activity for this document.
                            </p>
                        </div>
                    </div>

                    {auditEvents.length === 0 ? (
                        <div className="empty-state">
                            No audit events recorded yet.
                        </div>
                    ) : (
                        <div className="audit-list">
                            {auditEvents.map(
                                (event) => (
                                    <div
                                        className="audit-item"
                                        key={event.id}
                                    >
                                        <div>
                                            <strong>
                                                {readableFieldName(
                                                    event.event_type
                                                )}
                                            </strong>

                                            <p>
                                                {event.details ||
                                                    "No additional details."}
                                            </p>
                                        </div>

                                        <time>
                                            {formatDate(
                                                event.created_at
                                            )}
                                        </time>
                                    </div>
                                )
                            )}
                        </div>
                    )}
                </section>

                {/* Processing metadata */}

                <section className="result-section">
                    <h3>
                        Processing information
                    </h3>

                    <div className="metadata-card">
                        <div>
                            <span>Pipeline</span>

                            <strong>
                                {document.pipeline_version ||
                                    "—"}
                            </strong>
                        </div>

                        <div>
                            <span>Classifier</span>

                            <strong>
                                {document.classifier_version ||
                                    "—"}
                            </strong>
                        </div>

                        <div>
                            <span>File type</span>

                            <strong>
                                {document.mime_type}
                            </strong>
                        </div>

                        <div>
                            <span>Size</span>

                            <strong>
                                {(
                                    document.size_bytes /
                                    1024
                                ).toFixed(1)}{" "}
                                KB
                            </strong>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}