<template>
  <div class="notification-center">
    <transition-group name="notification-list" tag="div">
      <div
        v-for="notification in notificationStore.notifications"
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
      >
        <div class="notification-content">
          <span class="notification-message">{{ notification.message }}</span>
          <button
            @click="notificationStore.removeNotification(notification.id)"
            class="notification-close"
          >
            ✕
          </button>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()
</script>

<style scoped lang="scss">
.notification-center {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  pointer-events: none;
}

.notification {
  pointer-events: auto;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 250px;
}

.notification-content {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.notification-message {
  flex: 1;
  font-weight: 500;
}

.notification-close {
  background: none;
  border: none;
  color: currentColor;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: opacity 0.2s;

  &:hover {
    opacity: 1;
  }
}

.notification-success {
  background-color: #4caf50;
  color: white;
}

.notification-error {
  background-color: #f44336;
  color: white;
}

.notification-info {
  background-color: #2196f3;
  color: white;
}

.notification-warning {
  background-color: #ff9800;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-list-enter-active,
.notification-list-leave-active {
  transition: all 0.3s ease;
}

.notification-list-enter-from {
  transform: translateX(400px);
  opacity: 0;
}

.notification-list-leave-to {
  transform: translateX(400px);
  opacity: 0;
}
</style>
