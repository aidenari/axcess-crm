export function formatPhone(phone) {
  if (!phone) return ''
  const digits = String(phone).replace(/\D/g, '')
  return digits.replace(/(\d{2})(?=\d)/g, '$1 ').trim()
}
