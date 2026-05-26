<template>
  <div
    class="admin-finance"
    :style="{ '--finance-sticky-offset': `${financeHeaderHeight}px` }"
  >
    <!-- Sticky Header -->
    <div
      ref="financeHeader"
      class="page-header sticky-header"
    >
      <div class="title-row">
        <h2>Finanzen</h2>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Tagesabrechnungen, Kassenberichte und Umsatzübersichten.</span>
      </div>

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

      <!-- Sticky Action Bar – nur beim Z-Bon Tab -->
      <div
        v-if="activeTab === 'zbon'"
        class="action-bar"
      >
        <div class="period-info">
          <strong>Aktueller Zeitraum:</strong> {{ currentPeriodLabel }}
          <span class="receipt-info">• {{ currentReceiptLabel }}</span>
        </div>
        <div class="action-buttons">
          <button
            class="btn btn-secondary"
            @click="openCashCounterModal"
          >
            💰 Kasse zählen
          </button>
          <button
            v-if="authStore.isAdmin"
            class="btn btn-warning"
            @click="openWithdrawalModal"
          >
            💸 Abschöpfung
          </button>
          <button
            class="btn btn-primary"
            @click="openPreviewModal"
          >
            👁️ Vorschau
          </button>
          <button
            class="btn btn-info"
            @click="openZbonCreateModal"
          >
            ✅ Kassenbericht erstellen
          </button>
          <button
            class="btn btn-success"
            @click="handleDownloadZBon"
          >
            ⬇️ HTML
          </button>
        </div>
      </div>
    </div>

    <!-- Z-BON / Tagesabrechnung -->
    <div
      v-if="activeTab === 'zbon'"
      class="tab-content compact-content"
    >
      <div
        v-if="loading"
        class="loading"
      >
        Lade Daten...
      </div>
      <div
        v-else
        class="zbon-layout"
      >
        <!-- Summary Strip -->
        <div class="summary-strip">
          <div class="ss-item">
            <div class="ss-icon">
              💵
            </div>
            <span class="ss-label">Bar-Einnahmen</span>
            <span class="ss-value ss-green">{{ formatPrice(dailyStats.cash_total) }}</span>
          </div>
          <div class="ss-item">
            <div class="ss-icon">
              🪙
            </div>
            <span class="ss-label">Guthaben eingelöst</span>
            <span class="ss-value ss-blue">{{ formatPrice(dailyStats.balance_total) }}</span>
          </div>
          <div class="ss-item">
            <div class="ss-icon">
              🎟
            </div>
            <span class="ss-label">Gutscheine</span>
            <span class="ss-value ss-orange">{{ formatPrice(dailyStats.voucher_total) }}</span>
          </div>
          <div class="ss-item">
            <div class="ss-icon">
              💳
            </div>
            <span class="ss-label">Verzehrkarten</span>
            <span class="ss-value ss-blue">{{ formatPrice(dailyStats.prepaid_voucher_sales_total) }}</span>
          </div>
          <div class="ss-item ss-total-item">
            <div class="ss-icon">
              🧮
            </div>
            <span class="ss-label">Gesamt</span>
            <span class="ss-value ss-total">{{ formatPrice(dailyStats.total_amount) }}</span>
          </div>
        </div>

        <!-- Accordion -->
        <div class="accordion">
          <!-- 1. Einnahmen nach Zahlungsart (open by default) -->
          <div class="acc-section">
            <div
              class="acc-header"
              @click="toggleAccSection('einnahmen')"
            >
              <div class="acc-header-left">
                <span class="acc-icon">💰</span>
                <span class="acc-title">Einnahmen nach Zahlungsart</span>
              </div>
              <span class="acc-summary">Gesamt: {{ formatPrice(dailyStats.total_amount) }}</span>
              <span
                class="acc-chevron"
                :class="{ open: accSections.einnahmen }"
              />
            </div>
            <div
              v-show="accSections.einnahmen"
              class="acc-body"
            >
              <div class="acc-stat-rows">
                <div class="acc-row">
                  <span class="acc-row-label">💵 Bar-Einnahmen</span>
                  <span class="acc-row-value green">{{ formatPrice(dailyStats.cash_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">🪙 Guthaben eingelöst</span>
                  <span class="acc-row-value blue">{{ formatPrice(dailyStats.balance_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">🎟 Gutscheine (Gewinn)</span>
                  <span class="acc-row-value orange">{{ formatPrice(dailyStats.voucher_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">💳 Prepaid-Kartenverkauf</span>
                  <span class="acc-row-value blue">{{ formatPrice(dailyStats.prepaid_voucher_sales_total) }}</span>
                </div>
                <div class="acc-row acc-total-row">
                  <span class="acc-row-label">Umsatz Gesamt</span>
                  <span class="acc-row-value big">{{ formatPrice(dailyStats.total_amount) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 2. Kassensaldo (open by default) -->
          <div class="acc-section">
            <div
              class="acc-header"
              @click="toggleAccSection('saldo')"
            >
              <div class="acc-header-left">
                <span class="acc-icon">🏧</span>
                <span class="acc-title">Kassensaldo (Soll-Berechnung)</span>
              </div>
              <span class="acc-summary">Soll: {{ formatEuroValue(dailyStats.cash_calculated) }}</span>
              <span
                class="acc-chevron"
                :class="{ open: accSections.saldo }"
              />
            </div>
            <div
              v-show="accSections.saldo"
              class="acc-body"
            >
              <table class="calc-table">
                <tbody>
                  <tr>
                    <td>Anfangsbestand</td>
                    <td class="calc-right">
                      {{ formatEuroValue(dailyStats.opening_balance) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="calc-op">
                      + Bar-Einnahmen
                    </td>
                    <td class="calc-right calc-plus">
                      +{{ formatPrice(dailyStats.cash_total) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="calc-op">
                      + Prepaid-Verkäufe
                    </td>
                    <td class="calc-right calc-plus">
                      +{{ formatPrice(dailyStats.prepaid_voucher_sales_total) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="calc-op">
                      − Abschöpfungen
                    </td>
                    <td class="calc-right calc-minus">
                      −{{ formatPrice(dailyStats.withdrawal_total) }}
                    </td>
                  </tr>
                  <tr class="calc-total-row">
                    <td><strong>= Soll-Bestand</strong></td>
                    <td class="calc-right">
                      <strong>{{ formatEuroValue(dailyStats.cash_calculated) }}</strong>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 3. Offene Posten & Konten (closed by default) -->
          <div class="acc-section">
            <div
              class="acc-header"
              @click="toggleAccSection('offene')"
            >
              <div class="acc-header-left">
                <span class="acc-icon">📂</span>
                <span class="acc-title">Offene Posten &amp; Konten</span>
              </div>
              <span class="acc-summary">
                Gutscheine: {{ formatEuroValue(dailyStats.voucher_open_total) }} · Konto: {{ formatEuroValue(dailyStats.club_account_total) }}
              </span>
              <span
                class="acc-chevron"
                :class="{ open: accSections.offene }"
              />
            </div>
            <div
              v-show="accSections.offene"
              class="acc-body"
            >
              <div class="acc-stat-rows">
                <div class="acc-row">
                  <span class="acc-row-label">🎫 Offene Gutscheine</span>
                  <span class="acc-row-value orange">{{ formatEuroValue(dailyStats.voucher_open_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">🏦 Gutscheinkonto gesamt</span>
                  <span class="acc-row-value blue">{{ formatEuroValue(dailyStats.club_account_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">💸 Abschöpfungen gesamt</span>
                  <span class="acc-row-value red">{{ formatPrice(dailyStats.withdrawal_total) }}</span>
                </div>
                <div class="acc-row">
                  <span class="acc-row-label">🔢 Transaktionen im Zeitraum</span>
                  <span class="acc-row-value">{{ dailyStats.transaction_count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Transaktionen (open by default) -->
          <div class="acc-section">
            <div
              class="acc-header"
              @click="toggleAccSection('transaktionen')"
            >
              <div class="acc-header-left">
                <span class="acc-icon">📋</span>
                <span class="acc-title">Transaktionen</span>
              </div>
              <span class="acc-summary">{{ dailyStats.transaction_count }} gesamt</span>
              <span
                class="acc-chevron"
                :class="{ open: accSections.transaktionen }"
              />
            </div>
            <div
              v-show="accSections.transaktionen"
              class="acc-body"
            >
              <div
                v-if="dailyStats.transactions.length === 0"
                class="empty"
              >
                Keine Transaktionen im aktuellen Kassenbericht-Zeitraum
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
                        <span :class="['payment-badge', getPaymentBadgeClass(transaction)]">
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
            </div>
          </div>
        </div>

        <!-- Scheduler Info -->
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
            Der automatische Kassenbericht-Versand muss in der .env-Datei konfiguriert werden:
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
      <h3>📑 Kassenberichte</h3>

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
              Anzahl Kassenberichte
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
            Keine Kassenberichte für den ausgewählten Zeitraum
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

    <!-- Transaktionshistorie -->
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

    <!-- Korrekturen -->
    <div
      v-if="activeTab === 'corrections'"
      class="tab-content tab-content--flush"
    >
      <Corrections />
    </div>

    <!-- Interne Konten -->
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

<!--
  ================================================================
  KONSOLIDIERTE MODAL-TEMPLATES – Finance.vue
  Ersetzt die vier bestehenden Modal-Blöcke am Ende des Templates
  (ab "Cash Counter Modal" bis Ende der Datei, vor </div> .admin-finance).

  Klassen-Mapping (alt → neu):
    .confirmation-dialog              bleibt als Overlay-Wrapper
    .zbon-create-dialog               → .kk-dialog
    .withdrawal-dialog                → .kk-dialog .kk-dialog--narrow
    .member-picker-dialog             → .kk-dialog .kk-dialog--narrow
    .zbon-preview-dialog              → .kk-dialog .kk-dialog--wide
    .zbon-modal-header                → .kk-dialog__header
    .close-btn                        → .kk-dialog__close
    .zbon-subtitle                    → .kk-dialog__subtitle
    .modal-body                       → .kk-dialog__body
    .modal-actions / .confirmation-buttons → .kk-dialog__footer
    .info-box                         → .kk-info-box
    .form-grid                        → .kk-form-grid
    .form-group                       → .kk-form-group
    .select-btn                       → .kk-select-btn
    .clear-selection-btn              → .kk-clear-btn
    .selection-actions                → .kk-selection-row
    .balance-summary                  → .kk-balance-box
    .balance-row                      → .kk-balance-row
    .counted-input                    → .kk-counted-input
    .final-result                     → .kk-result-box
    .result-row                       → .kk-result-row
    .zbon-warning-text                → .kk-warning-text
    .member-search-input              → .kk-picker-search
    .member-picker-list               → .kk-picker-list
    .member-picker-item               → .kk-picker-item
    .member-picker-photo              → .kk-picker-photo
    .member-picker-empty              → .kk-picker-empty
    .zbon-preview-frame-shell         → .kk-preview-shell
    .zbon-preview-frame               → .kk-preview-frame
  ================================================================
-->

    <!-- Cash Counter Modal (Stil bereits ok, nur Shell angleichen) -->
    <CashCounterModal
      :show="showCashCounterModal"
      @close="showCashCounterModal = false"
      @confirm="onCashCounterConfirm"
    />

    <!-- ═══════════════════════════════════════════════════════════
         Z-BON ERSTELLEN
    ════════════════════════════════════════════════════════════ -->
    <div
      v-if="showZbonCreateModal"
      class="confirmation-overlay"
    >
      <div class="kk-dialog">

        <div class="kk-dialog__header">
          <div>
            <h3>🧾 Kassenbericht erstellen</h3>
            <p class="kk-dialog__subtitle">Kassenabschluss durchführen und Z-Bon erstellen</p>
          </div>
          <button class="kk-dialog__close" @click="closeZbonCreateModal">✕</button>
        </div>

        <div class="kk-dialog__body">

          <!-- Ablauf-Hinweis -->
          <div class="kk-info-box">
            Kassenprüfer wählen → Kasse zählen → ggf. Abschöpfung → Kassenbericht erstellen
          </div>

          <!-- Benutzer-Auswahl -->
          <div class="kk-form-grid">
            <div class="kk-form-group">
              <label>Erstellt von</label>
              <button
                class="kk-select-btn"
                @click="openUserPicker('createdByUserId')"
              >
                {{ getSelectedUserName(zbonForm.createdByUserId, 'Benutzer auswählen …') }}
              </button>
            </div>
            <div class="kk-form-group">
              <label>Kassenprüfer</label>
              <div class="kk-selection-row">
                <button
                  class="kk-select-btn"
                  @click="openMemberPicker('verifiedByUserId')"
                >
                  {{ getSelectedVerifierName(zbonForm.verifiedByUserId, 'Mitglied auswählen …') }}
                </button>
                <button
                  v-if="zbonForm.verifiedByUserId"
                  class="kk-clear-btn"
                  @click="zbonForm.verifiedByUserId = null"
                >
                  Entfernen
                </button>
              </div>
            </div>
          </div>

          <!-- Saldo-Übersicht -->
          <div class="kk-balance-box">
            <div class="kk-balance-row">
              <span>Vorheriger Barbestand</span>
              <strong>{{ formatEuroValue(dailyStats.opening_balance) }}</strong>
            </div>
            <div class="kk-balance-row">
              <span>Buchungs-Range</span>
              <strong>{{ currentReceiptLabel }}</strong>
            </div>
            <div class="kk-balance-row">
              <span>Abschöpfungen Zeitraum</span>
              <strong class="warning">{{ formatPrice(zbonModalWithdrawalTotalCents) }}</strong>
            </div>
            <div class="kk-balance-row">
              <span>Neuer Barbestand Soll</span>
              <strong>{{ zbonModalCashCalculatedDisplay }}</strong>
            </div>
          </div>

          <!-- Kassenbestand eingeben -->
          <div class="kk-counted-input">
            <label>Gezählter Kassenbestand (€)</label>
            <input
              v-model="zbonCountedCash"
              type="number"
              min="0"
              step="0.01"
              class="form-input large"
              placeholder="0,00"
            >
          </div>

          <!-- Ergebnis -->
          <div class="kk-result-box">
            <div class="kk-result-row">
              <span>Abschöpfung im Modal</span>
              <strong>{{ formatPrice(newWithdrawalsCents) }}</strong>
            </div>
            <div class="kk-result-row">
              <span>Neuer Ist-Bestand</span>
              <strong>{{ zbonNewCashBalanceDisplay }}</strong>
            </div>
            <div
              class="kk-result-row"
              :class="{ error: zbonFinalCashInvalid }"
            >
              <span>Differenz</span>
              <strong>{{ zbonDifferenceDisplay }}</strong>
            </div>
          </div>

          <small
            v-if="zbonFinalCashInvalid"
            class="kk-warning-text"
          >
            Der gezählte Bestand darf nicht kleiner als die im Modal vorgenommene Abschöpfung sein.
          </small>

        </div>

        <div class="kk-dialog__footer">
          <button class="btn btn-secondary" @click="closeZbonCreateModal">Abbrechen</button>
          <button class="btn btn-info"    @click="openCashCounterModal">💰 Kasse zählen</button>
          <button class="btn btn-warning" @click="openWithdrawalModal">💸 Abschöpfung</button>
          <button
            :class="['btn', canCreateZbon ? 'btn-ready' : 'btn-disabled']"
            :disabled="!canCreateZbon"
            @click="requestZBonCreate"
          >
            ✓ Kassenbericht erstellen
          </button>
        </div>

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         ABSCHÖPFUNG
    ════════════════════════════════════════════════════════════ -->
    <div
      v-if="showWithdrawalModal"
      class="confirmation-overlay"
    >
      <div class="kk-dialog kk-dialog--narrow">

        <div class="kk-dialog__header">
          <div>
            <h3>💸 Abschöpfung durchführen</h3>
            <p class="kk-dialog__subtitle">Barbetrag aus der Kasse entnehmen</p>
          </div>
          <button class="kk-dialog__close" @click="closeWithdrawalModal">✕</button>
        </div>

        <div class="kk-dialog__body kk-withdrawal-body">

          <div class="kk-form-group">
            <label>Betrag (€)</label>
            <input
              v-model="withdrawalForm.amount"
              type="number"
              min="0"
              step="0.01"
              class="form-input large"
              placeholder="0,00"
            >
          </div>

          <div class="kk-form-group">
            <label>Durchgeführt von</label>
            <button
              class="kk-select-btn"
              @click="openUserPicker('withdrawalUserId')"
            >
              {{ getSelectedUserName(selectedWithdrawalUserId, 'Benutzer auswählen …') }}
            </button>
          </div>

          <div class="kk-form-group">
            <label>Notiz (optional)</label>
            <input
              v-model="withdrawalForm.note"
              type="text"
              class="form-input"
              placeholder="z. B. Vereinskasse, Bank …"
            >
          </div>

        </div>

        <div class="kk-dialog__footer">
          <button class="btn btn-secondary" @click="closeWithdrawalModal">Abbrechen</button>
          <button class="btn btn-warning"   @click="submitWithdrawal">Abschöpfen</button>
        </div>

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         MEMBER / BENUTZER PICKER
    ════════════════════════════════════════════════════════════ -->
    <div
      v-if="showMemberPickerModal"
      class="confirmation-overlay member-picker-overlay"
    >
      <div class="kk-dialog kk-dialog--narrow">

        <div class="kk-dialog__header">
          <div>
            <h3>{{ pickerTitle }}</h3>
            <p class="kk-dialog__subtitle">{{ pickerSearchPlaceholder }}</p>
          </div>
          <button class="kk-dialog__close" @click="closeMemberPicker">✕</button>
        </div>

        <div class="kk-dialog__body" style="gap: 0.75rem;">

          <input
            v-model="memberSearch"
            type="text"
            :placeholder="pickerSearchPlaceholder"
            class="kk-picker-search"
          >

          <div class="kk-picker-list">
            <button
              v-for="entry in filteredPickerOptions"
              :key="entry.id"
              class="kk-picker-item"
              @click="selectPickerOption(entry)"
            >
              <div
                v-if="entry.photo_path"
                class="kk-picker-photo"
              >
                <img
                  :src="`/api/members/${entry.id}/photo`"
                  :alt="formatPickerLabel(entry)"
                >
              </div>
              <div v-else class="kk-picker-photo placeholder">👤</div>
              <span>{{ formatPickerLabel(entry) }}</span>
            </button>

            <div
              v-if="!filteredPickerOptions.length"
              class="kk-picker-empty"
            >
              Keine Einträge gefunden
            </div>
          </div>

        </div>

        <div class="kk-dialog__footer">
          <button class="btn btn-secondary" @click="closeMemberPicker">Abbrechen</button>
        </div>

      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Z-BON VORSCHAU
    ════════════════════════════════════════════════════════════ -->
    <div
      v-if="showZbonPreviewModal && zBonHtml"
      class="confirmation-overlay"
    >
      <div class="kk-dialog kk-dialog--wide">

        <div class="kk-dialog__header">
          <div>
            <h3>{{ zbonHtmlModalTitle }}</h3>
            <p class="kk-dialog__subtitle">Nur zur Ansicht – Download über den Button unten</p>
          </div>
          <button class="kk-dialog__close" @click="showZbonPreviewModal = false">✕</button>
        </div>

        <div class="kk-dialog__body" style="padding: 1rem;">
          <div class="kk-preview-shell">
            <iframe
              :srcdoc="zBonHtml"
              class="kk-preview-frame"
              title="Kassenbericht-Vorschau"
            />
          </div>
        </div>

        <div class="kk-dialog__footer">
          <button class="btn btn-secondary" @click="showZbonPreviewModal = false">Schließen</button>
          <button class="btn btn-success"   @click="downloadCurrentZbonHtml">⬇️ HTML herunterladen</button>
        </div>

      </div>
    </div>

    <!-- Password Confirm Modal (bleibt unverändert) -->
    <PasswordConfirmModal
      :show="showPasswordModal"
      title="Kassenbericht erstellen"
      message="Bitte Zugangsdaten des aktuell angemeldeten Benutzers bestätigen."
      :username="authStore.user?.username || ''"
      confirm-label="Kassenbericht erstellen"
      @close="showPasswordModal = false"
      @confirm="createZBon"
    />
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
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
const financeHeader = ref(null)
const financeHeaderHeight = ref(0)
let financeHeaderResizeObserver = null
let isWindowResizeListenerAttached = false

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
const zbonHtmlModalTitle = ref('📋 Kassenbericht-Vorschau')
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

// Accordion section open/close state for zbon tab
const accSections = ref({
  einnahmen: true,
  saldo: true,
  offene: false,
  transaktionen: true,
})

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
  zbon: '📊 Kassenbericht',
  zbons: '📑 Kassenberichte',
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

const updateFinanceHeaderHeight = () => {
  financeHeaderHeight.value = financeHeader.value?.offsetHeight || 0
}

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

const toggleAccSection = (key) => {
  accSections.value[key] = !accSections.value[key]
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
    notificationStore.success('Kassenbericht HTML erfolgreich heruntergeladen')
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
    zbonHtmlModalTitle.value = '📋 Kassenbericht-Vorschau'
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
      notificationStore.success('Abschöpfung für den Kassenbericht vorgemerkt')
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
    notificationStore.success('Kassenbericht erfolgreich erstellt')
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
    notificationStore.error('Fehler beim Laden der Kassenberichte: ' + (error.message || 'Unbekannter Fehler'))
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
  const baseName = zbon?.sequence_number ? `Kassenbericht-${zbon.sequence_number}` : 'Kassenbericht-Vorschau'
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
    zbonHtmlModalTitle.value = `📑 Kassenbericht #${zbon.sequence_number}`
    zbonHtmlDownloadMeta.value = zbon
    showZbonPreviewModal.value = true
  } catch (error) {
    console.error('[Finance] Error loading Z-Bon HTML detail:', error)
    notificationStore.error('Fehler beim Laden der Kassenbericht-Ansicht')
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
  nextTick(() => {
    updateFinanceHeaderHeight()
    if (typeof ResizeObserver !== 'undefined' && financeHeader.value) {
      financeHeaderResizeObserver = new ResizeObserver(updateFinanceHeaderHeight)
      financeHeaderResizeObserver.observe(financeHeader.value)
    } else {
      isWindowResizeListenerAttached = true
      window.addEventListener('resize', updateFinanceHeaderHeight)
    }
  })
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

onBeforeUnmount(() => {
  financeHeaderResizeObserver?.disconnect()
  if (isWindowResizeListenerAttached) {
    window.removeEventListener('resize', updateFinanceHeaderHeight)
  }
})
</script>

<style scoped lang="scss">
/* ==================== BASE LAYOUT ==================== */
.admin-finance {
  background: var(--app-background-color);
  border-radius: 8px;
  padding: 0 1rem 0.75rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);

  h3 {
    margin-bottom: 0.75rem;
    color: #555;
  }

  h4 {
    margin: 0.75rem 0 0.5rem 0;
    color: #666;
  }
}

/* ==================== STICKY HEADER ==================== */
.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--app-background-color);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0 -1rem 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.13);
}

.sticky-header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--app-background-color);
  padding: 0.75rem 1rem;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;

  h2 {
    margin: 0;
    color: #333;
    font-size: 1.25rem;
  }
}

.title-sep {
  color: #aaa;
  font-weight: 300;
}

.page-subtitle {
  color: #556;
  font-size: 0.82rem;
  margin: 0;
}

/* ==================== TABS ==================== */
.finance-tabs {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 0.5rem 0.9rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  color: #94a3b8;
  transition: all 0.2s;

  &:hover {
    background: color-mix(in srgb, var(--app-banner-color) 14%, white);
    border-color: color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
    color: #334155;
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

/* ==================== ACTION BAR ==================== */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  padding: 0.85rem 1.1rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-top: 0.75rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.period-info {
  font-size: 0.95rem;
  color: #475569;
}

.receipt-info {
  color: #64748b;
  margin-left: 0.5rem;
}

.action-buttons {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

/* ==================== TAB CONTENT ==================== */
.tab-content {
  animation: fadeIn 0.2s;
}

.compact-content .zbon-section {
  padding: 1.1rem 1.25rem;
  margin-bottom: 1.25rem;
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

/* ==================== Z-BON LAYOUT ==================== */
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

/* ==================== SUMMARY CARDS ==================== */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.9rem;
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

  &.total {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    transform: scale(1.02);
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

/* ==================== TABLES ==================== */
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
        background: color-mix(in srgb, var(--app-background-color) 60%, white);
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

/* ==================== PAYMENT BADGES ==================== */
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

/* ==================== FILTER SECTION ==================== */
.filter-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: color-mix(in srgb, var(--app-background-color) 80%, white);
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

/* ==================== BUTTONS ==================== */
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

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover {
    background: #e2e8f0;
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

.btn-subtle {
  background: transparent;
  color: #64748b;
  border: 1px solid #cbd5e1;

  &:hover {
    background: #f1f5f9;
  }
}

/* ==================== FORM ELEMENTS ==================== */
.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;

  &.large {
    font-size: 1.35rem;
    padding: 0.9rem 1rem;
    font-weight: 600;
  }
}

.select-btn {
  width: 100%;
  padding: 0.85rem 1rem;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-weight: 600;
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

/* ==================== SCHEDULER ==================== */
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

/* ==================== HISTORY / REVENUE / MEMBERS ==================== */
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

/* ==================== INTERNAL ACCOUNTS ==================== */
.internal-account-sections {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.internal-account-section {
  margin: 0;
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

/* ============================================================
   KONSOLIDIERTE MODAL-STILE – Finance.vue
   Ersetzt den bisherigen Abschnitt "MODALS" vollständig.
   Alle vier Dialoge teilen denselben Shell (.kk-dialog).
   Zielgröße: 80 % Bildschirm auf 19" (≈ 1280–1440 px).
   ============================================================ */

/* ---------- Overlay (gemeinsam) ---------- */
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  overflow-y: auto;
}

.member-picker-overlay {
  z-index: 1600;
}

/* ---------- Gemeinsame Dialog-Shell ---------- */
.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(80vw, 1100px);
  max-height: min(82vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

/* Schmalere Dialoge (Abschöpfung, Member Picker) */
.kk-dialog--narrow {
  width: min(80vw, 560px);
}

/* Preview-Dialog darf breiter sein */
.kk-dialog--wide {
  width: min(90vw, 1400px);
  max-height: min(88vh, 960px);
}

/* ---------- Header (gemeinsam) ---------- */
.kk-dialog__header {
  padding: 1rem 1.4rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-shrink: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.3;
  }
}

.kk-dialog__subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.82rem;
}

.kk-dialog__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: background 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.28);
  }
}

/* ---------- Body (gemeinsam) ---------- */
.kk-dialog__body {
  padding: 1.4rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

/* ---------- Footer (gemeinsam) ---------- */
.kk-dialog__footer {
  padding: 1rem 1.4rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  flex-shrink: 0;
  background: #f8fafc;
  flex-wrap: wrap;
}

/* ============================================================
   Z-BON ERSTELLEN – spezifische Inhaltsblöcke
   ============================================================ */

/* Info-Box (blauer Hinweis oben) */
.kk-info-box {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  line-height: 1.5;
}

/* Zwei-Spalten-Formular */
.kk-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.kk-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  text-align: left;

  label {
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

.kk-select-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
}

.kk-clear-btn {
  padding: 0.75rem 0.85rem;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: #f1f5f9;
    color: #64748b;
  }
}

.kk-selection-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

/* Saldo-Übersicht (graue Box) */
.kk-balance-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.kk-balance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 1rem;
  font-size: 0.88rem;
  border-bottom: 1px solid #f1f5f9;
  color: #475569;

  &:last-child {
    border-bottom: none;
  }

  strong {
    color: #1e293b;
    font-weight: 700;

    &.warning {
      color: #b45309;
    }
  }
}

/* Gezählter Kassenbestand */
.kk-counted-input {
  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
  }

  .form-input.large {
    font-size: 1.5rem;
    padding: 0.85rem 1.1rem;
    font-weight: 700;
    width: 100%;
    border-radius: 10px;
    border: 1.5px solid #cbd5e1;
    transition: border-color 0.15s;

    &:focus {
      outline: none;
      border-color: #0f766e;
    }
  }
}

/* Ergebnis-Box (grün/rot je nach Differenz) */
.kk-result-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  overflow: hidden;
}

.kk-result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 1rem;
  font-size: 0.9rem;
  border-bottom: 1px solid #dcfce7;
  color: #166534;

  &:last-child {
    border-bottom: none;
  }

  strong {
    font-weight: 700;
  }

  &.error {
    background: #fff1f2;
    color: #b91c1c;

    strong {
      color: #b91c1c;
    }
  }
}

.kk-warning-text {
  display: block;
  color: #b91c1c;
  font-size: 0.82rem;
  font-weight: 600;
  margin-top: -0.5rem;
}

/* ============================================================
   ABSCHÖPFUNG – spezifische Inhaltsblöcke
   ============================================================ */

.kk-withdrawal-body {
  gap: 0.85rem;
}

/* ============================================================
   MEMBER PICKER
   ============================================================ */

.kk-picker-search {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  background: #f8fafc;
  transition: border-color 0.15s;

  &:focus {
    outline: none;
    border-color: #0f766e;
    background: #fff;
  }
}

.kk-picker-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-height: 200px;
  max-height: 400px;
}

.kk-picker-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
}

.kk-picker-photo {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  background: #e2e8f0;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    color: #94a3b8;
    font-size: 1rem;
  }
}

.kk-picker-empty {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  font-style: italic;
  font-size: 0.9rem;
}

/* ============================================================
   Z-BON PREVIEW
   ============================================================ */

.kk-preview-shell {
  flex: 1;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.kk-preview-frame {
  width: 100%;
  flex: 1;
  border: none;
  display: block;
  min-height: 500px;
}

/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 900px) {
  .kk-dialog {
    width: min(94vw, 1100px);
    max-height: min(90vh, 900px);
    border-radius: 16px;
  }

  .kk-dialog--wide {
    width: 96vw;
  }
}

@media (max-width: 640px) {
  .confirmation-overlay {
    padding: 0.75rem;
    align-items: flex-start;
  }

  .kk-dialog {
    width: 100%;
    max-height: calc(100dvh - 1.5rem);
    border-radius: 14px;
  }

  .kk-dialog__footer {
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>

/* ==================== PAGINATION ==================== */
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

/* ==================== TABLE CONTAINER ==================== */
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

/* ==================== EMPTY / LOADING ==================== */
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

/* ==================== RESPONSIVE ==================== */
@media (max-width: 900px) {
  .zbon-create-layout {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .selection-actions {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 700px) {
  .admin-finance {
    padding: 0 1rem 1rem;
  }

  .page-header {
    margin: 0 -1rem 1rem;
    padding: 1rem;
  }

  .sticky-header {
    padding: 1rem;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    justify-content: stretch;

    .btn {
      flex: 1;
    }
  }

  .modal-actions {
    flex-direction: column;

    .btn {
      width: 100%;
    }
  }
}

/* ==================== SUMMARY STRIP ==================== */
.summary-strip {
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin-bottom: 0.75rem;
  overflow: hidden;
}

.ss-item {
  padding: 0.7rem 0.85rem;
  border-right: 1px solid #e2e8f0;
  text-align: center;

  &:last-child {
    border-right: none;
  }
}

.ss-total-item {
  background: #eff6ff;
}

.ss-icon {
  font-size: 1.1rem;
  margin-bottom: 0.15rem;
}

.ss-label {
  font-size: 0.68rem;
  color: #94a3b8;
  font-weight: 500;
  display: block;
}

.ss-value {
  font-size: 0.95rem;
  font-weight: 800;
  display: block;

  &.ss-green {
    color: #059669;
  }

  &.ss-blue {
    color: #2563eb;
  }

  &.ss-orange {
    color: #b45309;
  }

  &.ss-total {
    color: #1d4ed8;
    font-size: 1.05rem;
  }
}

@media (max-width: 700px) {
  .summary-strip {
    grid-template-columns: repeat(2, 1fr);

    .ss-item {
      border-right: 1px solid #e2e8f0;
      border-bottom: 1px solid #e2e8f0;

      &:nth-child(even) {
        border-right: none;
      }

      &:last-child {
        grid-column: 1 / -1;
        border-bottom: none;
      }
    }
  }
}

/* ==================== ACCORDION ==================== */
.accordion {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.acc-section {
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.acc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 1rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
  gap: 0.5rem;

  &:hover {
    background: #f8fafc;
  }
}

.acc-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.acc-icon {
  font-size: 1rem;
}

.acc-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #1e293b;
}

.acc-summary {
  font-size: 0.78rem;
  color: #64748b;
  margin-left: auto;
  margin-right: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.acc-chevron {
  font-size: 0.75rem;
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.2s;

  &::before {
    content: '▼';
  }

  &.open {
    transform: rotate(180deg);
  }
}

.acc-body {
  border-top: 1px solid #e2e8f0;
}

.acc-stat-rows {
  padding: 0.2rem 0;
}

.acc-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.45rem 1rem;
  border-bottom: 1px solid #f8fafc;
  font-size: 0.85rem;

  &:last-child {
    border-bottom: none;
  }
}

.acc-total-row {
  background: #eff6ff;

  .acc-row-label {
    font-weight: 700;
    color: #1e293b;
  }
}

.acc-row-label {
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.acc-row-value {
  font-weight: 700;

  &.green {
    color: #059669;
  }

  &.blue {
    color: #2563eb;
  }

  &.orange {
    color: #b45309;
  }

  &.red {
    color: #dc2626;
  }

  &.big {
    color: #1d4ed8;
    font-size: 0.95rem;
  }
}

/* ==================== CALC TABLE (Kassensaldo) ==================== */
.calc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;

  td {
    padding: 0.45rem 1rem;
    border-bottom: 1px solid #f8fafc;
  }

  tr:last-child td {
    border-bottom: none;
  }
}

.calc-op {
  color: #64748b;
}

.calc-right {
  text-align: right;
  font-weight: 600;
}

.calc-plus {
  color: #059669;
}

.calc-minus {
  color: #dc2626;
}

.calc-total-row {
  background: #eff6ff;

  td {
    color: #1d4ed8;
  }
}
</style>
