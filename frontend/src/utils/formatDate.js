export function formatDate(dateStr) {
  if (!dateStr) return null
  // Already JJ/MM/AAAA
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) return dateStr
  // ISO AAAA-MM-JJ
  const m = String(dateStr).match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[3]}/${m[2]}/${m[1]}`
  return dateStr
}
