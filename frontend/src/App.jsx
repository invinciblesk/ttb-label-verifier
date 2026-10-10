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
  const [formData, setFormData] = useState(initialForm);
  const [labelImage, setLabelImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
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
      const response = await fetch("http://127.0.0.1:8000/verify", {
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

  return (
    <main className="page">
      <div className="container">
        <header className="header">
          <p className="eyebrow">Label Compliance Prototype</p>
          <h1>Alcohol Label Verification</h1>
          <p className="intro">
            Compare application information with text detected on an uploaded
            alcohol label.
          </p>
        </header>

        <form onSubmit={handleSubmit}>
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

          <button className="verify-button" type="submit" disabled={loading}>
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
                {result.checks.filter((check) => check.status === "PASS").length}
                /{result.checks.length} checks passed
              </span>
            </div>

            <div className="check-list">
              {result.checks.map((check) => (
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

            <details className="ocr-details">
              <summary>View extracted label text</summary>
              <pre>{result.ocr?.text || "No text detected."}</pre>
            </details>
          </section>
        )}
      </div>
    </main>
  );
}

export default App;
