export const getMemberFullName = (member) => {
  if (!member) return ''

  const firstName = member.first_name?.trim()
  const lastName = member.last_name?.trim()
  if (firstName || lastName) {
    return [firstName, lastName].filter(Boolean).join(' ')
  }

  return member.name || ''
}

export const getMemberShortName = (member) => {
  if (!member) return ''

  const firstName = member.first_name?.trim()
  const lastName = member.last_name?.trim()
  if (firstName || lastName) {
    return [firstName, lastName ? `${lastName.charAt(0)}.` : ''].filter(Boolean).join(' ')
  }

  return member.name || ''
}

export const getMemberSearchText = (member) => {
  return [
    getMemberFullName(member),
    getMemberShortName(member),
    member?.membership_number,
    member?.member_number,
    member?.name,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

export const getRoleLabel = (role) => ({
  TOP_ADMIN: 'Top-Admin',
  ADMIN: 'Admin',
  VERKAUF: 'Verkauf',
  MANAGER: 'Manager',
}[role] || role || '-')
