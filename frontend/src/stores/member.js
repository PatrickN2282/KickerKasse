import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiService from '@/services/api'

import { getErrorDetailMessage } from '@/services/errorMessage'

export const useMemberStore = defineStore('member', () => {
  const members = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  const loadMembers = async (path) => {
    isLoading.value = true
    error.value = null

    try {
      // Clear full administration profiles before loading the checkout selection.
      if (path === '/members/selection') members.value = []
      const response = await apiService.get(path)
      members.value = response.data
      return members.value
    } catch (err) {
      error.value = getErrorDetailMessage(err, 'Failed to fetch members')
      return []
    } finally {
      isLoading.value = false
    }
  }

  const getMembers = () => loadMembers('/members')
  const getMemberSelection = () => loadMembers('/members/selection')

  const getMember = async (memberId) => {
    try {
      const response = await apiService.get(`/members/${memberId}`)
      return response.data
    } catch (err) {
      error.value = getErrorDetailMessage(err, 'Failed to fetch member')
      return null
    }
  }

  const createMember = async (memberData) => {
    error.value = null

    try {
      const response = await apiService.post('/members', memberData)
      members.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = getErrorDetailMessage(err, 'Failed to create member')
      return null
    }
  }

  const updateMember = async (memberId, memberData) => {
    error.value = null

    try {
      const response = await apiService.put(`/members/${memberId}`, memberData)
      const index = members.value.findIndex(m => m.id === memberId)
      if (index !== -1) {
        members.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = getErrorDetailMessage(err, 'Failed to update member')
      return null
    }
  }

  const rechargeMember = async (memberId, amountCents, authPassword) => {
    error.value = null

    try {
      const response = await apiService.post(`/members/${memberId}/recharge`, {
        amount_cents: amountCents,
        auth_password: authPassword,
      })
      const index = members.value.findIndex(m => m.id === memberId)
      if (index !== -1) {
        members.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = getErrorDetailMessage(err, 'Failed to recharge member')
      return null
    }
  }

  return {
    members,
    isLoading,
    error,
    getMembers,
    getMemberSelection,
    getMember,
    createMember,
    updateMember,
    rechargeMember,
  }
})
