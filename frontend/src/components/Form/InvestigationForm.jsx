import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import {
  loadInvestigation,
  reviewCause,
  saveInvestigation,
} from '../../api/rca'
import { setForm } from '../../store/formSlice'

const summaryFields = [
  ['deviation_id', 'Deviation reference'],
  ['title', 'Investigation title'],
  ['product_name', 'Product'],
  ['batch_number', 'Batch number'],
  ['process_step', 'Process step'],
  ['equipment_id', 'Equipment'],
  ['date_detected', 'Date detected'],
  ['reported_by', 'Reported by'],
  ['problem_statement', 'Problem statement'],
  ['affected_quantity', 'Affected quantity'],
  ['immediate_containment', 'Immediate containment'],
]

const causeCategories = [
  'Man',
  'Machine',
  'Method',
  'Material',
  'Measurement',
  'Environment',
]

function displayValue(value) {
  return value === null || value === undefined || value === ''
    ? 'Not provided'
    : value
}

function InvestigationForm() {
  const dispatch = useDispatch()
  const form = useSelector((state) => state.form)
  const [investigationId, setInvestigationId] = useState('')
  const [loadId, setLoadId] = useState('')
  const [noConfirmedRootCause, setNoConfirmedRootCause] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [reviewingCauseId, setReviewingCauseId] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const currentForm = {
    summary: form.summary,
    risk: form.risk,
    analysis: form.analysis,
  }
  const causes = form.analysis.causes
  const hasConfirmedCause = causes.some((cause) => cause.status === 'confirmed')
  const canSave = hasConfirmedCause || noConfirmedRootCause

  async function handleSave(event) {
    event.preventDefault()
    if (!canSave || isSaving) return

    setError('')
    setNotice('')
    setIsSaving(true)

    try {
      const result = await saveInvestigation(
        currentForm,
        noConfirmedRootCause,
      )
      setInvestigationId(String(result.id))
      setLoadId(String(result.id))
      setNotice(`Investigation ${result.id} saved.`)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not save the investigation.',
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function handleLoad(event) {
    event.preventDefault()
    const id = loadId.trim()
    if (!id || isLoading) return

    setError('')
    setNotice('')
    setIsLoading(true)

    try {
      const result = await loadInvestigation(id)
      dispatch(setForm(result.form))
      setInvestigationId(String(result.id))
      setNoConfirmedRootCause(false)
      setNotice(`Investigation ${result.id} loaded.`)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not load the investigation.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCauseReview(cause, status) {
    if (reviewingCauseId) return

    setError('')
    setNotice('')
    setReviewingCauseId(cause.id)

    try {
      if (investigationId) {
        await reviewCause(investigationId, cause.id, status)
      }

      dispatch(
        setForm({
          ...currentForm,
          analysis: {
            ...form.analysis,
            causes: causes.map((item) =>
              item.id === cause.id ? { ...item, status } : item,
            ),
          },
        }),
      )
      setNotice(
        investigationId
          ? `Cause ${cause.id} marked ${status}.`
          : `Cause ${cause.id} marked ${status}. Save the investigation to record this review.`,
      )
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not update the cause review.',
      )
    } finally {
      setReviewingCauseId(null)
    }
  }

  return (
    <section className="investigation-panel" aria-label="RCA investigation">
      <header className="form-header">
        <div>
          <p className="eyebrow">QUALITY INVESTIGATION</p>
          <h1>Root Cause Analysis</h1>
          <p className="form-guidance">Use the co-pilot to update this form.</p>
        </div>

        <form className="load-form" onSubmit={handleLoad}>
          <label htmlFor="load-investigation-id">Load saved investigation</label>
          <div>
            <input
              id="load-investigation-id"
              type="number"
              min="1"
              value={loadId}
              onChange={(event) => setLoadId(event.target.value)}
              placeholder="ID"
            />
            <button type="submit" disabled={!loadId.trim() || isLoading}>
              {isLoading ? 'Loading…' : 'Load'}
            </button>
          </div>
        </form>
      </header>

      {error && <p className="form-message form-error" role="alert">{error}</p>}
      {notice && <p className="form-message form-notice" role="status">{notice}</p>}

      <section className="form-section">
        <h2>Investigation summary</h2>
        <dl className="summary-grid">
          {summaryFields.map(([key, label]) => (
            <div
              className={form.highlighted.includes(`summary.${key}`) ? 'field-highlight' : ''}
              key={key}
            >
              <dt>{label}</dt>
              <dd>{displayValue(form.summary[key])}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="form-section">
        <h2>Risk assessment</h2>
        <dl className="summary-grid">
          <div>
            <dt>Severity</dt>
            <dd>{displayValue(form.risk.severity)}</dd>
          </div>
          <div>
            <dt>Batch impact</dt>
            <dd>{displayValue(form.risk.batch_impact)}</dd>
          </div>
          <div>
            <dt>Recommended next action</dt>
            <dd>{displayValue(form.risk.recommended_next_action)}</dd>
          </div>
          <div>
            <dt>Regulatory reportability</dt>
            <dd>{displayValue(form.risk.regulatory_reportability)}</dd>
          </div>
          <div>
            <dt>Rationale</dt>
            <dd>{displayValue(form.risk.rationale)}</dd>
          </div>
        </dl>
      </section>

      <section className="form-section">
        <h2>5 Whys</h2>
        {form.analysis.whys.length === 0 ? (
          <p className="empty-state">No Why analysis yet.</p>
        ) : (
          <ol className="why-list">
            {form.analysis.whys.map((why) => (
              <li key={`${why.level}-${why.question}`}>
                <h3>{why.question}</h3>
                <p>{why.answer}</p>
                {why.evidence_needed && (
                  <p className="supporting-note">
                    Evidence to check: {why.evidence_needed}
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="form-section">
        <h2>Fishbone categories</h2>
        <div className="fishbone-grid">
          {causeCategories.map((category) => {
            const categoryCauses = causes.filter(
              (cause) => cause.category === category,
            )

            return (
              <div className="fishbone-category" key={category}>
                <h3>{category}</h3>
                {categoryCauses.length === 0 ? (
                  <p>None identified</p>
                ) : (
                  <ul>
                    {categoryCauses.map((cause) => (
                      <li key={cause.id}>{cause.text}</li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })}
        </div>
      </section>

      <section className="form-section">
        <h2>Potential causes</h2>
        <p className="suggestion-banner">
          AI suggestions, not confirmed root causes. Qualified personnel must
          review the evidence.
        </p>

        {causes.length === 0 ? (
          <p className="empty-state">No potential causes identified yet.</p>
        ) : (
          <div className="cause-list">
            {causes.map((cause) => (
              <article className="cause-card" key={cause.id}>
                <div className="cause-heading">
                  <h3>{cause.text}</h3>
                  <span className={`cause-status cause-status--${cause.status}`}>
                    {cause.status}
                  </span>
                </div>
                <p>
                  {cause.category} · {cause.confidence} confidence
                  {cause.is_probable_root ? ' · Possible root cause' : ''}
                </p>
                {cause.source_quote && (
                  <details>
                    <summary>Why? View supporting quote</summary>
                    <blockquote>{cause.source_quote}</blockquote>
                  </details>
                )}
                <div className="review-actions">
                  <button
                    type="button"
                    disabled={Boolean(reviewingCauseId)}
                    onClick={() => handleCauseReview(cause, 'confirmed')}
                  >
                    Confirm
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(reviewingCauseId)}
                    onClick={() => handleCauseReview(cause, 'rejected')}
                  >
                    Reject
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="form-section">
        <h2>Evidence to review</h2>
        {form.analysis.evidence.length === 0 ? (
          <p className="empty-state">No evidence items listed yet.</p>
        ) : (
          <ul className="evidence-list">
            {form.analysis.evidence.map((item, index) => (
              <li className={`evidence-item evidence-item--${item.status}`} key={`${item.item}-${index}`}>
                <strong>{item.status === 'missing' ? 'Missing' : 'Provided'}:</strong>{' '}
                {item.item}
                {item.why_needed && <p>{item.why_needed}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="form-section">
        <h2>CAPA recommendations</h2>
        {form.analysis.capas.length === 0 ? (
          <p className="empty-state">No CAPA recommendations yet.</p>
        ) : (
          <div className="capa-list">
            {form.analysis.capas.map((capa) => (
              <article className="capa-card" key={capa.id}>
                <h3>{capa.type} action</h3>
                <p>{capa.action}</p>
                <p><strong>Rationale:</strong> {capa.rationale}</p>
                <p>
                  <strong>Effectiveness check:</strong> {capa.effectiveness_check}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      <form className="save-bar" onSubmit={handleSave}>
        <label>
          <input
            type="checkbox"
            checked={noConfirmedRootCause}
            onChange={(event) => setNoConfirmedRootCause(event.target.checked)}
          />
          No confirmed root cause yet
        </label>
        <button type="submit" disabled={!canSave || isSaving}>
          {isSaving ? 'Saving…' : 'Save investigation'}
        </button>
      </form>
    </section>
  )
}

export default InvestigationForm