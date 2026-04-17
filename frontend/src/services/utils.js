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

export const getContrastColor = (hexColor, dark = '#111827', light = '#FFFFFF') => {
  const hex = (hexColor || '').replace('#', '')
  if (hex.length !== 6) {
    return light
  }

  const red = parseInt(hex.slice(0, 2), 16)
  const green = parseInt(hex.slice(2, 4), 16)
  const blue = parseInt(hex.slice(4, 6), 16)
  const brightness = ((red * 299) + (green * 587) + (blue * 114)) / 1000

  return brightness >= 160 ? dark : light
}
