import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])

  const addNotification = (message, type = 'info', duration = 3000) => {
    const id = Date.now()
    const notification = { id, message, type }

    notifications.value.push(notification)

    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }

    return id
  }

  const removeNotification = (id) => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  const success = (message, duration = 3000) => addNotification(message, 'success', duration)
  const error = (message, duration = 3000) => addNotification(message, 'error', duration)
  const info = (message, duration = 3000) => addNotification(message, 'info', duration)
  const warning = (message, duration = 3000) => addNotification(message, 'warning', duration)

  return {
    notifications,
    addNotification,
    removeNotification,
    success,
    error,
    info,
    warning,
  }
})
