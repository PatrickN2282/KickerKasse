<template>
  <section class="panel-card audit-panel">
    <div class="section-header">
      <div>
        <h3>Audit-Log</h3>
        <p>Alle protokollierten Änderungen an Datenbankobjekten.</p>
      </div>
      <button class="btn btn-secondary" type="button" :disabled="isLoading" @click="loadAuditLogs">
        {{ isLoading ? 'Lädt…' : 'Neu laden' }}
      </button>
    </div>

    <div class="correction-table-wrapper">
      <table class="correction-slim-table">
        <thead>
          <tr>
            <th>Datum</th>
            <th>Benutzer</th>
            <th>Aktion</th>
            <th>Typ</th>
            <th>Name</th>
            <th class="text-right">Detail</th>
          </tr>
        </thead>
        <tbody>
          <template
            v-for="log in auditLogs"
            :key="`audit-${log.id}`"
          >
            <tr>
              <td>{{ formatTimestamp(log.created_at) }}</td>
              <td>{{ log.user_username || '—' }}</td>
              <td>
                <span :class="`audit-badge audit-badge--${String(log.action || '').toLowerCase()}`">
                  {{ auditActionLabel(log.action) }}
                </span>
              </td>
              <td>{{ auditEntityLabel(log.entity_type) }}</td>
              <td>{{ log.entity_name || '—' }}</td>
              <td class="text-right">
                <button
                  v-if="log.old_value || log.new_value"
                  class="btn-small btn-edit-inline"
                  type="button"
                  @click="toggleAuditDetail(log.id)"
                >
                  {{ expandedAuditLogIds.has(log.id) ? '▲' : '▼' }}
                </button>
                <span v-else class="text-muted">—</span>
              </td>
            </tr>
            <tr
              v-if="expandedAuditLogIds.has(log.id)"
              :key="`audit-detail-${log.id}`"
              class="audit-detail-row"
            >
              <td colspan="6">
                <div class="audit-detail-grid">
                  <div v-if="log.old_value" class="audit-value-block">
                    <span class="audit-value-label">Vorher</span>
                    <pre class="audit-value-pre">{{ formatJson(log.old_value) }}</pre>
                  </div>
                  <div v-if="log.new_value" class="audit-value-block">
                    <span class="audit-value-label">Nachher</span>
                    <pre class="audit-value-pre">{{ formatJson(log.new_value) }}</pre>
                  </div>
                </div>
              </td>
            </tr>
          </template>
          <tr v-if="auditLogs.length === 0 && !isLoading">
            <td
              colspan="6"
              class="empty-state-cell"
            >
              Noch keine Audit-Log-Einträge vorhanden
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import apiService from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const auditLogs = ref([])
const expandedAuditLogIds = ref(new Set())
const isLoading = ref(false)

const formatTimestamp = (value) => new Date(value).toLocaleString('de-DE', {
  dateStyle: 'short',
  timeStyle: 'medium',
})

const auditActionLabel = (action) => {
  const map = {
    CREATED: 'Erstellt',
    UPDATED: 'Geändert',
    DELETED: 'Gelöscht',
    RECHARGED: 'Guthaben +',
    RESTOCKED: 'Bestand +',
  }
  return map[action] || action
}

const auditEntityLabel = (type) => {
  const map = {
    member: 'Mitglied',
    product: 'Produkt',
    settings: 'Einstellungen',
    user: 'Benutzer',
    category: 'Kategorie',
    voucher: 'Gutschein / Verzehrkarte',
  }
  return map[type] || type
}

const toggleAuditDetail = (id) => {
  if (expandedAuditLogIds.value.has(id)) {
    expandedAuditLogIds.value.delete(id)
  } else {
    expandedAuditLogIds.value.add(id)
  }
  expandedAuditLogIds.value = new Set(expandedAuditLogIds.value)
}

const formatJson = (jsonStr) => {
  if (!jsonStr) return '—'
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

const loadAuditLogs = async () => {
  isLoading.value = true
  try {
    const response = await apiService.get('/admin/audit-log')
    auditLogs.value = response.data
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Audit-Log konnte nicht geladen werden')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadAuditLogs()
})
</script>

<style scoped lang="scss">
.audit-panel {
  --border: #e2e8f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.75rem;

  h3,
  p {
    margin: 0;
  }

  p {
    margin-top: 0.25rem;
    color: #64748b;
  }
}

.panel-card {
  background: color-mix(in srgb, var(--app-background-color) 30%, white);
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  border-radius: 12px;
  padding: 1rem;
}

.correction-table-wrapper {
  overflow-x: auto;
}

.correction-slim-table {
  width: 100%;
  min-width: 780px;
  border-collapse: collapse;
  font-size: 0.88rem;

  th,
  td {
    padding: 0.75rem 0.85rem;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
  }

  th {
    color: #475569;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
}

.text-right {
  text-align: right !important;
}

.text-muted {
  color: #94a3b8;
}

.empty-state-cell {
  text-align: center !important;
  color: #64748b;
}

.audit-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.01em;

  &--created {
    background: #dcfce7;
    color: #166534;
  }

  &--updated {
    background: #fef9c3;
    color: #854d0e;
  }

  &--deleted {
    background: #fee2e2;
    color: #991b1b;
  }

  &--recharged {
    background: #dbeafe;
    color: #1d4ed8;
  }

  &--restocked {
    background: #e0e7ff;
    color: #4338ca;
  }
}

.audit-detail-row td {
  padding: 0.6rem 1rem;
  background: #f8fafc;
}

.audit-detail-grid {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.audit-value-block {
  flex: 1;
  min-width: 200px;
}

.audit-value-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.audit-value-pre {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: #334155;
  max-height: 200px;
  overflow-y: auto;
}
</style>
