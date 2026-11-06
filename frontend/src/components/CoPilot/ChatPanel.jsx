import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { sendMessage, uploadDoc } from '../../api/rca'
import { addMessage, setLoading } from '../../store/chatSlice'
import {
  clearHighlighted,
  setForm,
  setHighlighted,
} from '../../store/formSlice'

const suggestedPrompts = [
  'Log an investigation from this incident: ',
  'What evidence is still needed?',
  'Explain the suggested causes.',
]

function ChatPanel() {
  const dispatch = useDispatch()
  const form = useSelector((state) => state.form)
  const { messages, isLoading } = useSelector((state) => state.chat)

  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const messageListRef = useRef(null)
  const highlightTimerRef = useRef(null)

  useEffect(() => {
    messageListRef.current?.scrollTo({
      top: messageListRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages])

  useEffect(
    () => () => {
      if (highlightTimerRef.current) {
        clearTimeout(highlightTimerRef.current)
      }
    },
    [],
  )

  function currentForm() {
    return {
      summary: form.summary,
      risk: form.risk,
      analysis: form.analysis,
    }
  }

  function applyResponse(result) {
    dispatch(setForm(result.form))
    dispatch(setHighlighted(result.changed ?? []))

    if (highlightTimerRef.current) {
      clearTimeout(highlightTimerRef.current)
    }

    highlightTimerRef.current = setTimeout(() => {
      dispatch(clearHighlighted())
    }, 2000)

    dispatch(addMessage({ role: 'assistant', content: result.reply }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const text = message.trim()

    if (!text || isLoading) return

    setMessage('')
    setError('')
    dispatch(addMessage({ role: 'user', content: text }))
    dispatch(setLoading(true))

    try {
      const result = await sendMessage(text, currentForm())
      applyResponse(result)
    } catch (requestError) {
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : 'An unexpected error occurred.'

      setError(errorMessage)
      dispatch(
        addMessage({
          role: 'assistant',
          content: `The request failed: ${errorMessage}`,
        }),
      )
    } finally {
      dispatch(setLoading(false))
    }
  }

  async function handleFileChange(event) {
    const file = event.target.files?.[0]
    event.target.value = ''

    if (!file || isLoading) return

    setError('')
    dispatch(
      addMessage({
        role: 'user',
        content: `Uploaded document: ${file.name}`,
      }),
    )
    dispatch(setLoading(true))

    try {
      const result = await uploadDoc(file, currentForm())
      applyResponse(result)
    } catch (requestError) {
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : 'An unexpected error occurred.'

      setError(errorMessage)
      dispatch(
        addMessage({
          role: 'assistant',
          content: `The upload failed: ${errorMessage}`,
        }),
      )
    } finally {
      dispatch(setLoading(false))
    }
  }

  return (
    <section className="copilot-panel" aria-label="RCA AI co-pilot">
      <header className="copilot-header">
        <div>
          <p className="eyebrow">INVESTIGATION ASSISTANT</p>
          <h2>RCA Co-Pilot</h2>
        </div>
        <span className="connection-status">● Ready</span>
      </header>

      <div className="chat-messages" ref={messageListRef} aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <h3>Start your investigation</h3>
            <p>
              Describe an incident or upload a PDF, text file, or email. I’ll
              help organize the facts and identify evidence to review.
            </p>
          </div>
        ) : (
          messages.map((item, index) => (
            <article
              className={`chat-message chat-message--${item.role}`}
              key={`${item.role}-${index}`}
            >
              <span className="message-author">
                {item.role === 'user' ? 'You' : 'Co-Pilot'}
              </span>
              <p>{item.content}</p>
            </article>
          ))
        )}

        {isLoading && (
          <p className="chat-loading" role="status">
            Reviewing the investigation…
          </p>
        )}
      </div>

      <div className="suggested-prompts" aria-label="Suggested prompts">
        {suggestedPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={isLoading}
            onClick={() => setMessage(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>

      {error && (
        <p className="chat-error" role="alert">
          {error}
        </p>
      )}

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.eml"
          hidden
          onChange={handleFileChange}
        />
        <button
          className="upload-button"
          type="button"
          disabled={isLoading}
          aria-label="Upload an investigation document"
          onClick={() => fileInputRef.current?.click()}
        >
          Attach
        </button>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Describe an incident or ask a question…"
          rows={2}
          disabled={isLoading}
        />
        <button
          className="send-button"
          type="submit"
          disabled={isLoading || !message.trim()}
        >
          Send
        </button>
      </form>

      <p className="chat-disclaimer">
        AI suggestions require review by qualified personnel.
      </p>
    </section>
  )
}

export default ChatPanel