const fieldLabels = {
  name: 'Name', first_name: 'Vorname', last_name: 'Nachname',
  description: 'Beschreibung', price_cents: 'Preis', member_price_cents: 'Mitgliedspreis',
  stock_quantity: 'Bestand', minimum_stock_quantity: 'Mindestbestand',
  email: 'E-Mail', phone: 'Telefon', membership_number: 'Mitgliedsnummer',
  warengruppe: 'Warengruppe', color: 'Farbe', display_order: 'Reihenfolge',
}

export const getErrorDetailMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map(item => {
      const key = item.loc?.at(-1)
      const label = fieldLabels[key] || (key === 'body' ? '' : key)
      const messages = {
        string_too_long: `Höchstens ${item.ctx?.max_length} Zeichen erlaubt`,
        string_too_short: 'Bitte einen Wert eingeben',
        missing: 'Bitte einen Wert eingeben',
        greater_than_equal: `Mindestens ${item.ctx?.ge} erforderlich`,
        less_than_equal: `Höchstens ${item.ctx?.le} erlaubt`,
        int_parsing: 'Bitte eine ganze Zahl eingeben',
        int_from_float: 'Bitte eine ganze Zahl eingeben',
      }
      const message = messages[item.type] || item.msg?.replace(/^Value error, /, '') || fallback
      return label ? `${label}: ${message}` : message
    }).join('; ') || fallback
  }
  if (detail && typeof detail === 'object') return detail.message || fallback
  return detail || fallback
}
