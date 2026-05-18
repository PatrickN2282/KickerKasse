<template>
  <div class="admin-finance">
    <h2>Finanzstatistik</h2>

    <div class="finance-tabs">
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="{ active: activeTab === tab }"
        class="tab-btn"
        @click="activeTab = tab"
      >
        {{ tabLabels[tab] }}
      </button>
    </div>

    <!-- Z-BON / Tagesabrechnung -->
    <div
      v-if="activeTab === 'zbon'"
      class="tab-content"
    >
      <h3>Z-Bon</h3>

      <div
        v-if="loading"
        class="loading"
      >
        Läuft...
      </div>
      <div
        v-else
        class="zbon-layout"
      >
        <div class="zbon-section date-picker">
          <div>
            <strong>Aktueller Zeitraum:</strong>
            {{ currentPeriodLabel }}
          </div>
          <div>
            <strong>Letzter Belegbereich:</strong>
            {{ currentReceiptLabel }}
          </div>
        </div>

        <section class="zbon-section">
          <div class="zbon-section-header">
            <div>
              <h4>Umsatz</h4>
              <p>Aktuelle Buchungen seit dem letzten Z-Bon.</p>
            </div>
          </div>
          <div class="summary-grid zbon-card-grid">
            <div class="summary-card">
              <div class="card-label">
                Bar-Einnahmen
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.cash_total) }}
              </div>
            </div>
            <div class="summary-card">
              <div class="card-label">
                Umsatz (Guthaben)
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.balance_total) }}
              </div>
            </div>
            <div class="summary-card">
              <div class="card-label">
                Gutscheine
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.voucher_total) }}
              </div>
            </div>
            <div class="summary-card">
              <div class="card-label">
                Verzehrkarten verkauft
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.prepaid_voucher_sales_total) }}
              </div>
            </div>
            <div class="summary-card highlight">
              <div class="card-label">
                Umsatz GESAMT
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.total_amount) }}
              </div>
            </div>
          </div>
        </section>

        <section class="zbon-section">
          <div class="zbon-section-header">
            <div>
              <h4>Konten & Bestand</h4>
              <p>Kasse, offene Werte und Nebenbuchungen im Überblick.</p>
            </div>
          </div>
          <div class="summary-grid zbon-card-grid secondary">
            <div class="summary-card">
              <div class="card-label">
                Soll-Bestand Kasse
              </div>
              <div class="card-value">
                {{ formatEuroValue(dailyStats.cash_calculated) }}
              </div>
            </div>
            <div class="summary-card warning">
              <div class="card-label">
                Abschöpfungen
              </div>
              <div class="card-value">
                {{ formatPrice(dailyStats.withdrawal_total) }}
              </div>
            </div>
            <div class="summary-card neutral">
              <div class="card-label">
                Offene Gutscheine
              </div>
              <div class="card-value">
                {{ formatEuroValue(dailyStats.voucher_open_total) }}
              </div>
            </div>
            <div class="summary-card neutral">
              <div class="card-label">
                Gutscheinkonto
              </div>
              <div class="card-value">
                {{ formatEuroValue(dailyStats.club_account_total) }}
              </div>
            </div>
            <div class="summary-card neutral">
              <div class="card-label">
                Anzahl Transaktionen
              </div>
              <div class="card-value">
                {{ dailyStats.transaction_count }}
              </div>
            </div>
          </div>
        </section>

        <section class="zbon-section">
          <div class="zbon-section-header">
            <div>
              <h4>Aktionen</h4>
            </div>
          </div>
          <div class="zbon-actions">
            <button
              class="btn btn-primary"
              @click="openPreviewModal"
            >
              👁️ Z-Bon Vorschau
            </button>
            <button
              class="btn btn-success"
              @click="handleDownloadZBon"
            >
              ⬇️ Als HTML herunterladen
            </button>
            <button
              class="btn btn-info"
              @click="openZbonCreateModal"
            >
              ✅ Z-Bon erstellen
            </button>
            <button
              v-if="authStore.isAdmin"
              class="btn btn-warning"
              @click="openWithdrawalModal"
            >
              💸 Abschöpfung
            </button>
            <button
              class="btn btn-secondary"
              @click="openCashCounterModal"
            >
              💰 Kasse zählen
            </button>
          </div>
        </section>

        <section class="daily-transactions zbon-section">
          <h4>Transaktionen seit dem letzten Z-Bon</h4>
          <div
            v-if="dailyStats.transactions.length === 0"
            class="empty"
          >
            Keine Transaktionen im aktuellen Z-Bon-Zeitraum
          </div>
          <table
            v-else
            class="transactions-table"
          >
            <thead>
              <tr>
                <th>Datum</th>
                <th>Zeit</th>
                <th>Belegnummer</th>
                <th>Typ</th>
                <th>Mitglied / Konto</th>
                <th>Betrag</th>
                <th>Zahlungsart</th>
                <th>Benutzer</th>
              </tr>
            </thead>
            <tbody>
              <template
                v-for="transaction in dailyStats.transactions"
                :key="transaction.id"
              >
                <tr
                  class="transaction-row"
                  style="cursor: pointer;"
                  @click="toggleTransaction(transaction.id)"
                >
                  <td>{{ formatDate(transaction.created_at) }}</td>
                  <td>{{ formatTime(transaction.created_at) }}</td>
                  <td><strong>{{ transaction.receipt_number ?? '-' }}</strong></td>
                  <td>{{ getTransactionTypeLabel(transaction) }}</td>
                  <td>{{ getTransactionMemberLabel(transaction) }}</td>
                  <td class="amount">
                    {{ formatPrice(transaction.gross_amount_cents || transaction.total_amount_cents) }}
                  </td>
                  <td>
                    <span
                      :class="['payment-badge', getPaymentBadgeClass(transaction)]"
                    >
                      {{ getPaymentBadgeLabel(transaction) }}
                    </span>
                  </td>
                  <td>{{ getTransactionUserLabel(transaction) }}</td>
                </tr>
                <tr
                  v-if="expandedTransactions.has(transaction.id)"
                  class="items-row"
                >
                  <td
                    colspan="8"
                    class="items-cell"
                  >
                    <div class="items-list">
                      <div
                        v-if="transaction.reason"
                        class="item-detail"
                      >
                        <span class="item-name">Buchungsgrund</span>
                        <span class="item-total">{{ transaction.reason }}</span>
                      </div>
                      <div v-if="transaction.items && transaction.items.length > 0">
                        <div
                          v-for="item in transaction.items"
                          :key="item.id"
                          class="item-detail"
                        >
                          <span class="item-name">{{ item.product?.name || item.id }}: </span>
                          <span class="item-qty">{{ item.quantity }}×</span>
                          <span class="item-price">{{ formatPrice(item.unit_price_cents) }}</span>
                          <span class="item-total">= {{ formatPrice(item.total_price_cents) }}</span>
                        </div>
                      </div>
                      <div
                        v-else-if="!transaction.reason"
                        class="no-items"
                      >
                        Keine Artikel
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </section>

        <section class="scheduler-section zbon-section">
          <h4>⏱️ Automatischer Email-Versand</h4>
          <div class="scheduler-status">
            <div class="status-item">
              <span>Status:</span>
              <span
                v-if="schedulerStatus.running"
                class="status-badge running"
              >
                ● Läuft
              </span>
              <span
                v-else
                class="status-badge stopped"
              >
                ● Gestoppt
              </span>
            </div>
            <div
              v-if="schedulerStatus.next_run"
              class="status-item"
            >
              <span>Nächster Versand:</span>
              <span class="next-run">{{ formatTime(schedulerStatus.next_run) }}</span>
            </div>
          </div>
          <p class="scheduler-info">
            Der automatische Z-Bon-Versand muss in der .env-Datei konfiguriert werden:
          </p>
          <ul class="config-list">
            <li><code>SCHEDULED_ZBON_ENABLED=true</code></li>
            <li><code>SCHEDULED_ZBON_TIME=23:59</code> (HH:MM Format)</li>
            <li><code>SCHEDULED_ZBON_REPORT_TYPE=zbon</code> (oder "daily-report")</li>
            <li><code>EMAIL_ENABLED=true</code></li>
            <li>SMTP-Einstellungen konfigurieren</li>
          </ul>
        </section>
      </div>
    </div>

    <!-- Z-BÖNS VERLAUF -->
    <div
      v-if="activeTab === 'zbons'"
      class="tab-content"
    >
      <h3>📑 Z-Bons Verlauf</h3>

      <div class="filter-section">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input
            v-model="zbonsFilterStartDate"
            type="date"
            class="form-input"
          >
        </div>
        <div class="filter-group">
          <label>Bis Datum:</label>
          <input
            v-model="zbonsFilterEndDate"
            type="date"
            class="form-input"
          >
        </div>
        <button
          class="btn btn-primary"
          @click="loadZbonsHistory"
        >
          🔍 Filtern
        </button>
      </div>

      <div
        v-if="loadingZbons"
        class="loading"
      >
        Läuft...
      </div>
      <div v-else>
        <!-- Summary Cards -->
        <div
          class="summary-grid"
          style="margin-bottom: 1.5rem;"
        >
          <div class="summary-card">
            <div class="card-label">
              Anzahl Z-Böns
            </div>
            <div class="card-value">
              {{ zbonsList.length }}
            </div>
          </div>
          <div class="summary-card">
            <div class="card-label">
              Gesamt Umsatz (BAR)
            </div>
            <div class="card-value">
              {{ formatPrice(zbonsTotalCash) }}
            </div>
          </div>
          <div class="summary-card">
            <div class="card-label">
              Gesamt Umsatz (Guthaben)
            </div>
            <div class="card-value">
              {{ formatPrice(zbonsTotalBalance) }}
            </div>
          </div>
          <div class="summary-card highlight">
            <div class="card-label">
              Gesamt Umsatz
            </div>
            <div class="card-value">
              {{ formatPrice(zbonsTotalRevenue) }}
            </div>
          </div>
        </div>

        <!-- Z-Böns Table -->
        <div class="table-container">
          <table
            v-if="zbonsList.length > 0"
            class="transactions-table"
          >
            <thead>
              <tr>
                <th>Seq#</th>
                <th>Datum</th>
                <th>Umsatz BAR</th>
                <th>Umsatz Guthaben</th>
                <th>Kasse Anfang</th>
                <th>Kasse Ende</th>
                <th>Differenz</th>
                <th>Entnahmen</th>
                <th>Benutzer</th>
                <th>Erstellt</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="zbon in zbonsList" 
                :key="zbon.id"
                class="transaction-row"
                style="cursor: pointer;"
                @click="openZbonHistoryModal(zbon)"
              >
                <td><strong>#{{ zbon.sequence_number }}</strong></td>
                <td>{{ formatDate(zbon.business_date) }}</td>
                <td class="amount">
                  {{ formatPrice(zbon.gross_revenue_cash * 100) }}
                </td>
                <td class="amount">
                  {{ formatPrice(zbon.gross_revenue_balance * 100) }}
                </td>
                <td class="amount">
                  {{ formatPrice(zbon.cash_opening_balance * 100) }}
                </td>
                <td class="amount">
                  {{ formatPrice((zbon.cash_calculated || 0) * 100) }}
                </td>
                <td
                  class="amount"
                  :class="{ withdrawal: (zbon.cash_difference || 0) !== 0 }"
                >
                  {{ formatPrice((zbon.cash_difference || 0) * 100) }}
                </td>
                <td class="amount withdrawal">
                  {{ formatPrice(zbon.cash_withdrawals * 100) }}
                </td>
                <td>{{ zbon.created_by_name || '-' }}</td>
                <td class="date">
                  {{ formatTime(zbon.generated_at) }}
                </td>
              </tr>
            </tbody>
          </table>

          <div
            v-else
            class="empty"
          >
            Keine Z-Böns für den ausgewählten Zeitraum
          </div>
        </div>

        <!-- Pagination -->
        <div
          v-if="zbonsTotalPages > 1"
          class="pagination"
          style="margin-top: 2rem;"
        >
          <button
            :disabled="zbonsCurrentPage === 1"
            class="btn btn-secondary"
            @click="zbonsCurrentPage--"
          >
            ◀ Zurück
          </button>
          <span>Seite {{ zbonsCurrentPage }} von {{ zbonsTotalPages }}</span>
          <button
            :disabled="zbonsCurrentPage === zbonsTotalPages"
            class="btn btn-secondary"
            @click="zbonsCurrentPage++"
          >
            Weiter ▶
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="activeTab === 'history'"
      class="tab-content"
    >
      <h3>Transaktionshistorie</h3>

      <div class="filter-section">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input
            v-model="filterStartDate"
            type="date"
            class="form-input"
          >
        </div>
        <div class="filter-group">
          <label>Bis Datum:</label>
          <input
            v-model="filterEndDate"
            type="date"
            class="form-input"
          >
        </div>
        <div class="filter-group">
          <label>Zahlungsart:</label>
          <select
            v-model="filterPaymentMethod"
            class="form-input"
          >
            <option value="">
              Alle
            </option>
            <option value="CASH">
              BAR
            </option>
            <option value="BALANCE">
              Guthaben
            </option>
            <option value="VOUCHER_GIFT">
              Gutschein
            </option>
            <option value="VOUCHER_PREPAID">
              Verzehrkarte
            </option>
            <option value="WITHDRAWAL">
              Abschöpfung
            </option>
          </select>
        </div>
        <button
          class="btn btn-info"
          @click="applyFilters"
        >
          Filter anwenden
        </button>
      </div>

      <div
        v-if="loadingHistory"
        class="loading"
      >
        Läuft...
      </div>
      <div v-else>
        <div class="history-summary">
          <div class="summary-item">
            <span>Umsatz gesamt:</span>
            <span class="amount">{{ formatPrice(filteredStats.total) }}</span>
          </div>
          <div class="summary-item">
            <span>Gutscheine:</span>
            <span class="amount">{{ formatPrice(filteredStats.voucherTotal) }}</span>
          </div>
          <div class="summary-item">
            <span>Anzahl Transaktionen:</span>
            <span>{{ filteredTransactions.length }}</span>
          </div>
        </div>

        <table
          v-if="filteredTransactions.length > 0"
          class="transactions-table"
        >
          <thead>
            <tr>
              <th>Datum</th>
              <th>Zeit</th>
              <th>Belegnummer</th>
              <th>Typ</th>
              <th>Mitglied / Konto</th>
              <th>Betrag</th>
              <th>Zahlungsart</th>
              <th>Benutzer</th>
            </tr>
          </thead>
          <tbody>
            <template
              v-for="transaction in filteredTransactions"
              :key="transaction.id"
            >
              <tr
                class="transaction-row"
                style="cursor: pointer;"
                @click="toggleTransaction(transaction.id)"
              >
                <td>{{ formatDate(transaction.created_at) }}</td>
                <td>{{ formatTime(transaction.created_at) }}</td>
                <td><strong>{{ transaction.receipt_number ?? '-' }}</strong></td>
                <td>{{ getTransactionTypeLabel(transaction) }}</td>
                <td>{{ getTransactionMemberLabel(transaction) }}</td>
                <td class="amount">
                  {{ formatPrice(transaction.gross_amount_cents || transaction.total_amount_cents) }}
                </td>
                <td>
                  <span
                    :class="['payment-badge', getPaymentBadgeClass(transaction)]"
                  >
                    {{ getPaymentBadgeLabel(transaction) }}
                  </span>
                </td>
                <td>{{ getTransactionUserLabel(transaction) }}</td>
              </tr>
              <tr
                v-if="expandedTransactions.has(transaction.id)"
                class="items-row"
              >
                <td
                  colspan="8"
                  class="items-cell"
                >
                  <div class="items-list">
                    <div
                      v-if="transaction.reason"
                      class="item-detail"
                    >
                      <span class="item-name">Buchungsgrund</span>
                      <span class="item-total">{{ transaction.reason }}</span>
                    </div>
                    <div v-if="transaction.items && transaction.items.length > 0">
                      <div
                        v-for="item in transaction.items"
                        :key="item.id"
                        class="item-detail"
                      >
                        <span class="item-name">{{ item.product?.name || item.id }}: </span>
                        <span class="item-qty">{{ item.quantity }}×</span>
                        <span class="item-price">{{ formatPrice(item.unit_price_cents) }}</span>
                        <span class="item-total">= {{ formatPrice(item.total_price_cents) }}</span>
                      </div>
                    </div>
                    <div
                      v-else-if="!transaction.reason"
                      class="no-items"
                    >
                      Keine Artikel
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        <div
          v-else
          class="empty"
        >
          Keine Transaktionen im ausgewählten Zeitraum
        </div>
      </div>
    </div>

    <!-- Umsatzstatistik -->
    <div
      v-if="activeTab === 'revenue'"
      class="tab-content"
    >
      <h3>Umsatzstatistik</h3>

      <div class="revenue-overview">
        <div class="revenue-card">
          <div class="card-label">
            Umsatz diese Woche
          </div>
          <div class="card-value">
            {{ formatPrice(revenueStats.week_total) }}
          </div>
        </div>
        <div class="revenue-card">
          <div class="card-label">
            Umsatz diesen Monat
          </div>
          <div class="card-value">
            {{ formatPrice(revenueStats.month_total) }}
          </div>
        </div>
        <div class="revenue-card">
          <div class="card-label">
            Durchschnitt pro Tag
          </div>
          <div class="card-value">
            {{ formatPrice(revenueStats.daily_average) }}
          </div>
        </div>
        <div class="revenue-card warning">
          <div class="card-label">
            Abschöpfungen diese Woche
          </div>
          <div class="card-value">
            {{ formatPrice(revenueStats.week_withdrawals) }}
          </div>
        </div>
      </div>

      <div class="payment-stats">
        <h4>Nach Zahlungsart</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">
              💰 Bargeld
            </div>
            <div class="stat-value">
              {{ formatPrice(revenueStats.cash_total) }}
            </div>
            <div class="stat-percent">
              {{ revenueStats.cash_percent }}%
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">
              💳 Guthaben
            </div>
            <div class="stat-value">
              {{ formatPrice(revenueStats.balance_total) }}
            </div>
            <div class="stat-percent">
              {{ revenueStats.balance_percent }}%
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">
              💳 Verzehrkarten
            </div>
            <div class="stat-value">
              {{ formatPrice(revenueStats.prepaid_voucher_sales_total) }}
            </div>
            <div class="stat-percent">
              diese Woche
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">
              💸 Abschöpfungen 30 Tage
            </div>
            <div class="stat-value">
              {{ formatPrice(revenueStats.month_withdrawals) }}
            </div>
          </div>
        </div>
      </div>

      <div class="top-products">
        <h4>Top Produkte (diese Woche)</h4>
        <table
          v-if="revenueStats.top_products.length > 0"
          class="products-table"
        >
          <thead>
            <tr>
              <th>Produkt</th>
              <th>Menge</th>
              <th>Umsatz</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in revenueStats.top_products"
              :key="product.id"
            >
              <td>{{ product.name }}</td>
              <td>{{ product.quantity_sold }}</td>
              <td>{{ formatPrice(product.total_revenue) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Member-Statistik -->
    <div
      v-if="activeTab === 'members'"
      class="tab-content"
    >
      <h3>Mitglied-Statistik</h3>

      <div class="member-stats-overview">
        <div class="stat-card">
          <div class="stat-label">
            Gesamte Mitglieder
          </div>
          <div class="stat-value">
            {{ memberStats.total_members }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            Aktiv diese Woche
          </div>
          <div class="stat-value">
            {{ memberStats.active_this_week }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">
            Gesamtes Guthaben
          </div>
          <div class="stat-value">
            {{ formatPrice(memberStats.total_balance) }}
          </div>
        </div>
      </div>

      <h4>Top Mitglieder (nach Ausgaben)</h4>
      <table
        v-if="memberStats.top_members.length > 0"
        class="members-table"
      >
        <thead>
          <tr>
            <th>Name</th>
            <th>Transaktionen</th>
            <th>Ausgegeben</th>
            <th>Guthaben</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in memberStats.top_members"
            :key="member.id"
          >
            <td>{{ formatMemberLabel(member) }}</td>
            <td>{{ member.transaction_count }}</td>
            <td>{{ formatPrice(member.total_spent) }}</td>
            <td>{{ formatPrice(member.balance_cents) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="activeTab === 'corrections'"
      class="tab-content tab-content--flush"
    >
      <Corrections />
    </div>

    <div
      v-if="activeTab === 'internalAccounts'"
      class="tab-content"
    >
      <h3>Interne Konten</h3>

      <div class="summary-grid">
        <div class="summary-card neutral">
          <div class="card-label">
            Gutscheinkonto gesamt
          </div>
          <div class="card-value">
            {{ formatPrice(clubAccount.balance_cents) }}
          </div>
        </div>
        <div class="summary-card neutral">
          <div class="card-label">
            Materialartikel gesamt
          </div>
          <div class="card-value">
            {{ materialAccount.total_quantity }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">
            Gutscheinbuchungen
          </div>
          <div class="card-value">
            {{ clubAccount.entries.length }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">
            Materialbuchungen
          </div>
          <div class="card-value">
            {{ materialAccount.entries.length }}
          </div>
        </div>
      </div>

      <div class="internal-account-sections">
        <section class="zbon-section internal-account-section">
          <div class="zbon-section-header internal-account-header">
            <div>
              <h4>Gutscheinkonto</h4>
              <p>Saldo und Verlauf aller Buchungen auf dem Gutscheinkonto.</p>
            </div>
            <button
              class="btn btn-subtle internal-account-toggle"
              @click="toggleInternalAccountSection('club')"
            >
              {{ isInternalAccountSectionExpanded('club') ? 'Ausblenden' : 'Einblenden' }}
            </button>
          </div>
          <div
            v-if="isInternalAccountSectionExpanded('club')"
            class="internal-account-section-body"
          >
            <div class="summary-grid zbon-card-grid secondary">
              <div class="summary-card neutral">
                <div class="card-label">
                  Kontostand
                </div>
                <div class="card-value">
                  {{ formatPrice(clubAccount.balance_cents) }}
                </div>
              </div>
              <div class="summary-card neutral">
                <div class="card-label">
                  Buchungen
                </div>
                <div class="card-value">
                  {{ clubAccount.entries.length }}
                </div>
              </div>
              <div class="summary-card neutral">
                <div class="card-label">
                  Offene Gutscheine
                </div>
                <div class="card-value">
                  {{ formatEuroValue(dailyStats.voucher_open_total) }}
                </div>
              </div>
            </div>

            <div class="table-container">
              <table
                v-if="clubAccount.entries.length"
                class="transactions-table"
              >
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Zeit</th>
                    <th>Betrag</th>
                    <th>Grund</th>
                    <th>Beleg</th>
                    <th>Benutzer</th>
                  </tr>
                </thead>
                <tbody>
                  <template
                    v-for="entry in clubAccount.entries"
                    :key="`club-${entry.id}`"
                  >
                    <tr
                      class="transaction-row"
                      style="cursor: pointer;"
                      @click="toggleInternalAccountEntry('club', entry.id)"
                    >
                      <td>{{ formatDate(entry.created_at) }}</td>
                      <td>{{ formatTime(entry.created_at) }}</td>
                      <td
                        class="amount"
                        :class="{ withdrawal: entry.amount_cents < 0 }"
                      >
                        {{ formatPrice(entry.amount_cents) }}
                      </td>
                      <td>{{ entry.reason }}</td>
                      <td>{{ entry.transaction?.receipt_number ? `#${entry.transaction.receipt_number}` : '-' }}</td>
                      <td>{{ entry.user_name || '-' }}</td>
                    </tr>
                    <tr
                      v-if="isInternalAccountEntryExpanded('club', entry.id)"
                      class="items-row"
                    >
                      <td
                        colspan="6"
                        class="items-cell"
                      >
                        <div class="items-list">
                          <div class="item-detail">
                            <span class="item-name">Buchungsgrund</span>
                            <span class="item-total">{{ entry.reason }}</span>
                          </div>
                          <div
                            v-if="entry.voucher"
                            class="item-detail"
                          >
                            <span class="item-name">Gutschein</span>
                            <span class="item-total">
                              {{ entry.voucher.voucher_number }} · {{ getVoucherTypeLabel(entry.voucher.voucher_type) }}
                            </span>
                          </div>
                          <div v-if="entry.transaction?.items?.length">
                            <div
                              v-for="item in entry.transaction.items"
                              :key="item.id"
                              class="item-detail"
                            >
                              <span class="item-name">{{ item.product?.name || item.id }}: </span>
                              <span class="item-qty">{{ item.quantity }}×</span>
                              <span class="item-price">{{ formatPrice(item.unit_price_cents) }}</span>
                              <span class="item-total">= {{ formatPrice(item.total_price_cents) }}</span>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
              <div
                v-else
                class="empty"
              >
                Keine Buchungen im Gutscheinkonto vorhanden
              </div>
            </div>
          </div>
        </section>

        <section class="zbon-section internal-account-section">
          <div class="zbon-section-header internal-account-header">
            <div>
              <h4>Materialkonto</h4>
              <p>Gebuchte interne Materialverkäufe mit Verlauf und Belegdaten.</p>
            </div>
            <button
              class="btn btn-subtle internal-account-toggle"
              @click="toggleInternalAccountSection('material')"
            >
              {{ isInternalAccountSectionExpanded('material') ? 'Ausblenden' : 'Einblenden' }}
            </button>
          </div>
          <div
            v-if="isInternalAccountSectionExpanded('material')"
            class="internal-account-section-body"
          >
            <div class="summary-grid zbon-card-grid secondary">
              <div class="summary-card neutral">
                <div class="card-label">
                  Artikel gesamt
                </div>
                <div class="card-value">
                  {{ materialAccount.total_quantity }}
                </div>
              </div>
              <div class="summary-card neutral">
                <div class="card-label">
                  Buchungen
                </div>
                <div class="card-value">
                  {{ materialAccount.entries.length }}
                </div>
              </div>
            </div>

            <div class="table-container">
              <table
                v-if="materialAccount.entries.length"
                class="transactions-table"
              >
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Zeit</th>
                    <th>Typ</th>
                    <th>Artikel</th>
                    <th>Menge</th>
                    <th>Beleg</th>
                    <th>Benutzer</th>
                  </tr>
                </thead>
                <tbody>
                  <template
                    v-for="entry in materialAccount.entries"
                    :key="`material-${entry.id}`"
                  >
                    <tr
                      class="transaction-row"
                      style="cursor: pointer;"
                      @click="toggleInternalAccountEntry('material', entry.id)"
                    >
                      <td>{{ formatDate(entry.created_at) }}</td>
                      <td>{{ formatTime(entry.created_at) }}</td>
                      <td>{{ entry.entry_type_label }}</td>
                      <td>{{ entry.product_name || entry.reason }}</td>
                      <td>{{ entry.quantity ?? '-' }}</td>
                      <td>{{ entry.receipt_number ? `#${entry.receipt_number}` : '-' }}</td>
                      <td>{{ entry.user_name || '-' }}</td>
                    </tr>
                    <tr
                      v-if="isInternalAccountEntryExpanded('material', entry.id)"
                      class="items-row"
                    >
                      <td
                        colspan="7"
                        class="items-cell"
                      >
                        <div class="items-list">
                          <div class="item-detail">
                            <span class="item-name">Buchungsgrund</span>
                            <span class="item-total">{{ entry.reason }}</span>
                          </div>
                          <div
                            v-if="entry.transaction"
                            class="item-detail"
                          >
                            <span class="item-name">Zahlung</span>
                            <span class="item-total">{{ getPaymentBadgeLabel(entry.transaction) }}</span>
                          </div>
                          <div v-if="entry.transaction?.items?.length">
                            <div
                              v-for="item in entry.transaction.items"
                              :key="item.id"
                              class="item-detail internal-material-item-detail"
                            >
                              <span class="item-name">{{ item.product?.name || item.id }}: </span>
                              <span class="item-qty">{{ item.quantity }}×</span>
                              <div
                                v-if="item.note"
                                class="item-detail-note"
                              >
                                Notiz: {{ item.note }}
                              </div>
                            </div>
                          </div>
                          <div
                            v-else-if="entry.note"
                            class="item-detail internal-material-item-detail"
                          >
                            <span class="item-name">Notiz</span>
                            <span class="item-total">{{ entry.note }}</span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
              <div
                v-else
                class="empty"
              >
                Keine Buchungen im Materialkonto vorhanden
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Cash Counter Modal -->
    <CashCounterModal
      :show="showCashCounterModal"
      @close="showCashCounterModal = false"
      @confirm="onCashCounterConfirm"
    />

    <div
      v-if="showZbonCreateModal"
      class="confirmation-overlay"
    >
      <div class="confirmation-dialog zbon-create-dialog">
        <h3>Z-Bon erstellen</h3>
        <div class="zbon-create-layout">
          <div class="zbon-create-main">
            <div class="zbon-note-box">
              Kassenprüfer wählen → Kassenbestand zählen → ggf. Abschöpfung vornehmen → mit neuem Kassenbestand abgleichen → Z-Bon erstellen
            </div>
            <div class="selection-grid">
              <div class="selection-group">
                <label>Erstellt von</label>
                <button
                  class="member-select-btn"
                  @click="openUserPicker('createdByUserId')"
                >
                  {{ getSelectedUserName(zbonForm.createdByUserId, 'Benutzer auswählen') }}
                </button>
              </div>
              <div class="selection-group">
                <label>Kassenprüfer</label>
                <div class="selection-actions">
                  <button
                    class="member-select-btn"
                    @click="openMemberPicker('verifiedByUserId')"
                  >
                    {{ getSelectedVerifierName(zbonForm.verifiedByUserId, 'Mitglied auswählen') }}
                  </button>
                  <button
                    v-if="zbonForm.verifiedByUserId"
                    class="clear-selection-btn"
                    @click="zbonForm.verifiedByUserId = null"
                  >
                    Entfernen
                  </button>
                </div>
              </div>
            </div>
            <div class="summary-grid compact-summary-grid">
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Vorheriger Barbestand
                </div>
                <div class="card-value">
                  {{ formatEuroValue(dailyStats.opening_balance) }}
                </div>
              </div>
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Buchungs-Range
                </div>
                <div class="card-value">
                  {{ currentReceiptLabel }}
                </div>
              </div>
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Abschöpfungen Zeitraum
                </div>
                <div class="card-value">
                  {{ formatPrice(zbonModalWithdrawalTotalCents) }}
                </div>
              </div>
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Neuer Barbestand Soll
                </div>
                <div class="card-value">
                  {{ zbonModalCashCalculatedDisplay }}
                </div>
              </div>
            </div>
            <div class="zbon-balance-group">
              <div class="selection-group zbon-counted-group">
                <label>Gezählter Kassenbestand</label>
                <input
                  v-model="zbonCountedCash"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-input"
                  placeholder="0,00"
                >
              </div>
              <div class="summary-grid zbon-side-summary">
                <div class="summary-card modal-summary-card">
                  <div class="card-label">
                    Abschöpfung im Modal
                  </div>
                  <div class="card-value">
                    {{ formatPrice(newWithdrawalsCents) }}
                  </div>
                </div>
                <div class="summary-card modal-summary-card">
                  <div class="card-label">
                    Neuer Ist-Bestand
                  </div>
                  <div class="card-value">
                    {{ zbonNewCashBalanceDisplay }}
                  </div>
                </div>
                <div class="summary-card modal-summary-card">
                  <div class="card-label">
                    Differenz
                  </div>
                  <div class="card-value">
                    {{ zbonDifferenceDisplay }}
                  </div>
                </div>
              </div>
              <small
                v-if="zbonFinalCashInvalid"
                class="zbon-warning-text"
              >
                Der gezählte Bestand darf nicht kleiner als die im Modal vorgenommenen Abschöpfung sein.
              </small>
            </div>
          </div>
          <div class="zbon-create-side">
            <div class="confirmation-buttons zbon-create-buttons">
              <button
                class="btn btn-info"
                @click="openCashCounterModal"
              >
                💰 Kasse zählen
              </button>
              <button
                class="btn btn-warning"
                @click="openWithdrawalModal"
              >
                💸 Abschöpfung
              </button>
              <button
                :class="['btn', canCreateZbon ? 'btn-ready' : 'btn-disabled']"
                :disabled="!canCreateZbon"
                @click="requestZBonCreate"
              >
                ✓ Z-Bon erstellen
              </button>
              <button
                class="btn btn-secondary"
                @click="closeZbonCreateModal"
              >
                Abbrechen / Zurück
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showWithdrawalModal"
      class="confirmation-overlay"
    >
      <div class="confirmation-dialog">
        <h3>Abschöpfung</h3>
        <div class="filter-group">
          <label>Betrag in EUR</label>
          <input
            v-model="withdrawalForm.amount"
            type="number"
            min="0"
            step="0.01"
            class="form-input"
          >
        </div>
        <div class="selection-group">
          <label>Durchgeführt von</label>
          <button
            class="member-select-btn"
            @click="openUserPicker('withdrawalUserId')"
          >
            {{ getSelectedUserName(selectedWithdrawalUserId, 'Benutzer auswählen') }}
          </button>
        </div>
        <div class="filter-group">
          <label>Notiz (optional)</label>
          <input
            v-model="withdrawalForm.note"
            type="text"
            class="form-input"
            placeholder="z. B. Vereinskasse"
          >
        </div>
        <div class="confirmation-buttons">
          <button
            class="btn btn-secondary"
            @click="closeWithdrawalModal"
          >
            Abbrechen / Zurück
          </button>
          <button
            class="btn btn-warning"
            @click="submitWithdrawal"
          >
            💸 Abschöpfen
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showMemberPickerModal"
      class="confirmation-overlay member-picker-overlay"
    >
      <div class="confirmation-dialog member-picker-dialog">
        <h3>{{ pickerTitle }}</h3>
        <input
          v-model="memberSearch"
          type="text"
          :placeholder="pickerSearchPlaceholder"
          class="form-input member-search-input"
        >
        <div class="member-picker-list">
          <button
            v-for="entry in filteredPickerOptions"
            :key="entry.id"
            class="member-picker-item"
            @click="selectPickerOption(entry)"
          >
            <div
              v-if="entry.photo_path"
              class="member-picker-photo"
            >
              <img
                :src="`/api/members/${entry.id}/photo`"
                :alt="formatPickerLabel(entry)"
              >
            </div>
            <div
              v-else
              class="member-picker-photo placeholder"
            >
              👤
            </div>
            <span>{{ formatPickerLabel(entry) }}</span>
          </button>
          <div
            v-if="!filteredPickerOptions.length"
            class="empty member-picker-empty"
          >
            Keine Einträge gefunden
          </div>
        </div>
        <div class="confirmation-buttons">
          <button
            class="btn btn-secondary"
            @click="closeMemberPicker"
          >
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showZbonPreviewModal && zBonHtml"
      class="confirmation-overlay"
    >
      <div
        class="confirmation-dialog zbon-preview-dialog"
      >
        <h3>{{ zbonHtmlModalTitle }}</h3>
        <div class="zbon-preview-frame-shell">
          <iframe
            :srcdoc="zBonHtml"
            class="zbon-preview-frame"
            title="Z-Bon Vorschau"
          />
        </div>
        <div class="confirmation-buttons">
          <button
            class="btn btn-success"
            @click="downloadCurrentZbonHtml"
          >
            ⬇️ HTML herunterladen
          </button>
          <button
            class="btn btn-secondary"
            @click="showZbonPreviewModal = false"
          >
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>
    <PasswordConfirmModal
      :show="showPasswordModal"
      title="Z-Bon erstellen"
      message="Bitte Zugangsdaten des aktuell angemeldeten Benutzers bestätigen."
      :username="authStore.user?.username || ''"
      confirm-label="Z-Bon erstellen"
      @close="showPasswordModal = false"
      @confirm="createZBon"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatPrice } from '@/services/utils'
import apiService from '@/services/api'
import CashCounterModal from '@/components/CashCounterModal.vue'
import PasswordConfirmModal from '@/components/PasswordConfirmModal.vue'
import { useNotificationStore } from '@/stores/notification'
import { useMemberStore } from '@/stores/member'
import { getMemberFullName, getMemberSearchText, getMemberShortName } from '@/services/member'
import { useAuthStore } from '@/stores/auth'
import Corrections from '@/views/admin/Corrections.vue'

const notificationStore = useNotificationStore()
const memberStore = useMemberStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const DEFAULT_FINANCE_TAB = 'zbon'
const activeTab = ref(DEFAULT_FINANCE_TAB)
const loading = ref(false)
const loadingHistory = ref(false)

// Cash counter modal state
const showCashCounterModal = ref(false)
const cashCountData = ref(null)
// Filters
const filterStartDate = ref(getDateDaysAgo(30))
const filterEndDate = ref(new Date().toISOString().split('T')[0])
const filterPaymentMethod = ref('')

const showZbonCreateModal = ref(false)
const showZbonPreviewModal = ref(false)
const showWithdrawalModal = ref(false)
const showMemberPickerModal = ref(false)
const showPasswordModal = ref(false)
const memberPickerTarget = ref(null)
const memberSearch = ref('')
const financeUsers = ref([])
const zbonHtmlModalTitle = ref('📋 Z-Bon Vorschau')
const zbonHtmlDownloadMeta = ref(null)
const clubAccount = ref({ balance_cents: 0, entries: [] })
const materialAccount = ref({ total_quantity: 0, entries: [] })
const zbonForm = ref({
  createdByUserId: null,
  verifiedByUserId: null,
})
const zbonCountedCash = ref('')
const withdrawalForm = ref({
  amount: '',
  userId: null,
  note: '',
})
const pendingWithdrawals = ref([])
// Expanded transactions state
const expandedTransactions = ref(new Set())
const expandedInternalAccountEntries = ref(new Set())
const expandedInternalAccountSections = ref(new Set())

// Z-Bon HTML preview
const zBonHtml = ref('')

// Z-Böns History
const zbonsList = ref([])
const loadingZbons = ref(false)
const zbonsFilterStartDate = ref(getDateDaysAgo(90))
const zbonsFilterEndDate = ref(new Date().toISOString().split('T')[0])
const zbonsCurrentPage = ref(1)
const zbonsTotalPages = ref(1)

// Data
const dailyStats = ref({
  cash_total: 0,
  balance_total: 0,
  voucher_total: 0,
  prepaid_voucher_sales_total: 0,
  total_amount: 0,
  transaction_count: 0,
  opening_balance: 0,
  cash_calculated: 0,
  withdrawal_total: 0,
  voucher_open_total: 0,
  voucher_created_count: 0,
  voucher_created_total: 0,
  voucher_redeemed_count: 0,
  voucher_redeemed_total: 0,
  voucher_open_count: 0,
  material_account_total: 0,
  club_account_total: 0,
  period_start: null,
  period_end: null,
  receipt_min: null,
  receipt_max: null,
  report_content: '',
  transactions: [],
})

const filteredTransactions = ref([])
const filteredStats = ref({ total: 0, voucherTotal: 0 })
const revenueStats = ref({
  week_total: 0,
  month_total: 0,
  daily_average: 0,
  cash_total: 0,
  balance_total: 0,
  prepaid_voucher_sales_total: 0,
  month_prepaid_voucher_sales_total: 0,
  cash_percent: 0,
  balance_percent: 0,
  week_withdrawals: 0,
  month_withdrawals: 0,
  top_products: [],
})

const memberStats = ref({
  total_members: 0,
  active_this_week: 0,
  total_balance: 0,
  top_members: [],
})

const tabs = computed(() => (authStore.isManager
  ? ['zbon', 'zbons']
  : ['zbon', 'zbons', 'history', 'revenue', 'members', 'internalAccounts', ...(authStore.isAdmin ? ['corrections'] : [])]
))
const tabLabels = {
  zbon: '📊 Z-Bon',
  zbons: '📑 Z-Bons Verlauf',
  history: '📜 Transaktionen',
  revenue: '📈 Umsatz',
  members: '👥 Mitglieder',
  internalAccounts: '🏦 Interne Konten',
  corrections: '🧾 Korrekturen',
}

// Scheduler configuration
const schedulerStatus = ref({
  enabled: false,
  running: false,
  scheduled_time: '23:59',
})
function getDateDaysAgo(days) {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

const loadSchedulerStatus = async () => {
  try {
    const response = await apiService.get('/transactions/scheduler/status')
    schedulerStatus.value = response.data
    console.log('Scheduler status loaded:', schedulerStatus.value)
  } catch (error) {
    console.error('Error loading scheduler status:', error)
  }
}
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE')
}

function formatTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

function formatEuroValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '-'
  }

  return `${Number(value).toFixed(2)} €`
}

const currentPeriodLabel = computed(() => {
  if (!dailyStats.value.period_end) {
    return 'noch kein Zeitraum geladen'
  }

  const start = dailyStats.value.period_start
    ? `${formatDate(dailyStats.value.period_start)} ${formatTime(dailyStats.value.period_start)}`
    : 'Beginn'
  const end = `${formatDate(dailyStats.value.period_end)} ${formatTime(dailyStats.value.period_end)}`
  return `${start} bis ${end}`
})

const currentReceiptLabel = computed(() => {
  if (!dailyStats.value.receipt_min || !dailyStats.value.receipt_max) {
    return 'keine Belege'
  }

  return `#${dailyStats.value.receipt_min} bis #${dailyStats.value.receipt_max}`
})

const zbonCountedCashValue = computed(() => {
  if (zbonCountedCash.value === '' || zbonCountedCash.value === null) return null
  const value = Number(zbonCountedCash.value)
  return Number.isNaN(value) ? null : value
})

const pendingWithdrawalsTotalCents = computed(() => pendingWithdrawals.value
  .reduce((sum, withdrawal) => sum + Number(withdrawal.amount_cents || 0), 0))

const newWithdrawalsCents = computed(() => pendingWithdrawalsTotalCents.value)

const zbonModalWithdrawalTotalCents = computed(() => (
  Number(dailyStats.value.withdrawal_total || 0) + newWithdrawalsCents.value
))

const zbonModalCashCalculatedValue = computed(() => (
  Number(dailyStats.value.cash_calculated || 0) - (newWithdrawalsCents.value / 100)
))

const zbonModalCashCalculatedDisplay = computed(() => (
  formatEuroValue(zbonModalCashCalculatedValue.value)
))

const zbonFinalCashValue = computed(() => {
  if (zbonCountedCashValue.value === null) return null

  const finalValue = zbonCountedCashValue.value - (newWithdrawalsCents.value / 100)
  if (finalValue < 0) {
    return null
  }

  return Number(finalValue.toFixed(2))
})

const zbonFinalCashInvalid = computed(() => (
  zbonCountedCashValue.value !== null
  && zbonFinalCashValue.value === null
))

const zbonDifferenceValue = computed(() => {
  if (zbonFinalCashValue.value === null) return null
  return zbonFinalCashValue.value - zbonModalCashCalculatedValue.value
})

const zbonDifferenceDisplay = computed(() => {
  return zbonDifferenceValue.value === null ? '-' : formatEuroValue(zbonDifferenceValue.value)
})

const zbonNewCashBalanceDisplay = computed(() => {
  return zbonFinalCashValue.value === null ? '-' : formatEuroValue(zbonFinalCashValue.value)
})

const canCreateZbon = computed(() => (
  !!zbonForm.value.createdByUserId
  && !!zbonForm.value.verifiedByUserId
  && zbonFinalCashValue.value !== null
))

const isUserPickerTarget = computed(() => ['createdByUserId', 'withdrawalUserId'].includes(memberPickerTarget.value))

const filteredPickerOptions = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()
  const options = isUserPickerTarget.value ? financeUsers.value : memberStore.members

  if (!search) {
    return options
  }

  if (isUserPickerTarget.value) {
    return options.filter(user => `${user.username} ${user.role || ''}`.toLowerCase().includes(search))
  }

  return options.filter(member => getMemberSearchText(member).includes(search))
})

const selectedWithdrawalUserId = computed(() => withdrawalForm.value.userId)
const formatMemberLabel = (member) => getMemberShortName(member)
const formatUserLabel = (user) => user?.username || ''
const formatPickerLabel = (entry) => isUserPickerTarget.value ? formatUserLabel(entry) : formatMemberLabel(entry)
const pickerTitle = computed(() => isUserPickerTarget.value ? 'Benutzer auswählen' : 'Mitglied auswählen')
const pickerSearchPlaceholder = computed(() => (
  isUserPickerTarget.value ? 'Nach Benutzername suchen...' : 'Nach Name suchen...'
))

const getMemberById = (memberId) => {
  if (!memberId) return null
  return memberStore.members.find(member => member.id === memberId)
}

const getTransactionMemberLabel = (transaction) => {
  if (!transaction) return 'Gast'

  if (transaction.booking_type === 'CASH_WITHDRAWAL') {
    return 'Abschöpfung'
  }

  if (transaction.booking_type === 'CLUB_ACCOUNT_TOP_UP') {
    return 'Gutscheinkonto'
  }

  if (transaction.booking_type === 'GIFT_VOUCHER_CREATE' || transaction.booking_type === 'PREPAID_VOUCHER_CREATE') {
    return 'Gutscheinsystem'
  }

  const member = transaction.member || (transaction.member_name ? { name: transaction.member_name } : null)
  return formatMemberLabel(member) || transaction.member_name || 'Gast'
}

const getTransactionTypeLabel = (transaction) => {
  if (!transaction) return '-'

  if (transaction.booking_type === 'CASH_WITHDRAWAL') {
    return 'Abschöpfung'
  }

  if (transaction.booking_type === 'CLUB_ACCOUNT_TOP_UP') {
    return 'Gutscheinkonto'
  }

  if (transaction.booking_type === 'MEMBER_BALANCE_RECHARGE') {
    return 'Mitgliedsguthaben'
  }

  if (transaction.booking_type === 'GIFT_VOUCHER_CREATE') {
    return 'Gutschein erstellt'
  }

  if (transaction.booking_type === 'PREPAID_VOUCHER_CREATE') {
    return 'Verzehrkarte erstellt'
  }

  if (transaction.type === 'STORNO') {
    return 'Storno'
  }

  if (transaction.type === 'VOUCHER_REDEMPTION') {
    return 'Einlösung'
  }

  if (transaction.type === 'VOUCHER_SALE') {
    return 'Gutscheinverkauf'
  }

  if (transaction.type === 'DEPOSIT') {
    return 'Einlage'
  }

  if (transaction.type === 'RECHARGE') {
    return 'Aufladung'
  }

  return 'Verkauf'
}

const getTransactionUserLabel = (transaction) => (
  transaction?.performed_by
  || transaction?.user?.username
  || '-'
)

const getUserById = (userId) => {
  if (!userId) return null
  return financeUsers.value.find(user => user.id === userId) || null
}

const getSelectedUserName = (userId, fallback = '-') => {
  return formatUserLabel(getUserById(userId)) || fallback
}

const getSelectedVerifierName = (memberId, fallback = '-') => {
  const member = getMemberById(memberId)
  return getMemberFullName(member) || fallback
}

const getVoucherTypeLabel = (voucherType) => {
  if (voucherType === 'GIFT') {
    return 'Gutschein'
  }

  if (voucherType === 'PREPAID') {
    return 'Verzehrkarte'
  }

  return voucherType || '-'
}

const getCurrentFinanceUserOptionId = () => {
  if (!authStore.user?.id) return null
  const optionId = `user-${authStore.user.id}`
  const matchedUser = financeUsers.value.find(user => (
    user.id === optionId
    || String(user.id) === String(authStore.user.id)
  ))
  return matchedUser?.id || null
}

const getSortableTransactionId = (transaction) => {
  const rawId = transaction?.id
  if (typeof rawId === 'string') {
    const pendingMatch = rawId.match(/^pending-withdrawal-(\d+)$/)
    if (pendingMatch) {
      return {
        group: 2,
        id: Number(pendingMatch[1]),
      }
    }
  }

  const numericId = Number(rawId)
  return {
    group: Number.isFinite(numericId) && numericId < 0 ? 1 : 0,
    id: Number.isFinite(numericId) ? Math.abs(numericId) : 0,
  }
}

const loadDailyStats = async () => {
  loading.value = true
  try {
    const payload = {
      created_by_name: getSelectedUserName(zbonForm.value.createdByUserId, null),
      cash_counted_by_name: getSelectedVerifierName(zbonForm.value.verifiedByUserId, null),
      cash_count: cashCountData.value
        ? {
          coins: cashCountData.value.coins,
          notes: cashCountData.value.notes,
        }
        : null,
    }
    const response = await apiService.post('/transactions/zbon/preview', payload)
    const preview = response.data
    dailyStats.value = {
      cash_total: Math.round((preview.summary?.cash_sales_total || 0) * 100),
      balance_total: Math.round((preview.summary?.balance_sales_total || 0) * 100),
      voucher_total: Math.round((preview.summary?.voucher_sales_total || 0) * 100),
      prepaid_voucher_sales_total: Math.round((preview.summary?.prepaid_voucher_sales_total || 0) * 100),
      total_amount: Math.round((preview.summary?.total_revenue || 0) * 100),
      transaction_count: preview.summary?.transaction_count || 0,
      opening_balance: preview.summary?.opening_cash_balance || 0,
      cash_calculated: preview.summary?.cash_calculated || 0,
      withdrawal_total: Math.round((preview.summary?.cash_withdrawals_total || 0) * 100),
      voucher_open_total: preview.summary?.voucher_open_total || 0,
      voucher_created_count: preview.summary?.voucher_created_count || 0,
      voucher_created_total: preview.summary?.voucher_created_total || 0,
      voucher_redeemed_count: preview.summary?.voucher_redeemed_count || 0,
      voucher_redeemed_total: preview.summary?.voucher_redeemed_total || 0,
      voucher_open_count: preview.summary?.voucher_open_count || 0,
      material_account_total: preview.summary?.material_account_total || 0,
      club_account_total: preview.summary?.club_account_total || 0,
      period_start: preview.period_start,
      period_end: preview.period_end,
      receipt_min: preview.summary?.receipt_number_min,
      receipt_max: preview.summary?.receipt_number_max,
      report_content: preview.report_content || '',
      transactions: [...(preview.transactions || [])].sort((left, right) => {
        const dateDiff = right.created_at.localeCompare(left.created_at)
        if (dateDiff !== 0) return dateDiff

        const rightSortKey = getSortableTransactionId(right)
        const leftSortKey = getSortableTransactionId(left)
        return (rightSortKey.group - leftSortKey.group) || (rightSortKey.id - leftSortKey.id)
      }),
    }
    zBonHtml.value = preview.report_content || ''
  } catch (error) {
    console.error('Error loading Z-Bon preview:', error)
    dailyStats.value = {
      cash_total: 0,
      balance_total: 0,
      voucher_total: 0,
      prepaid_voucher_sales_total: 0,
      total_amount: 0,
      transaction_count: 0,
      opening_balance: 0,
      cash_calculated: 0,
      withdrawal_total: 0,
      voucher_open_total: 0,
      voucher_created_count: 0,
      voucher_created_total: 0,
      voucher_redeemed_count: 0,
      voucher_redeemed_total: 0,
      voucher_open_count: 0,
      material_account_total: 0,
      club_account_total: 0,
      period_start: null,
      period_end: null,
      receipt_min: null,
      receipt_max: null,
      report_content: '',
      transactions: [],
    }
    zBonHtml.value = ''
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  loadingHistory.value = true
  try {
    const params = new URLSearchParams({
      start_date: filterStartDate.value,
      end_date: filterEndDate.value,
    })
    if (filterPaymentMethod.value) {
      params.append('payment_method', filterPaymentMethod.value)
    }

    console.log('Loading filtered transactions:', params.toString())
    const data = await apiService.get(`/transactions/filtered?${params.toString()}`)
    console.log('Filtered transactions loaded:', data.data)
    filteredTransactions.value = data.data.transactions || []
    filteredStats.value = {
      total: data.data.total_amount || 0,
      voucherTotal: filteredTransactions.value.reduce(
        (sum, transaction) => sum + (transaction.voucher_applied_cents || 0),
        0
      ),
    }
  } catch (error) {
    console.error('Error loading filtered transactions:', error)
    filteredTransactions.value = []
    filteredStats.value = { total: 0, voucherTotal: 0 }
  } finally {
    loadingHistory.value = false
  }
}

const getPaymentBadgeClass = (transaction) => {
  if (transaction.booking_type === 'CASH_WITHDRAWAL') {
    return 'withdrawal'
  }

  if (transaction.booking_type === 'CLUB_ACCOUNT_TOP_UP' || transaction.booking_type === 'MEMBER_BALANCE_RECHARGE') {
    return 'recharge'
  }

  if (transaction.voucher_applied_cents > 0 && transaction.voucher_type) {
    return transaction.voucher_type === 'GIFT' ? 'voucher-gift' : 'voucher-prepaid'
  }

  if (transaction.payment_method === 'VOUCHER_GIFT') {
    return 'voucher-gift'
  }

  if (transaction.payment_method === 'VOUCHER_PREPAID') {
    return 'voucher-prepaid'
  }

  if (transaction.balance_applied_cents > 0 && transaction.payment_method === 'CASH') {
    return 'balance'
  }

  return transaction.payment_method.toLowerCase()
}

const hasCashPaymentPortion = (transaction) => (
  transaction?.payment_method === 'CASH'
  && Number(transaction?.total_amount_cents || 0) !== 0
)

const hasBalancePaymentPortion = (transaction) => (
  transaction?.payment_method === 'BALANCE'
  || Number(transaction?.balance_applied_cents || 0) > 0
)

const getPaymentBadgeParts = (transaction) => {
  if (!transaction) return []

  const parts = []

  if (transaction.voucher_applied_cents > 0 && transaction.voucher_type) {
    parts.push(transaction.voucher_type === 'GIFT' ? '🎁 Gutschein' : '🎫 Verzehrkarte')
  } else if (transaction.payment_method === 'VOUCHER_GIFT') {
    parts.push('🎁 Gutschein')
  } else if (transaction.payment_method === 'VOUCHER_PREPAID') {
    parts.push('🎫 Verzehrkarte')
  }

  if (hasBalancePaymentPortion(transaction)) {
    parts.push('💳 Guthaben')
  }

  if (hasCashPaymentPortion(transaction)) {
    parts.push('💰 BAR')
  }

  return [...new Set(parts)]
}

const getPaymentBadgeLabel = (transaction) => {
  if (transaction.booking_type === 'CASH_WITHDRAWAL') {
    return '💸 Abschöpfung'
  }

  if (transaction.booking_type === 'CLUB_ACCOUNT_TOP_UP') {
    return '🏦 Gutscheinkonto'
  }

  if (transaction.booking_type === 'MEMBER_BALANCE_RECHARGE') {
    return '⬆️ Guthaben aufladen'
  }

  if (transaction.booking_type === 'GIFT_VOUCHER_CREATE') {
    return '🎁 Gutschein erstellt'
  }

  if (transaction.booking_type === 'PREPAID_VOUCHER_CREATE') {
    return '💳 Verzehrkarte erstellt'
  }

  if (transaction.type === 'VOUCHER_SALE' && transaction.voucher_type === 'PREPAID') {
    return '💳 Verzehrkarte Verkauf'
  }

  const paymentBadgeParts = getPaymentBadgeParts(transaction)
  if (paymentBadgeParts.length > 0) {
    return paymentBadgeParts.join(' + ')
  }

  if (transaction.payment_method === 'WITHDRAWAL') {
    return '💸 Abschöpfung'
  }

  return transaction.payment_method === 'CASH' ? '💰 BAR' : '💳 Guthaben'
}

const loadRevenueStats = async () => {
  try {
    console.log('Loading revenue stats')
    const data = await apiService.get('/transactions/revenue-stats')
    console.log('Revenue stats loaded:', data.data)
    revenueStats.value = data.data
  } catch (error) {
    console.error('Error loading revenue stats:', error)
  }
}

const loadMemberStats = async () => {
  try {
    console.log('Loading member stats')
    const data = await apiService.get('/members/statistics')
    console.log('Member stats loaded:', data.data)
    memberStats.value = data.data
  } catch (error) {
    console.error('Error loading member stats:', error)
  }
}

const loadMaterialAccount = async () => {
  if (!authStore.isAdmin) return

  try {
    const response = await apiService.get('/admin/vouchers/material-account')
    materialAccount.value = response.data
  } catch (error) {
    console.error('Error loading material account:', error)
  }
}

const loadClubAccount = async () => {
  if (!authStore.isAdmin) return

  try {
    const response = await apiService.get('/admin/vouchers/club-account')
    clubAccount.value = response.data
  } catch (error) {
    console.error('Error loading club account:', error)
  }
}

const loadInternalAccounts = async () => {
  if (!authStore.isAdmin) return

  await Promise.all([
    loadClubAccount(),
    loadMaterialAccount(),
  ])
}

const toggleTransaction = (transactionId) => {
  if (expandedTransactions.value.has(transactionId)) {
    expandedTransactions.value.delete(transactionId)
  } else {
    expandedTransactions.value.add(transactionId)
  }
}

const buildInternalAccountEntryKey = (accountType, entryId) => `${accountType}:${entryId}`

const toggleInternalAccountSection = (accountType) => {
  if (expandedInternalAccountSections.value.has(accountType)) {
    expandedInternalAccountSections.value.delete(accountType)
  } else {
    expandedInternalAccountSections.value.add(accountType)
  }
}

const isInternalAccountSectionExpanded = (accountType) => (
  expandedInternalAccountSections.value.has(accountType)
)

const toggleInternalAccountEntry = (accountType, entryId) => {
  const key = buildInternalAccountEntryKey(accountType, entryId)
  if (expandedInternalAccountEntries.value.has(key)) {
    expandedInternalAccountEntries.value.delete(key)
  } else {
    expandedInternalAccountEntries.value.add(key)
  }
}

const isInternalAccountEntryExpanded = (accountType, entryId) => (
  expandedInternalAccountEntries.value.has(buildInternalAccountEntryKey(accountType, entryId))
)

const openCashCounterModal = () => {
  showCashCounterModal.value = true
}
const onCashCounterConfirm = (data) => {
  cashCountData.value = data
  zbonCountedCash.value = data.total.toFixed(2)
  loadDailyStats()
}

const loadFinanceUsers = async () => {
  const response = await apiService.get('/users/finance-options')
  financeUsers.value = response.data
}

const openMemberPicker = async (target) => {
  memberPickerTarget.value = target
  memberSearch.value = ''
  if (!memberStore.members.length) {
    await memberStore.getMembers()
  }
  showMemberPickerModal.value = true
}

const openUserPicker = async (target) => {
  memberPickerTarget.value = target
  memberSearch.value = ''
  if (!financeUsers.value.length) {
    await loadFinanceUsers()
  }
  showMemberPickerModal.value = true
}

const closeMemberPicker = () => {
  showMemberPickerModal.value = false
  memberPickerTarget.value = null
  memberSearch.value = ''
}

const selectPickerOption = (entry) => {
  if (memberPickerTarget.value === 'createdByUserId') {
    zbonForm.value.createdByUserId = entry.id
  } else if (memberPickerTarget.value === 'verifiedByUserId') {
    zbonForm.value.verifiedByUserId = entry.id
  } else if (memberPickerTarget.value === 'withdrawalUserId') {
    withdrawalForm.value.userId = entry.id
  }

  closeMemberPicker()
}

// Download Z-Bon as HTML file
const handleDownloadZBon = async () => {
  try {
    if (!zBonHtml.value) {
      await loadDailyStats()
    }

    triggerHtmlDownload(zBonHtml.value, buildZbonHtmlFilename(zbonHtmlDownloadMeta.value))
    notificationStore.success('Z-Bon HTML erfolgreich heruntergeladen')
  } catch (error) {
    console.error('Error downloading Z-Bon HTML:', error)
    notificationStore.error(`Fehler beim Download: ${error.response?.data?.detail || error.message}`)
  }
}

const openZbonCreateModal = async () => {
  if (!financeUsers.value.length) {
    await loadFinanceUsers()
  }
  zbonForm.value.createdByUserId = getCurrentFinanceUserOptionId()
  zbonForm.value.verifiedByUserId = null
  pendingWithdrawals.value = []
  await loadDailyStats()
  zbonCountedCash.value = ''
  zbonHtmlDownloadMeta.value = {
    period_end: dailyStats.value.period_end,
  }
  showZbonCreateModal.value = true
}

const closeZbonCreateModal = () => {
  showZbonCreateModal.value = false
  pendingWithdrawals.value = []
  loadDailyStats()
}

const openPreviewModal = async () => {
  await loadDailyStats()
  if (zBonHtml.value) {
    zbonHtmlModalTitle.value = '📋 Z-Bon Vorschau'
    zbonHtmlDownloadMeta.value = {
      period_end: dailyStats.value.period_end,
    }
    showZbonPreviewModal.value = true
  }
}

const openWithdrawalModal = async () => {
  if (!financeUsers.value.length) {
    await loadFinanceUsers()
  }
  withdrawalForm.value.userId = getCurrentFinanceUserOptionId()
  showWithdrawalModal.value = true
}

const closeWithdrawalModal = () => {
  withdrawalForm.value = {
    amount: '',
    userId: null,
    note: '',
  }
  showWithdrawalModal.value = false
}

const submitWithdrawal = async () => {
  const amount = Number(withdrawalForm.value.amount)
  if (Number.isNaN(amount) || amount <= 0) {
    notificationStore.error('Bitte einen gültigen Betrag eingeben')
    return
  }

  const userName = getSelectedUserName(withdrawalForm.value.userId, '')
  if (!userName) {
    notificationStore.error('Bitte einen Benutzer auswählen')
    return
  }

  const note = withdrawalForm.value.note?.trim()
  const reason = note
    ? `Abschöpfung - ${userName} - ${note}`
    : `Abschöpfung - ${userName}`

  try {
    loading.value = true
    if (showZbonCreateModal.value) {
      pendingWithdrawals.value.push({
        amount_cents: Math.round(amount * 100),
        reason,
      })
      notificationStore.success('Abschöpfung für den Z-Bon vorgemerkt')
    } else {
      await apiService.post('/transactions/cash/withdrawal', {
        amount_cents: Math.round(amount * 100),
        reason,
      })
      notificationStore.success('Abschöpfung erfolgreich gespeichert')
    }
    closeWithdrawalModal()
    await loadDailyStats()
    if (activeTab.value === 'zbons' && !showZbonCreateModal.value) {
      await loadZbonsHistory()
    }
  } catch (error) {
    console.error('Error recording withdrawal:', error)
    notificationStore.error(`Fehler beim Speichern: ${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const requestZBonCreate = () => {
  if (!canCreateZbon.value) {
    notificationStore.error('Bitte Zählung und Auswahl vervollständigen')
    return
  }
  showPasswordModal.value = true
}

const createZBon = async (password) => {
  showPasswordModal.value = false
  const employeeName = getSelectedUserName(zbonForm.value.createdByUserId, '')
  const checkerName = getSelectedVerifierName(zbonForm.value.verifiedByUserId, '')

  if (!employeeName) {
    notificationStore.error('Bitte einen Mitarbeiter auswählen')
    return
  }

  if (!checkerName) {
    notificationStore.error('Bitte eine Sichtkontrolle auswählen')
    return
  }

  if (zbonCountedCashValue.value === null) {
    notificationStore.error('Bitte den Ist-Barbestand erfassen')
    return
  }

  try {
    loading.value = true
    await apiService.post('/transactions/zbon/create', {
      created_by_name: employeeName,
      cash_counted_by_name: checkerName,
      auth_password: password,
      cash_count_total: zbonFinalCashValue.value,
      pending_withdrawals: pendingWithdrawals.value,
    })
    notificationStore.success('Z-Bon erfolgreich erstellt')
    closeZbonCreateModal()
    zbonForm.value = {
      createdByUserId: null,
      verifiedByUserId: null,
    }
    pendingWithdrawals.value = []
    cashCountData.value = null
    zbonCountedCash.value = ''
    await loadDailyStats()
    if (activeTab.value === 'zbons') {
      await loadZbonsHistory()
    }
  } catch (error) {
    console.error('Error creating Z-Bon:', error)
    notificationStore.error(`Fehler beim Erstellen: ${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

// Watch für Filteränderungen
watch([filterStartDate, filterEndDate, filterPaymentMethod], () => {
  applyFilters()
})

// Z-Böns History Methods
const loadZbonsHistory = async () => {
  loadingZbons.value = true
  try {
    const params = {
      page: zbonsCurrentPage.value,
      page_size: 20,
    }
    
    if (zbonsFilterStartDate.value) {
      params.start_date = zbonsFilterStartDate.value
    }
    if (zbonsFilterEndDate.value) {
      params.end_date = zbonsFilterEndDate.value
    }
    
    console.log('[Finance] Loading Z-Böns history with params:', params)
    const response = await apiService.get('/transactions/zbon/history', { params })
    const payload = response.data
    zbonsList.value = payload.histories || []
    zbonsTotalPages.value = payload.total_pages || 1
    console.log('[Finance] Z-Böns history loaded:', zbonsList.value.length, 'entries, total pages:', zbonsTotalPages.value)
  } catch (error) {
    console.error('[Finance] Error loading Z-Böns history:', error)
    console.error('[Finance] Error details:', error.response?.data || error.message)
    notificationStore.error('Fehler beim Laden der Z-Bons Verlauf: ' + (error.message || 'Unbekannter Fehler'))
  } finally {
    loadingZbons.value = false
  }
}

const formatDateForFilename = (value) => {
  const today = new Date().toISOString().split('T')[0]
  if (!value) {
    return today
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return today
  }

  return date.toISOString().split('T')[0]
}

const buildZbonHtmlFilename = (zbon) => {
  const datePart = formatDateForFilename(zbon?.business_date || zbon?.period_end)
  const baseName = zbon?.sequence_number ? `Z-Bon-${zbon.sequence_number}` : 'Z-Bon-Vorschau'
  return `${baseName}_${datePart}.html`
}

const triggerHtmlDownload = (html, filename) => {
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.parentNode.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const downloadCurrentZbonHtml = async () => {
  await handleDownloadZBon()
}

const openZbonHistoryModal = async (zbon) => {
  try {
    const response = await apiService.get(`/transactions/zbon/history/${zbon.sequence_number}/html`, {
      responseType: 'text',
    })
    zBonHtml.value = response.data
    zbonHtmlModalTitle.value = `📑 Z-Bon #${zbon.sequence_number}`
    zbonHtmlDownloadMeta.value = zbon
    showZbonPreviewModal.value = true
  } catch (error) {
    console.error('[Finance] Error loading Z-Bon HTML detail:', error)
    notificationStore.error('Fehler beim Laden der Z-Bon-Ansicht')
  }
}

// Computed properties for Z-Böns
const zbonsTotalCash = computed(() => {
  return zbonsList.value.reduce((sum, zbon) => sum + (zbon.gross_revenue_cash * 100), 0)
})

const zbonsTotalBalance = computed(() => {
  return zbonsList.value.reduce((sum, zbon) => sum + (zbon.gross_revenue_balance * 100), 0)
})

const zbonsTotalRevenue = computed(() => {
  return zbonsList.value.reduce((sum, zbon) => sum + ((zbon.total_revenue || 0) * 100), 0)
})

const resolveActiveTab = (requestedTab) => (tabs.value.includes(requestedTab) ? requestedTab : tabs.value[0] || DEFAULT_FINANCE_TAB)

watch(() => route.query.tab, (requestedTab) => {
  const nextTab = resolveActiveTab(typeof requestedTab === 'string' ? requestedTab : '')
  if (activeTab.value !== nextTab) {
    activeTab.value = nextTab
  }
}, { immediate: true })

watch(tabs, (availableTabs) => {
  if (!availableTabs.includes(activeTab.value)) {
    activeTab.value = availableTabs[0] || DEFAULT_FINANCE_TAB
  }
})

// Watch für Tab-Wechsel
watch(activeTab, (newTab) => {
  if (route.query.tab !== newTab) {
    router.replace({ query: { ...route.query, tab: newTab } })
  }

  console.log('Switched to tab:', newTab)
  if (newTab === 'zbon' && dailyStats.value.transaction_count === 0) {
    loadDailyStats()
  } else if (newTab === 'history' && filteredTransactions.value.length === 0) {
    applyFilters()
  } else if (newTab === 'zbons') {
    loadZbonsHistory()
  } else if (newTab === 'revenue' && revenueStats.value.week_total === 0) {
    loadRevenueStats()
  } else if (newTab === 'members' && memberStats.value.total_members === 0) {
    loadMemberStats()
  } else if (
    newTab === 'internalAccounts'
    && authStore.isAdmin
    && !clubAccount.value.entries.length
    && !materialAccount.value.entries.length
  ) {
    loadInternalAccounts()
  }
})

// Watch für Z-Böns Filter-Änderungen
watch([zbonsFilterStartDate, zbonsFilterEndDate, zbonsCurrentPage], () => {
  if (activeTab.value === 'zbons') {
    loadZbonsHistory()
  }
})

onMounted(() => {
  console.log('Finance component mounted, loading data...')
  memberStore.getMembers()
  loadFinanceUsers()
  loadDailyStats()
  applyFilters()
  loadRevenueStats()
  loadMemberStats()
  loadInternalAccounts()
  loadSchedulerStatus()
})
</script>

<style scoped lang="scss">
.admin-finance {
  background: #dde2e8;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);

  h2 {
    margin-bottom: 0.6rem;
    color: #333;
  }

  h3 {
    margin-bottom: 0.75rem;
    color: #555;
  }

  h4 {
    margin: 0.75rem 0 0.5rem 0;
    color: #666;
  }
}

.finance-tabs {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.35rem 0 0.7rem;
  border-bottom: 1px solid #aeb5be;
  flex-wrap: wrap;
  background: #dde2e8;
}

.tab-btn {
  padding: 0.5rem 0.9rem;
  background: color-mix(in srgb, var(--app-banner-color) 14%, white);
  border: 1px solid color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  color: #334155;
  transition: all 0.2s;

  &:hover {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.tab-content {
  animation: fadeIn 0.2s;
}

@media (max-width: 700px) {
  .admin-finance {
    padding: 1rem;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.date-picker {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0;

  label {
    font-weight: 600;
  }

  input {
    padding: 0.5rem;
    border: 1px solid #9ca4ae;
    border-radius: 8px;
    font-size: 1rem;
  }
}

.zbon-layout {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.zbon-section {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(24, 28, 34, 0.08);
  border-radius: 18px;
  padding: 0.85rem 1rem;
  box-shadow: 0 8px 20px rgba(24, 28, 34, 0.08);
}

.internal-account-sections {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.internal-account-section {
  margin: 0;
}

.zbon-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;

  h4 {
    margin: 0 0 0.25rem;
  }

  p {
    margin: 0;
    color: #5b6470;
  }
}

.internal-account-header {
  margin-bottom: 0;
}

.internal-account-section-body {
  margin-top: 1rem;
}

.internal-account-toggle {
  flex-shrink: 0;
}

.filter-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #d8dde3;
  border-radius: 8px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  input,
  select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #9ca4ae;
    border-radius: 8px;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.zbon-card-grid {
  margin-bottom: 0;

  &.secondary {
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  }
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);

  &.highlight {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.warning {
    background: linear-gradient(135deg, #ffb74d 0%, #ef6c00 100%);
  }

  &.neutral {
    background: linear-gradient(135deg, #475569 0%, #334155 100%);
  }

  .card-label {
    font-size: 0.85rem;
    opacity: 0.9;
    margin-bottom: 0.3rem;
  }

  .card-value {
    font-size: 1.5rem;
    font-weight: bold;
  }
}

.zbon-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;

  .btn {
    min-height: 52px;
  }
}

.daily-transactions,
.payment-stats,
.top-products {
  margin: 0;
}

.transactions-table,
.products-table,
.members-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;

  thead {
    background: #d8dde3;

    th {
      padding: 0.55rem 0.75rem;
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid #ddd;
    }
  }

  tbody {
    tr {
      border-bottom: 1px solid #eee;

      &:hover {
        background: #dde2e8;
      }

      td {
        padding: 0.5rem 0.75rem;

        &.amount {
          font-weight: 600;
          color: #667eea;
        }
      }
    }
  }
}

.payment-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-block;

  &.cash {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.balance {
    background: #e3f2fd;
    color: #1565c0;
  }

  &.recharge {
    background: #fff3e0;
    color: #e65100;
  }

  &.withdrawal {
    background: #ffebee;
    color: #c62828;
  }

  &.voucher-gift {
    background: rgba(255, 107, 53, 0.16);
    color: #b84b1f;
  }

  &.voucher-prepaid {
    background: rgba(255, 107, 53, 0.1);
    color: #ff6b35;
  }
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.scheduler-section {
  .scheduler-status {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
}

.history-summary,
.revenue-overview,
.member-stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.summary-item,
.stat-card,
.revenue-card {
  background: #d8dde3;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  span {
    &:first-child {
      font-weight: 600;
    }

    &.amount {
      font-size: 1.3rem;
      font-weight: bold;
      color: #667eea;
    }
  }
}

.stat-card {
  .stat-label {
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
  }
}

.revenue-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  &.warning {
    background: linear-gradient(135deg, #ffb74d 0%, #ef6c00 100%);
  }

  .card-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }

  .card-value {
    font-size: 1.8rem;
    font-weight: bold;
    margin-top: 0.5rem;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;

  .stat-label {
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 0.5rem;
  }

  .stat-percent {
    font-size: 0.9rem;
    color: #999;
  }
}

.btn {
  padding: 0.65rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;

  &:hover {
    background: #1565c0;
  }
}

.btn-info {
  background: #00bcd4;
  color: white;

  &:hover {
    background: #0097a7;
  }
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover {
    background: #e2e8f0;
  }
}

.zbon-actions {
  display: flex;
  gap: 0.75rem;
  margin: 0 0 1.5rem 0;
  flex-wrap: wrap;
}
.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.scheduler-section {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  border-left: 4px solid #ff9800;
}

.scheduler-status {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  gap: 1rem;
  align-items: center;

  span:first-child {
    font-weight: 600;
    color: #666;
  }
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;

  &.running {
    background: #c8e6c9;
    color: #2e7d32;
  }

  &.stopped {
    background: #ffcccc;
    color: #c62828;
  }
}

.next-run {
  color: #667eea;
  font-weight: 600;
}

.scheduler-info {
  margin: 1rem 0 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
}

.config-list {
  margin: 0.5rem 0 0 1.5rem;
  color: #666;
  font-size: 0.9rem;

  li {
    margin: 0.3rem 0;

    code {
      background: #fff;
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-family: monospace;
      color: #d32f2f;
    }
  }
}
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1rem;
}

.confirmation-dialog {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 400px;
  width: min(100%, 520px);
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  text-align: center;

  h3 {
    margin: 0 0 1rem 0;
    color: #1e293b;
    font-size: 1.2rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #e2e8f0;
    text-align: left;
  }

  p {
    margin: 0 0 1.5rem 0;
    color: #666;
  }
}

.zbon-create-dialog {
  max-width: min(92vw, 1080px);
  width: min(92vw, 1080px);
  text-align: left;
  padding: 1.25rem;
}

.zbon-create-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 1rem;
  align-items: start;
}

.zbon-note-box {
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: #eef4ff;
  border: 1px solid #c8d8f2;
  color: #22446b;
  font-weight: 500;
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.compact-summary-grid {
  margin-bottom: 0;
  gap: 0.75rem;
}

.zbon-balance-group {
  padding: 0.9rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid #cbd5e1;
}

.zbon-counted-group {
  margin-bottom: 0.75rem;
}

.zbon-side-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.modal-summary-card {
  padding: 1.15rem;

  .card-label {
    font-size: 0.82rem;
    margin-bottom: 0.35rem;
  }

  .card-value {
    font-size: 1.45rem;
    line-height: 1.2;
  }
}

.zbon-warning-text {
  display: block;
  margin-top: 0.75rem;
  color: #b91c1c;
  font-weight: 600;
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.zbon-create-buttons {
  flex-direction: column;
  align-items: stretch;
}

.selection-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  text-align: left;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }
}

.selection-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.member-select-btn {
  padding: 0.75rem 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  text-align: left;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #eef2f7;
    border-color: #94a3b8;
  }
}

.clear-selection-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  cursor: pointer;
}

.member-picker-overlay {
  z-index: 1600;
}

.member-picker-dialog {
  max-width: 520px;
}

.member-search-input {
  width: 100%;
  margin-bottom: 1rem;
}

.member-picker-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 360px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.member-picker-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.75rem 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  font-weight: 600;
  color: #1e293b;
  transition: all 0.2s;

  &:hover {
    background: #eef2f7;
    border-color: #94a3b8;
  }
}

.member-picker-photo {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  overflow: hidden;
  background: #cbd5e1;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    color: #475569;
    font-size: 1.1rem;
  }
}

.member-picker-empty {
  margin: 0;
  padding: 1rem 0;
}

@media (max-width: 900px) {
  .zbon-create-layout {
    grid-template-columns: 1fr;
  }

  .zbon-side-summary {
    grid-template-columns: 1fr;
  }

  .selection-actions {
    flex-direction: column;
    align-items: stretch;
  }
}

.transaction-row {
  &:hover {
    background: #f0f0f0;
  }
}

.items-row {
  background: #d8dde3;

  td {
    padding: 0 !important;
  }
}

.items-cell {
  background: #d8dde3 !important;
  padding: 0.5rem 1rem !important;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-detail {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  background: #eef1f4;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  font-size: 0.9rem;

  .item-name {
    font-weight: 600;
    flex: 1;
  }

  .item-qty {
    color: #666;
    min-width: 40px;
  }

  .item-price {
    color: #666;
    min-width: 60px;
    text-align: right;
  }

  .item-total {
    font-weight: 600;
    color: #667eea;
    min-width: 70px;
    text-align: right;
  }
}

.internal-material-item-detail {
  flex-wrap: wrap;
}

.item-detail-note {
  width: 100%;
  margin-top: 0.25rem;
  color: #475569;
  font-size: 0.85rem;
  padding-top: 0.35rem;
  border-top: 1px dashed #c3ced9;
}

.no-items {
  padding: 1rem;
  text-align: center;
  color: #999;
  font-style: italic;
}

.zbon-preview {
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
}

.zbon-preview-dialog {
  width: min(96vw, 2200px);
  max-width: min(96vw, 2200px);
}

.zbon-preview-frame-shell {
  background: white;
  border-radius: 8px;
  max-height: min(80vh, 1200px);
  overflow: hidden;
  border: 1px solid #eee;
}

.zbon-preview-frame {
  width: 100%;
  min-height: min(80vh, 1200px);
  border: 0;
  display: block;
}

/* Z-Böns History Table Styles */
.table-container {
  overflow-x: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.amount.withdrawal {
  color: #d32f2f;
  font-weight: bold;
}

.amount.deposit {
  color: #388e3c;
  font-weight: bold;
}

.date {
  color: #666;
  font-size: 0.9rem;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;

  tr {
    border-bottom: 1px solid #eee;
  }

  td {
    padding: 0.75rem;

    &:first-child {
      width: 200px;
      font-weight: 500;
      color: #333;
      background: #f5f5f5;
    }

    &.currency {
      text-align: right;
      font-family: 'Courier New', monospace;
      font-weight: 500;
    }

    &.positive {
      color: #388e3c;
    }

    &.negative {
      color: #d32f2f;
    }
  }

  tr.section-row {
    background: #f0f0f0;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;

  span {
    color: #666;
    font-weight: 500;
  }

  button {
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.btn-success {
  background: #4caf50;
  color: white;

  &:hover {
    background: #45a049;
  }
}

.btn-warning {
  background: #ff9800;
  color: white;

  &:hover {
    background: #e65100;
  }
}

.btn-ready {
  background: #2e7d32;
  color: white;
}

.btn-disabled {
  background: #9ca3af;
  color: white;
  cursor: not-allowed;
}
</style>
