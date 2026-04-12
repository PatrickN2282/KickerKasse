// Utility functions
export const formatPrice = (cents) => {
  return (cents / 100).toLocaleString('de-DE', {
    style: 'currency',
    currency: 'EUR',
  })
}

export const formatBalance = (cents) => {
  return (cents / 100).toLocaleString('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + ' €'
}

export const parsePrice = (value) => {
  return Math.round(parseFloat(value) * 100)
}
