export default function Modal({ open, onClose, children }) {
    if (!open) return null
    return (
      <div
        role="dialog"
        aria-modal="true"
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.35)',
          display: 'grid', placeItems: 'center', padding: 16
        }}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          style={{ background: 'white', color: 'black', maxWidth: 720, width: '100%', borderRadius: 12, padding: 16 }}
        >
          <button onClick={onClose} aria-label="Close" style={{ float: 'right' }}>✕</button>
          {children}
        </div>
      </div>
    )
  }