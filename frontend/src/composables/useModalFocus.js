import { nextTick, onBeforeUnmount, watch } from 'vue'

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export const useModalFocus = (show, container, { canClose = () => true, onClose } = {}) => {
  let returnTarget = null

  const requestClose = () => {
    if (canClose()) onClose?.()
  }

  const handleKeydown = (event) => {
    if (!show.value || !container.value) return
    const openDialogs = [...document.querySelectorAll('[role="dialog"][aria-modal="true"]')]
    if (openDialogs.length && openDialogs[openDialogs.length - 1] !== container.value) return
    if (event.key === 'Escape') {
      event.preventDefault()
      requestClose()
      return
    }
    if (event.key !== 'Tab') return
    const targets = [...container.value.querySelectorAll(FOCUSABLE)]
    if (!targets.length) return
    const first = targets[0]
    const last = targets[targets.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  watch(show, async (visible) => {
    if (visible) {
      returnTarget = document.activeElement
      await nextTick()
      const preferred = container.value?.querySelector('[autofocus], input:not([type="hidden"]), select, textarea, button')
      preferred?.focus()
      document.addEventListener('keydown', handleKeydown)
    } else {
      document.removeEventListener('keydown', handleKeydown)
      returnTarget?.focus?.()
      returnTarget = null
    }
  }, { immediate: true })

  onBeforeUnmount(() => document.removeEventListener('keydown', handleKeydown))
  return { requestClose }
}
