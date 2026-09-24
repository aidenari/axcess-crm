import React, { useRef } from 'react'

// Champ date d'un lot : bouton "Effacer" toujours visible (vider un
// <input type="date"> au clavier n'est pas évident) et borne à 1900,
// comme la validation backend.
export default function DateField({ label, name, value, onChange }) {
  const inputRef = useRef(null)

  const clear = () => {
    // Vide aussi une saisie partielle, que React voit déjà comme ''.
    if (inputRef.current) inputRef.current.value = ''
    onChange({ target: { name, value: '', type: 'date' } })
  }

  return (
    <div>
      <label className="block text-sm mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          className="input flex-1 min-w-0"
          type="date"
          name={name}
          value={value}
          min="1900-01-01"
          onChange={onChange}
        />
        <button
          type="button"
          onClick={clear}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 bg-white text-gray-700 whitespace-nowrap"
          title="Vider cette date"
        >
          Effacer
        </button>
      </div>
    </div>
  )
}
