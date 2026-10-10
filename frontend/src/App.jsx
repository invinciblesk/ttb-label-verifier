import { useState } from "react";
import "./App.css";

const initialForm = {
  brand_name: "",
  class_type: "",
  alcohol_content: "",
  net_contents: "",
  producer: "",
  country_of_origin: "",
};

function App() {
  const [mode, setMode] = useState("single");

  const [formData, setFormData] = useState(initialForm);
  const [labelImage, setLabelImage] = useState(null);
  const [result, setResult] = useState(null);

  const [manifest, setManifest] = useState(null);
  const [batchImages, setBatchImages] = useState([]);
  const [batchResult, setBatchResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSingleSubmit = async (event) => {
    event.preventDefault();

    if (!labelImage) {
      setError("Please select a label image.");
      return;
    }

    setError("");
    setResult(null);
    setLoading(true);

    const data = new FormData();

    Object.entries(formData).forEach(([key, value]) => {
      data.append(key, value);
    });

    data.append("label_image", labelImage);

    try {
      const response = await fetch("/verify", {
        method: "POST",
        body: data,
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(
          responseData.detail || "Verification could not be completed."
        );
      }

      setResult(responseData);
    } catch (err) {
      setError(err.message || "Unable to contact the verification service.");
    } finally {
      setLoading(false);
    }
  };

  const handleBatchSubmit = async (event) => {
    event.preventDefault();

    if (!manifest) {
      setError("Please select a CSV manifest.");
      return;
    }

    if (batchImages.length === 0) {
      setError("Please select at least one label image.");
      return;
    }

    setError("");
    setBatchResult(null);
    setLoading(true);

    const data = new FormData();

    data.append("manifest", manifest);

    batchImages.forEach((image) => {
      data.append("label_images", image);
    });

    try {
      const response = await fetch(
        "/verify-batch",
        {
          method: "POST",
          body: data,
        }
      );

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(
          responseData.detail || "Batch verification could not be completed."
        );
      }

      setBatchResult(responseData);
    } catch (err) {
      setError(err.message || "Unable to process the batch.");
    } finally {
      setLoading(false);
    }
  };

  const displayDetected = (value) => {
    if (value === null || value === undefined) {
      return "Not detected";
    }

    if (Array.isArray(value)) {
      return value.length ? value.join(", ") : "Not detected";
    }

    return value;
  };

  const displayStatus = (status) => {
    if (status === "PASS") return "Match";
    if (status === "REVIEW") return "Review";
    return "Potential issue";
  };

  const renderChecks = (checks) => (
    <div className="check-list">
      {checks.map((check) => (
        <article
          key={check.field}
          className={`check-card status-${check.status.toLowerCase()}`}
        >
          <div className="check-heading">
            <h3>{check.field}</h3>

            <span
              className={`badge badge-${check.status.toLowerCase()}`}
            >
              {displayStatus(check.status)}
            </span>
          </div>

          <dl>
            <div>
              <dt>Application</dt>
              <dd>{check.expected}</dd>
            </div>

            <div>
              <dt>Detected on label</dt>
              <dd>{displayDetected(check.detected)}</dd>
            </div>

            {check.similarity !== undefined && (
              <div>
                <dt>Text similarity</dt>
                <dd>{check.similarity}%</dd>
              </div>
            )}
          </dl>

          {check.reason && (
            <p className="check-reason">{check.reason}</p>
          )}
        </article>
      ))}
    </div>
  );

  return (
    <main className="page">
      <div className="container">
        <header className="header">
          <p className="eyebrow">Label Compliance Prototype</p>

          <h1>Alcohol Label Verification</h1>

          <p className="intro">
            Compare application information with text detected on uploaded
            alcohol labels.
          </p>
        </header>

        <div className="mode-switch">
          <button
            type="button"
            className={mode === "single" ? "mode-button active" : "mode-button"}
            onClick={() => {
              setMode("single");
              setError("");
            }}
          >
            Single Label
          </button>

          <button
            type="button"
            className={mode === "batch" ? "mode-button active" : "mode-button"}
            onClick={() => {
              setMode("batch");
              setError("");
            }}
          >
            Batch Upload
          </button>
        </div>

        {mode === "single" && (
          <>
            <form onSubmit={handleSingleSubmit}>
              <section className="card">
                <h2>Application Information</h2>

                <div className="form-grid">
                  <label>
                    Brand Name
                    <input
                      name="brand_name"
                      value={formData.brand_name}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    Class / Type
                    <input
                      name="class_type"
                      value={formData.class_type}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    Alcohol Content
                    <input
                      name="alcohol_content"
                      placeholder="Example: 45%"
                      value={formData.alcohol_content}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    Net Contents
                    <input
                      name="net_contents"
                      placeholder="Example: 750 mL"
                      value={formData.net_contents}
                      onChange={handleChange}
                      required
                    />
                  </label>

                  <label>
                    Producer / Bottler
                    <input
                      name="producer"
                      value={formData.producer}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Country of Origin
                    <input
                      name="country_of_origin"
                      placeholder="For imported products"
                      value={formData.country_of_origin}
                      onChange={handleChange}
                    />
                  </label>
                </div>
              </section>

              <section className="card">
                <h2>Label Image</h2>

                <p className="helper">
                  Upload a clear JPG, PNG, or other supported image.
                </p>

                <input
                  className="file-input"
                  type="file"
                  accept="image/*"
                  onChange={(event) => {
                    setLabelImage(event.target.files[0]);
                    setResult(null);
                    setError("");
                  }}
                />

                {labelImage && (
                  <p className="selected-file">
                    Selected: <strong>{labelImage.name}</strong>
                  </p>
                )}
              </section>

              {error && <div className="error-message">{error}</div>}

              <button
                className="verify-button"
                type="submit"
                disabled={loading}
              >
                {loading ? "Checking label..." : "Verify Label"}
              </button>
            </form>

            {result && (
              <section className="results-section">
                <div
                  className={
                    result.overall_status === "CHECKS PASSED"
                      ? "overall overall-pass"
                      : "overall overall-review"
                  }
                >
                  <div>
                    <p className="result-label">Verification result</p>

                    <h2>
                      {result.overall_status === "CHECKS PASSED"
                        ? "Checks passed"
                        : "Manual review required"}
                    </h2>
                  </div>

                  <span className="result-count">
                    {
                      result.checks.filter(
                        (check) => check.status === "PASS"
                      ).length
                    }
                    /{result.checks.length} checks passed
                  </span>
                </div>

                {result.processing_time_ms !== undefined && (
                  <p
                    className={`performance-note ${
                      result.performance_target_met
                        ? "performance-pass"
                        : "performance-review"
                    }`}
                  >
                    Processed in{" "}
                    <strong>
                      {(result.processing_time_ms / 1000).toFixed(2)} seconds
                    </strong>
                    {" · "}
                    {result.performance_target_met
                      ? "Within 5-second target"
                      : "Exceeded 5-second target"}
                  </p>
                )}

                {renderChecks(result.checks)}

                <details className="ocr-details">
                  <summary>View extracted label text</summary>
                  <pre>{result.ocr?.text || "No text detected."}</pre>
                </details>
              </section>
            )}
          </>
        )}

        {mode === "batch" && (
          <>
            <form onSubmit={handleBatchSubmit}>
              <section className="card">
                <h2>Batch Manifest</h2>

                <p className="helper">
                  Upload a CSV containing the application information for each
                  label.
                </p>

                <input
                  className="file-input"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) => {
                    setManifest(event.target.files[0]);
                    setBatchResult(null);
                    setError("");
                  }}
                />

                {manifest && (
                  <p className="selected-file">
                    Manifest: <strong>{manifest.name}</strong>
                  </p>
                )}
              </section>

              <section className="card">
                <h2>Label Images</h2>

                <p className="helper">
                  Select the label images referenced by filename in the CSV.
                  Prototype limit: 20 labels per batch.
                </p>

                <input
                  className="file-input"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(event) => {
                    setBatchImages(Array.from(event.target.files));
                    setBatchResult(null);
                    setError("");
                  }}
                />

                {batchImages.length > 0 && (
                  <div className="selected-files">
                    <strong>{batchImages.length} image(s) selected</strong>

                    <ul>
                      {batchImages.map((image) => (
                        <li key={image.name}>{image.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>

              {error && <div className="error-message">{error}</div>}

              <button
                className="verify-button"
                type="submit"
                disabled={loading}
              >
                {loading ? "Processing batch..." : "Verify Batch"}
              </button>
            </form>

            {batchResult && (
              <section className="results-section">
                <div className="overall overall-pass">
                  <div>
                    <p className="result-label">Batch result</p>
                    <h2>{batchResult.batch_size} label(s) processed</h2>
                  </div>
                </div>

                <div className="batch-results">
                  {batchResult.results.map((item, index) => (
                    <article className="batch-card" key={`${item.filename}-${index}`}>
                      <div className="check-heading">
                        <h3>{item.filename || "Unknown file"}</h3>

                        <span
                          className={
                            item.overall_status === "CHECKS PASSED"
                              ? "badge badge-pass"
                              : item.overall_status === "ERROR"
                              ? "badge badge-fail"
                              : "badge badge-review"
                          }
                        >
                          {item.overall_status === "CHECKS PASSED"
                            ? "Checks passed"
                            : item.overall_status === "ERROR"
                            ? "Error"
                            : "Manual review"}
                        </span>
                      </div>

                      {item.error ? (
                        <p className="check-reason">{item.error}</p>
                      ) : (
                        <>
                          <p>
                            <strong>
                              {item.passed}/{item.total_checks}
                            </strong>{" "}
                            checks passed
                          </p>

                          {item.processing_time_ms !== undefined && (
                            <p
                              className={`performance-note ${
                                item.performance_target_met
                                  ? "performance-pass"
                                  : "performance-review"
                              }`}
                            >
                              Processed in{" "}
                              <strong>
                                {(item.processing_time_ms / 1000).toFixed(2)} seconds
                              </strong>
                              {" · "}
                              {item.performance_target_met
                                ? "Within 5-second target"
                                : "Exceeded 5-second target"}
                            </p>
                          )}

                          <details>
                            <summary>View verification details</summary>

                            <div className="batch-check-details">
                              {renderChecks(item.checks)}

                              <details className="ocr-details">
                                <summary>View extracted label text</summary>
                                <pre>
                                  {item.ocr?.text || "No text detected."}
                                </pre>
                              </details>
                            </div>
                          </details>
                        </>
                      )}
                    </article>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}

export default App;
