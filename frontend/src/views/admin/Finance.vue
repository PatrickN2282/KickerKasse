<template>
  <div class="admin-finance">
    <h2>Finanzstatistik</h2>

    <div class="finance-tabs">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :class="{ active: activeTab === tab }"
        class="tab-btn"
      >
        {{ tabLabels[tab] }}
      </button>
    </div>

    <!-- Z-BON / Tagesabrechnung -->
    <div v-if="activeTab === 'zbon'" class="tab-content">
      <h3>Z-Bon</h3>

      <div class="date-picker">
        <div>
          <strong>Aktueller Zeitraum:</strong>
          {{ currentPeriodLabel }}
        </div>
        <div>
          <strong>Letzter Belegbereich:</strong>
          {{ currentReceiptLabel }}
        </div>
      </div>

      <div v-if="loading" class="loading">Läuft...</div>
        <div v-else class="zbon-summary">
          <div class="summary-grid">
          <div class="summary-card">
            <div class="card-label">Umsatz (BAR)</div>
            <div class="card-value">{{ formatPrice(dailyStats.cash_total) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Umsatz (Guthaben)</div>
            <div class="card-value">{{ formatPrice(dailyStats.balance_total) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Gutscheine</div>
            <div class="card-value">{{ formatPrice(dailyStats.voucher_total) }}</div>
          </div>
          <div class="summary-card highlight">
            <div class="card-label">Umsatz GESAMT</div>
            <div class="card-value">{{ formatPrice(dailyStats.total_amount) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Soll-Bestand Kasse</div>
            <div class="card-value">{{ formatEuroValue(dailyStats.cash_calculated) }}</div>
          </div>
          <div class="summary-card warning">
            <div class="card-label">Abschöpfungen</div>
            <div class="card-value">{{ formatPrice(dailyStats.withdrawal_total) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Offene Gutscheine</div>
            <div class="card-value">{{ formatEuroValue(dailyStats.voucher_open_total) }}</div>
          </div>
            <div class="summary-card">
              <div class="card-label">Anzahl Transaktionen</div>
              <div class="card-value">{{ dailyStats.transaction_count }}</div>
            </div>
          </div>

          <div class="zbon-actions">
            <button @click="loadDailyStats" class="btn btn-primary">
              👁️ Z-Bon Vorschau
            </button>
            <button @click="handleDownloadZBon" class="btn btn-success">
              ⬇️ Als HTML herunterladen
            </button>
            <button @click="openZbonCreateModal" class="btn btn-info">
              ✅ Z-Bon erstellen
            </button>
            <button @click="openWithdrawalModal" class="btn btn-warning">
              💸 Abschöpfung
            </button>
            <button @click="openCashCounterModal" class="btn btn-secondary">
              💰 Kasse zählen
            </button>
          </div>

          <div class="daily-transactions">
            <h4>Transaktionen seit dem letzten Z-Bon</h4>
          <div v-if="dailyStats.transactions.length === 0" class="empty">
            Keine Transaktionen im aktuellen Z-Bon-Zeitraum
          </div>
          <table v-else class="transactions-table">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Belegnummer</th>
                <th>Mitglied</th>
                <th>Betrag</th>
                <th>Zahlungsart</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="transaction in dailyStats.transactions" :key="transaction.id">
                <tr class="transaction-row" @click="toggleTransaction(transaction.id)" style="cursor: pointer;">
                  <td>{{ formatTime(transaction.created_at) }}</td>
                  <td><strong>{{ transaction.receipt_number }}</strong></td>
                  <td>{{ transaction.member?.name || transaction.member_name || 'Gast' }}</td>
                  <td class="amount">{{ formatPrice(transaction.gross_amount_cents || transaction.total_amount_cents) }}</td>
                  <td>
                    <span v-if="transaction.type === 'RECHARGE'" class="payment-badge recharge">
                      ⬆️ Aufladen
                    </span>
                    <span v-else :class="['payment-badge', getPaymentBadgeClass(transaction)]">
                      {{ getPaymentBadgeLabel(transaction) }}
                    </span>
                  </td>
                </tr>
                <tr v-if="expandedTransactions.has(transaction.id)" class="items-row">
                  <td colspan="5" class="items-cell">
                    <div class="items-list">
                      <div v-if="transaction.items && transaction.items.length > 0">
                        <div v-for="item in transaction.items" :key="item.id" class="item-detail">
                          <span class="item-name">{{ item.product?.name || item.id }}: </span>
                          <span class="item-qty">{{ item.quantity }}×</span>
                          <span class="item-price">{{ formatPrice(item.unit_price_cents) }}</span>
                          <span class="item-total">= {{ formatPrice(item.total_price_cents) }}</span>
                        </div>
                      </div>
                      <div v-else class="no-items">
                        Keine Artikel
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
            </table>
          </div>

          <!-- Z-Bon HTML Preview -->
        <div v-if="zBonHtml" class="zbon-preview" style="margin-top: 2rem; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; background: #f9f9f9;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0;">📋 Z-Bon Vorschau</h4>
            <button @click="zBonHtml = ''" style="background: none; border: 1px solid #999; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">
              ✕ Schließen
            </button>
          </div>
          <div class="zbon-preview-frame-shell">
            <iframe :srcdoc="zBonHtml" class="zbon-preview-frame" title="Z-Bon Vorschau"></iframe>
          </div>
          <div style="margin-top: 1rem; text-align: center;">
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">
              💡 Tipp: Mit Ctrl+P oder Cmd+P zum Drucken / Als PDF speichern
            </p>
          </div>
        </div>

        <div class="scheduler-section">
          <h4>⏱️ Automatischer Email-Versand</h4>
          <div class="scheduler-status">
            <div class="status-item">
              <span>Status:</span>
              <span v-if="schedulerStatus.running" class="status-badge running">
                ● Läuft
              </span>
              <span v-else class="status-badge stopped">
                ● Gestoppt
              </span>
            </div>
            <div v-if="schedulerStatus.next_run" class="status-item">
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
        </div>
      </div>
    </div>

    <!-- Z-BÖNS VERLAUF -->
    <div v-if="activeTab === 'zbons'" class="tab-content">
      <h3>📑 Z-Bons Verlauf</h3>

      <div class="filter-section">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input v-model="zbonsFilterStartDate" type="date" class="form-input" />
        </div>
        <div class="filter-group">
          <label>Bis Datum:</label>
          <input v-model="zbonsFilterEndDate" type="date" class="form-input" />
        </div>
        <button @click="loadZbonsHistory" class="btn btn-primary">
          🔍 Filtern
        </button>
      </div>

      <div v-if="loadingZbons" class="loading">Läuft...</div>
      <div v-else>
        <!-- Summary Cards -->
        <div class="summary-grid" style="margin-bottom: 1.5rem;">
          <div class="summary-card">
            <div class="card-label">Anzahl Z-Böns</div>
            <div class="card-value">{{ zbonsList.length }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Gesamt Umsatz (BAR)</div>
            <div class="card-value">{{ formatPrice(zbonsTotalCash) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Gesamt Umsatz (Guthaben)</div>
            <div class="card-value">{{ formatPrice(zbonsTotalBalance) }}</div>
          </div>
          <div class="summary-card highlight">
            <div class="card-label">Gesamt Umsatz</div>
            <div class="card-value">{{ formatPrice(zbonsTotalRevenue) }}</div>
          </div>
        </div>

        <!-- Z-Böns Table -->
        <div class="table-container">
          <table v-if="zbonsList.length > 0" class="transactions-table">
            <thead>
              <tr>
                <th>Seq#</th>
                <th>Datum</th>
                <th>Umsatz BAR</th>
                <th>Umsatz Guthaben</th>
                <th>Kasse Anfang</th>
                <th>Kasse Ende</th>
                <th>Entnahmen</th>
                <th>Erstellt</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="zbon in zbonsList" 
                :key="zbon.id"
                class="transaction-row"
                style="cursor: pointer;"
                @click="selectZbon(zbon)"
              >
                <td><strong>#{{ zbon.sequence_number }}</strong></td>
                <td>{{ formatDate(zbon.business_date) }}</td>
                <td class="amount">{{ formatPrice(zbon.gross_revenue_cash * 100) }}</td>
                <td class="amount">{{ formatPrice(zbon.gross_revenue_balance * 100) }}</td>
                <td class="amount">{{ formatPrice(zbon.cash_opening_balance * 100) }}</td>
                <td class="amount">{{ formatPrice((zbon.cash_calculated || 0) * 100) }}</td>
                <td class="amount withdrawal">{{ formatPrice(zbon.cash_withdrawals * 100) }}</td>
                <td class="date">{{ formatTime(zbon.generated_at) }}</td>
              </tr>
            </tbody>
          </table>

          <div v-else class="empty">
            Keine Z-Böns für den ausgewählten Zeitraum
          </div>
        </div>

        <!-- Z-Bon Detail View -->
        <div v-if="selectedZbon" class="zbon-detail" style="margin-top: 2rem; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; background: #f9f9f9;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h4 style="margin: 0;">📑 Z-Bon #{{ selectedZbon.sequence_number }} - Detailansicht</h4>
            <button @click="selectedZbon = null" style="background: none; border: 1px solid #999; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">
              ✕ Schließen
            </button>
          </div>

          <table class="detail-table">
            <tr>
              <td>Sequenznummer:</td>
              <td><strong>{{ selectedZbon.sequence_number }}</strong></td>
            </tr>
            <tr>
              <td>Geschäftstag:</td>
              <td>{{ formatDateDE(selectedZbon.business_date) }}</td>
            </tr>
            <tr>
              <td>Zeitraum:</td>
              <td>{{ formatTime(selectedZbon.period_start) }} - {{ formatTime(selectedZbon.period_end) }}</td>
            </tr>
            <tr>
              <td>Erstellt:</td>
              <td>{{ formatDate(selectedZbon.generated_at) }}, {{ formatTime(selectedZbon.generated_at) }}</td>
            </tr>
            <tr>
              <td>Mitarbeiter:</td>
              <td>{{ selectedZbon.created_by_name || '-' }}</td>
            </tr>
            <tr>
              <td>Sichtkontrolle:</td>
              <td>{{ selectedZbon.cash_counted_by_name || '-' }}</td>
            </tr>
            <tr class="section-row">
              <td colspan="2" style="text-align: center; font-weight: bold; padding-top: 1rem;">UMSÄTZE</td>
            </tr>
            <tr>
              <td>Umsatz BAR:</td>
              <td class="currency">{{ formatPrice(selectedZbon.gross_revenue_cash * 100) }}</td>
            </tr>
            <tr>
              <td>Umsatz Guthaben:</td>
              <td class="currency">{{ formatPrice(selectedZbon.gross_revenue_balance * 100) }}</td>
            </tr>
            <tr>
              <td>Umsatz Gutscheine:</td>
              <td class="currency">{{ formatPrice(selectedZbon.gross_revenue_voucher * 100) }}</td>
            </tr>
            <tr>
              <td>Gesamtumsatz brutto:</td>
              <td class="currency">{{ formatPrice(selectedZbon.total_revenue * 100) }}</td>
            </tr>
            <tr>
              <td>Guthabenaufladungen:</td>
              <td class="currency">{{ formatPrice(selectedZbon.recharge_total * 100) }}</td>
            </tr>
            <tr>
              <td>Stornierungen:</td>
              <td class="currency">{{ formatPrice(selectedZbon.storno_total * 100) }}</td>
            </tr>
            <tr>
              <td>Gutscheine erstellt:</td>
              <td class="currency">{{ selectedZbon.voucher_created_count }} / {{ formatPrice(selectedZbon.voucher_created_total * 100) }}</td>
            </tr>
            <tr>
              <td>Gutscheine eingelöst:</td>
              <td class="currency">{{ selectedZbon.voucher_redeemed_count }} / {{ formatPrice(selectedZbon.voucher_redeemed_total * 100) }}</td>
            </tr>
            <tr>
              <td>Offene Gutscheine:</td>
              <td class="currency">{{ selectedZbon.voucher_open_count }} / {{ formatPrice(selectedZbon.voucher_open_total * 100) }}</td>
            </tr>
            <tr class="section-row">
              <td colspan="2" style="text-align: center; font-weight: bold; padding-top: 1rem;">KASSENBESTAND</td>
            </tr>
            <tr>
              <td>Anfangsbestand:</td>
              <td class="currency">{{ formatPrice(selectedZbon.cash_opening_balance * 100) }}</td>
            </tr>
            <tr>
              <td>Calculated:</td>
              <td class="currency">{{ formatPrice((selectedZbon.cash_calculated || 0) * 100) }}</td>
            </tr>
            <tr>
              <td>Gezählt:</td>
              <td class="currency">{{ formatPrice((selectedZbon.cash_counted || 0) * 100) }}</td>
            </tr>
            <tr v-if="selectedZbon.cash_difference !== null">
              <td>Differenz:</td>
              <td :class="['currency', selectedZbon.cash_difference >= 0 ? 'positive' : 'negative']">
                {{ formatPrice(selectedZbon.cash_difference * 100) }}
              </td>
            </tr>
            <tr class="section-row">
              <td colspan="2" style="text-align: center; font-weight: bold; padding-top: 1rem;">BEWEGUNGEN</td>
            </tr>
            <tr>
              <td>Abschöpfung:</td>
              <td class="currency withdrawal">{{ formatPrice(selectedZbon.cash_withdrawals * 100) }}</td>
            </tr>
            <tr>
              <td>Einlagen:</td>
              <td class="currency deposit">{{ formatPrice(selectedZbon.cash_deposits * 100) }}</td>
            </tr>
            <tr class="section-row">
              <td colspan="2" style="text-align: center; font-weight: bold; padding-top: 1rem;">TRANSAKTIONEN</td>
            </tr>
            <tr>
              <td>Transaktionen gesamt:</td>
              <td>{{ selectedZbon.transaction_count_total }}</td>
            </tr>
            <tr>
              <td>Verkäufe:</td>
              <td>{{ selectedZbon.transaction_count_sales }}</td>
            </tr>
            <tr>
              <td>Aufladungen:</td>
              <td>{{ selectedZbon.transaction_count_recharge }}</td>
            </tr>
            <tr>
              <td>Stornierungen:</td>
              <td>{{ selectedZbon.transaction_count_storno }}</td>
            </tr>
            <tr>
              <td>Belegnummern:</td>
              <td>#{{ selectedZbon.receipt_number_min }} - #{{ selectedZbon.receipt_number_max }}</td>
            </tr>
          </table>

          <div style="margin-top: 1.5rem; display: flex; gap: 1rem;">
            <button @click="downloadZbonHTML(selectedZbon)" class="btn btn-success">
              ⬇️ Als HTML herunterladen
            </button>
            <button @click="downloadZbonPDF(selectedZbon)" class="btn btn-info">
              📄 Als PDF herunterladen
            </button>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="zbonsTotalPages > 1" class="pagination" style="margin-top: 2rem;">
          <button @click="zbonsCurrentPage--" :disabled="zbonsCurrentPage === 1" class="btn btn-secondary">
            ◀ Zurück
          </button>
          <span>Seite {{ zbonsCurrentPage }} von {{ zbonsTotalPages }}</span>
          <button @click="zbonsCurrentPage++" :disabled="zbonsCurrentPage === zbonsTotalPages" class="btn btn-secondary">
            Weiter ▶
          </button>
        </div>
      </div>
    </div>
    <div v-if="activeTab === 'history'" class="tab-content">
      <h3>Transaktionshistorie</h3>

      <div class="filter-section">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input v-model="filterStartDate" type="date" class="form-input" />
        </div>
        <div class="filter-group">
          <label>Bis Datum:</label>
          <input v-model="filterEndDate" type="date" class="form-input" />
        </div>
        <div class="filter-group">
          <label>Zahlungsart:</label>
          <select v-model="filterPaymentMethod" class="form-input">
            <option value="">Alle</option>
            <option value="CASH">BAR</option>
            <option value="BALANCE">Guthaben</option>
            <option value="VOUCHER_GIFT">Geschenk-Gutschein</option>
            <option value="VOUCHER_PREPAID">Guthaben-Gutschein</option>
          </select>
        </div>
        <button @click="applyFilters" class="btn btn-info">Filter anwenden</button>
      </div>

      <div v-if="loadingHistory" class="loading">Läuft...</div>
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

        <table v-if="filteredTransactions.length > 0" class="transactions-table">
          <thead>
            <tr>
              <th>Datum</th>
              <th>Zeit</th>
              <th>Belegnummer</th>
              <th>Mitglied</th>
              <th>Betrag</th>
              <th>Zahlungsart</th>
              <th>Benutzer</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td>{{ formatDate(transaction.created_at) }}</td>
              <td>{{ formatTime(transaction.created_at) }}</td>
              <td><strong>{{ transaction.receipt_number }}</strong></td>
              <td>{{ transaction.member?.name || 'Gast' }}</td>
              <td class="amount">{{ formatPrice(transaction.total_amount_cents) }}</td>
              <td>
                <span v-if="transaction.type === 'RECHARGE'" class="payment-badge recharge">
                  ⬆️ Aufladen
                </span>
                <span v-else :class="['payment-badge', getPaymentBadgeClass(transaction)]">
                  {{ getPaymentBadgeLabel(transaction) }}
                </span>
              </td>
              <td>{{ transaction.user?.username || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">
          Keine Transaktionen im ausgewählten Zeitraum
        </div>
      </div>
    </div>

    <!-- Umsatzstatistik -->
    <div v-if="activeTab === 'revenue'" class="tab-content">
      <h3>Umsatzstatistik</h3>

      <div class="revenue-overview">
        <div class="revenue-card">
          <div class="card-label">Umsatz diese Woche</div>
          <div class="card-value">{{ formatPrice(revenueStats.week_total) }}</div>
        </div>
        <div class="revenue-card">
          <div class="card-label">Umsatz diesen Monat</div>
          <div class="card-value">{{ formatPrice(revenueStats.month_total) }}</div>
        </div>
        <div class="revenue-card">
          <div class="card-label">Durchschnitt pro Tag</div>
          <div class="card-value">{{ formatPrice(revenueStats.daily_average) }}</div>
        </div>
        <div class="revenue-card warning">
          <div class="card-label">Abschöpfungen diese Woche</div>
          <div class="card-value">{{ formatPrice(revenueStats.week_withdrawals) }}</div>
        </div>
      </div>

      <div class="payment-stats">
        <h4>Nach Zahlungsart</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">💰 Bargeld</div>
            <div class="stat-value">{{ formatPrice(revenueStats.cash_total) }}</div>
            <div class="stat-percent">{{ revenueStats.cash_percent }}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">💳 Guthaben</div>
            <div class="stat-value">{{ formatPrice(revenueStats.balance_total) }}</div>
            <div class="stat-percent">{{ revenueStats.balance_percent }}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">💸 Abschöpfungen 30 Tage</div>
            <div class="stat-value">{{ formatPrice(revenueStats.month_withdrawals) }}</div>
          </div>
        </div>
      </div>

      <div class="top-products">
        <h4>Top Produkte (diese Woche)</h4>
        <table v-if="revenueStats.top_products.length > 0" class="products-table">
          <thead>
            <tr>
              <th>Produkt</th>
              <th>Menge</th>
              <th>Umsatz</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in revenueStats.top_products" :key="product.id">
              <td>{{ product.name }}</td>
              <td>{{ product.quantity_sold }}</td>
              <td>{{ formatPrice(product.total_revenue) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Member-Statistik -->
    <div v-if="activeTab === 'members'" class="tab-content">
      <h3>Mitglied-Statistik</h3>

      <div class="member-stats-overview">
        <div class="stat-card">
          <div class="stat-label">Gesamte Mitglieder</div>
          <div class="stat-value">{{ memberStats.total_members }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Aktiv diese Woche</div>
          <div class="stat-value">{{ memberStats.active_this_week }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Gesamtes Guthaben</div>
          <div class="stat-value">{{ formatPrice(memberStats.total_balance) }}</div>
        </div>
      </div>

      <h4>Top Mitglieder (nach Ausgaben)</h4>
      <table v-if="memberStats.top_members.length > 0" class="members-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Transaktionen</th>
            <th>Ausgegeben</th>
            <th>Guthaben</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in memberStats.top_members" :key="member.id">
            <td>{{ member.name }}</td>
            <td>{{ member.transaction_count }}</td>
            <td>{{ formatPrice(member.total_spent) }}</td>
            <td>{{ formatPrice(member.balance_cents) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Cash Counter Modal -->
    <CashCounterModal
      :show="showCashCounterModal"
      @close="showCashCounterModal = false"
      @confirm="onCashCounterConfirm"
    />

    <div v-if="showZbonCreateModal" class="confirmation-overlay">
      <div class="confirmation-dialog">
        <h3>Z-Bon erstellen</h3>
        <div class="selection-group">
          <label>Mitarbeiter</label>
          <button @click="openMemberPicker('employeeMemberId')" class="member-select-btn">
            {{ getSelectedMemberName(zbonForm.employeeMemberId, 'Mitglied auswählen') }}
          </button>
        </div>
        <div class="selection-group">
          <label>Sichtkontrolle</label>
          <button @click="openMemberPicker('checkerMemberId')" class="member-select-btn">
            {{ getSelectedMemberName(zbonForm.checkerMemberId, 'Mitglied auswählen') }}
          </button>
        </div>
        <p v-if="cashCountData" class="cash-count-hint">
          Gezählter Barbestand: <strong>{{ formatEuroValue(getCashCountTotal(cashCountData)) }}</strong>
        </p>
        <div class="filter-group">
          <label>Passwort bestätigen</label>
          <input
            v-model="zbonForm.authPassword"
            type="password"
            class="form-input"
            placeholder="Passwort des angemeldeten Benutzers"
          />
        </div>
        <div class="confirmation-buttons">
          <button @click="closeZbonCreateModal" class="btn btn-secondary">
            Abbrechen
          </button>
          <button @click="openCashCounterModal" class="btn btn-secondary">
            💰 Kasse zählen
          </button>
          <button @click="createZBon" class="btn btn-primary" :disabled="!zbonForm.authPassword">
            ✓ Erstellen
          </button>
        </div>
      </div>
    </div>

    <div v-if="showWithdrawalModal" class="confirmation-overlay">
      <div class="confirmation-dialog">
        <h3>Abschöpfung</h3>
        <div class="filter-group">
          <label>Betrag in EUR</label>
          <input v-model="withdrawalForm.amount" type="number" min="0" step="0.01" class="form-input" />
        </div>
        <div class="selection-group">
          <label>Durchgeführt von</label>
          <button @click="openMemberPicker('withdrawalMemberId')" class="member-select-btn">
            {{ getSelectedMemberName(selectedWithdrawalMemberId, 'Mitglied auswählen') }}
          </button>
        </div>
        <div class="filter-group">
          <label>Notiz (optional)</label>
          <input v-model="withdrawalForm.note" type="text" class="form-input" placeholder="z. B. Vereinskasse" />
        </div>
        <div class="confirmation-buttons">
          <button @click="closeWithdrawalModal" class="btn btn-secondary">
            Abbrechen
          </button>
          <button @click="submitWithdrawal" class="btn btn-warning">
            💸 Abschöpfen
          </button>
        </div>
      </div>
    </div>

    <div v-if="showMemberPickerModal" class="confirmation-overlay member-picker-overlay">
      <div class="confirmation-dialog member-picker-dialog">
        <h3>Mitglied auswählen</h3>
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name suchen..."
          class="form-input member-search-input"
        />
        <div class="member-picker-list">
          <button
            v-for="member in filteredPickerMembers"
            :key="member.id"
            @click="selectMemberForTarget(member)"
            class="member-picker-item"
          >
            <div v-if="member.photo_path" class="member-picker-photo">
              <img :src="`/api/members/${member.id}/photo`" :alt="member.name" />
            </div>
            <div v-else class="member-picker-photo placeholder">👤</div>
            <span>{{ member.name }}</span>
          </button>
          <div v-if="!filteredPickerMembers.length" class="empty member-picker-empty">
            Keine Mitglieder gefunden
          </div>
        </div>
        <div class="confirmation-buttons">
          <button @click="closeMemberPicker" class="btn btn-secondary">
            Abbrechen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { formatPrice } from '@/services/utils'
import apiService from '@/services/api'
import CashCounterModal from '@/components/CashCounterModal.vue'
import { useNotificationStore } from '@/stores/notification'
import { useMemberStore } from '@/stores/member'

const notificationStore = useNotificationStore()
const memberStore = useMemberStore()

const activeTab = ref('zbon')
const loading = ref(false)
const loadingHistory = ref(false)

// Cash counter modal state
const showCashCounterModal = ref(false)
const cashCountData = ref(null)
const reportType = ref('zbon') // 'zbon' or 'daily-report'
// Filters
const filterStartDate = ref(getDateDaysAgo(30))
const filterEndDate = ref(new Date().toISOString().split('T')[0])
const filterPaymentMethod = ref('')

const showZbonCreateModal = ref(false)
const showWithdrawalModal = ref(false)
const showMemberPickerModal = ref(false)
const memberPickerTarget = ref(null)
const memberSearch = ref('')
const zbonForm = ref({
  employeeMemberId: null,
  checkerMemberId: null,
  authPassword: '',
})
const withdrawalForm = ref({
  amount: '',
  memberId: null,
  note: '',
})
// Expanded transactions state
const expandedTransactions = ref(new Set())

// Z-Bon HTML preview
const zBonHtml = ref('')

// Z-Böns History
const zbonsList = ref([])
const selectedZbon = ref(null)
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
  total_amount: 0,
  transaction_count: 0,
  cash_calculated: 0,
  withdrawal_total: 0,
  voucher_open_total: 0,
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

const tabs = ['zbon', 'zbons', 'history', 'revenue', 'members']
const tabLabels = {
  zbon: '📊 Z-Bon',
  zbons: '📑 Z-Bons Verlauf',
  history: '📜 Transaktionen',
  revenue: '📈 Umsatz',
  members: '👥 Mitglieder',
}

// Scheduler configuration
const schedulerStatus = ref({
  enabled: false,
  running: false,
  scheduled_time: '23:59',
})
const schedulerEnabled = ref(false)
const schedulerTime = ref('23:59')
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
function formatDateDE(dateStr) {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('de-DE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
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

function getCashCountTotal(cashCount) {
  if (!cashCount) return 0
  if (cashCount.total !== undefined && cashCount.total !== null) {
    return cashCount.total
  }

  const coinTotal = Object.entries(cashCount.coins || {}).reduce(
    (sum, [denomination, count]) => sum + (parseFloat(denomination) * count),
    0,
  )
  const noteTotal = Object.entries(cashCount.notes || {}).reduce(
    (sum, [denomination, count]) => sum + (parseFloat(denomination) * count),
    0,
  )

  return coinTotal + noteTotal
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

const filteredPickerMembers = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()
  if (!search) {
    return memberStore.members
  }

  return memberStore.members.filter(member => member.name.toLowerCase().includes(search))
})

const selectedWithdrawalMemberId = computed(() => withdrawalForm.value.memberId)

const getMemberById = (memberId) => {
  if (!memberId) return null
  return memberStore.members.find(member => member.id === memberId)
}

const getSelectedMemberName = (memberId, fallback = '-') => {
  return getMemberById(memberId)?.name || fallback
}

const loadDailyStats = async () => {
  loading.value = true
  try {
    const payload = {
      created_by_name: getMemberById(zbonForm.value.employeeMemberId)?.name || null,
      cash_counted_by_name: getMemberById(zbonForm.value.checkerMemberId)?.name || null,
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
      total_amount: Math.round((preview.summary?.gross_sales_total || 0) * 100),
      transaction_count: preview.summary?.transaction_count || 0,
      cash_calculated: preview.summary?.cash_calculated || 0,
      withdrawal_total: Math.round((preview.summary?.cash_withdrawals_total || 0) * 100),
      voucher_open_total: preview.summary?.voucher_open_total || 0,
      period_start: preview.period_start,
      period_end: preview.period_end,
      receipt_min: preview.summary?.receipt_number_min,
      receipt_max: preview.summary?.receipt_number_max,
      report_content: preview.report_content || '',
      transactions: preview.transactions || [],
    }
    zBonHtml.value = preview.report_content || ''
  } catch (error) {
    console.error('Error loading Z-Bon preview:', error)
    dailyStats.value = {
      cash_total: 0,
      balance_total: 0,
      voucher_total: 0,
      total_amount: 0,
      transaction_count: 0,
      cash_calculated: 0,
      withdrawal_total: 0,
      voucher_open_total: 0,
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
  if (transaction.voucher_applied_cents > 0 && transaction.voucher_type) {
    return transaction.voucher_type === 'GIFT' ? 'voucher-gift' : 'voucher-prepaid'
  }

  return transaction.payment_method.toLowerCase()
}

const getPaymentBadgeLabel = (transaction) => {
  if (transaction.voucher_applied_cents > 0 && transaction.voucher_type) {
    const baseLabel = transaction.payment_method === 'BALANCE' ? '💳 Guthaben' : '💰 BAR'
    const voucherLabel = transaction.voucher_type === 'GIFT' ? '🎁 Gutschein' : '🎫 Gutschein'
    return `${voucherLabel} + ${baseLabel}`
  }

  if (transaction.payment_method === 'VOUCHER_GIFT') {
    return '🎁 Gutschein'
  }

  if (transaction.payment_method === 'VOUCHER_PREPAID') {
    return '🎫 Gutschein'
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

const toggleTransaction = (transactionId) => {
  if (expandedTransactions.value.has(transactionId)) {
    expandedTransactions.value.delete(transactionId)
  } else {
    expandedTransactions.value.add(transactionId)
  }
}

const openCashCounterModal = () => {
  showCashCounterModal.value = true
}
const onCashCounterConfirm = (data) => {
  cashCountData.value = data
  loadDailyStats()
}

const openMemberPicker = async (target) => {
  memberPickerTarget.value = target
  memberSearch.value = ''
  if (!memberStore.members.length) {
    await memberStore.getMembers()
  }
  showMemberPickerModal.value = true
}

const closeMemberPicker = () => {
  showMemberPickerModal.value = false
  memberPickerTarget.value = null
  memberSearch.value = ''
}

const selectMemberForTarget = (member) => {
  if (memberPickerTarget.value === 'employeeMemberId') {
    zbonForm.value.employeeMemberId = member.id
  } else if (memberPickerTarget.value === 'checkerMemberId') {
    zbonForm.value.checkerMemberId = member.id
  } else if (memberPickerTarget.value === 'withdrawalMemberId') {
    withdrawalForm.value.memberId = member.id
  }

  closeMemberPicker()
}

// Download Z-Bon as HTML file
const handleDownloadZBon = async () => {
  try {
    if (!zBonHtml.value) {
      await loadDailyStats()
    }

    const blob = new Blob([zBonHtml.value], { type: 'text/html;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Z-Bon-Vorschau.html`
    a.click()
    window.URL.revokeObjectURL(url)
    notificationStore.success('Z-Bon HTML erfolgreich heruntergeladen')
  } catch (error) {
    console.error('Error downloading Z-Bon HTML:', error)
    notificationStore.error(`Fehler beim Download: ${error.response?.data?.detail || error.message}`)
  }
}

const openZbonCreateModal = async () => {
  if (!memberStore.members.length) {
    await memberStore.getMembers()
  }
  zbonForm.value.authPassword = ''
  showZbonCreateModal.value = true
}

const closeZbonCreateModal = () => {
  zbonForm.value.authPassword = ''
  showZbonCreateModal.value = false
}

const openWithdrawalModal = async () => {
  if (!memberStore.members.length) {
    await memberStore.getMembers()
  }
  showWithdrawalModal.value = true
}

const closeWithdrawalModal = () => {
  withdrawalForm.value = {
    amount: '',
    memberId: null,
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

  const memberName = getMemberById(withdrawalForm.value.memberId)?.name
  if (!memberName) {
    notificationStore.error('Bitte eine Person auswählen')
    return
  }

  const note = withdrawalForm.value.note?.trim()
  const reason = note
    ? `Abschöpfung - ${memberName} - ${note}`
    : `Abschöpfung - ${memberName}`

  try {
    loading.value = true
    await apiService.post('/transactions/cash/withdrawal', {
      amount_cents: Math.round(amount * 100),
      reason,
    })
    notificationStore.success('Abschöpfung erfolgreich gespeichert')
    closeWithdrawalModal()
    await loadDailyStats()
    if (activeTab.value === 'zbons') {
      await loadZbonsHistory()
    }
  } catch (error) {
    console.error('Error recording withdrawal:', error)
    notificationStore.error(`Fehler beim Speichern: ${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const createZBon = async () => {
  const employeeName = getMemberById(zbonForm.value.employeeMemberId)?.name
  const checkerName = getMemberById(zbonForm.value.checkerMemberId)?.name

  if (!employeeName) {
    notificationStore.error('Bitte einen Mitarbeiter auswählen')
    return
  }

  if (!checkerName) {
    notificationStore.error('Bitte eine Sichtkontrolle auswählen')
    return
  }

  if (!zbonForm.value.authPassword) {
    notificationStore.error('Bitte das Passwort des angemeldeten Benutzers eingeben')
    return
  }

  try {
    loading.value = true
    await apiService.post('/transactions/zbon/create', {
      created_by_name: employeeName,
      cash_counted_by_name: checkerName,
      auth_password: zbonForm.value.authPassword,
      cash_count: cashCountData.value
        ? {
          coins: cashCountData.value.coins,
          notes: cashCountData.value.notes,
        }
        : null,
    })
    notificationStore.success('Z-Bon erfolgreich erstellt')
    closeZbonCreateModal()
    cashCountData.value = null
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

const selectZbon = async (zbon) => {
  if (selectedZbon.value?.id === zbon.id) {
    selectedZbon.value = null
    return
  }

  try {
    const response = await apiService.get(`/transactions/zbon/history/${zbon.sequence_number}`)
    selectedZbon.value = response.data
  } catch (error) {
    console.error('[Finance] Error loading Z-Bon detail:', error)
    notificationStore.error('Fehler beim Laden der Z-Bon-Details')
  }
}

const downloadZbonHTML = async (zbon) => {
  try {
    const response = await apiService.get(`/transactions/zbon/history/${zbon.sequence_number}/html`, {
      responseType: 'text',
    })

    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/html;charset=utf-8,' + encodeURIComponent(response.data))
    element.setAttribute('download', `Z-Bon-${zbon.sequence_number}.html`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
    notificationStore.success('Z-Bon HTML heruntergeladen')
  } catch (error) {
    console.error('[Finance] Error downloading Z-Bon HTML:', error)
    notificationStore.error('Fehler beim Herunterladen der Z-Bon')
  }
}

const downloadZbonPDF = async (zbon) => {
  try {
    const response = await apiService.get(`/transactions/zbon/history/${zbon.sequence_number}/pdf`, {
      responseType: 'blob',
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Z-Bon-${zbon.sequence_number}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.parentNode.removeChild(link)
    window.URL.revokeObjectURL(url)
    notificationStore.success('Z-Bon PDF heruntergeladen')
  } catch (error) {
    console.error('[Finance] Error downloading Z-Bon PDF:', error)
    notificationStore.error('PDF-Export nicht verfügbar, als HTML heruntergeladen')
    // Fallback to HTML
    downloadZbonHTML(zbon)
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

// Watch für Tab-Wechsel
watch(activeTab, (newTab) => {
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
  loadDailyStats()
  applyFilters()
  loadRevenueStats()
  loadMemberStats()
  loadSchedulerStatus()
})
</script>

<style scoped lang="scss">
.admin-finance {
  background: #dde2e8;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);

  h2 {
    margin-bottom: 2rem;
    color: #333;
  }

  h3 {
    margin-bottom: 1.5rem;
    color: #555;
  }

  h4 {
    margin: 1.5rem 0 1rem 0;
    color: #666;
  }
}

.finance-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #aeb5be;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: var(--app-banner-color);
  border: 1px solid color-mix(in srgb, var(--app-banner-color) 70%, #000 30%);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  cursor: pointer;
  font-weight: 600;
  color: var(--app-banner-contrast);
  transition: all 0.2s;

  &:hover {
    opacity: 0.92;
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
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;

  label {
    font-weight: 600;
  }

  input {
    padding: 0.5rem;
    border: 1px solid #9ca4ae;
    border-radius: 4px;
    font-size: 1rem;
  }
}

.filter-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #d8dde3;
  border-radius: 4px;
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
    padding: 0.5rem;
      border: 1px solid #9ca4ae;
    border-radius: 4px;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);

  &.highlight {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.warning {
    background: linear-gradient(135deg, #ffb74d 0%, #ef6c00 100%);
  }

  .card-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 0.5rem;
  }

  .card-value {
    font-size: 1.8rem;
    font-weight: bold;
  }
}

.daily-transactions,
.payment-stats,
.top-products {
  margin: 2rem 0;
}

.transactions-table,
.products-table,
.members-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;

  thead {
    background: #d8dde3;

    th {
      padding: 1rem;
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
        padding: 1rem;

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

.history-summary,
.revenue-overview,
.member-stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-item,
.stat-card,
.revenue-card {
  background: #d8dde3;
  padding: 1.5rem;
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
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
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
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;

  &:hover {
    background: #e0e0e0;
  }
}

.zbon-actions {
  display: flex;
  gap: 0.75rem;
  margin: 0 0 1.5rem 0;
  flex-wrap: wrap;
}
.form-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.scheduler-section {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
}

.confirmation-dialog {
  background: #dde2e8;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  width: min(100%, 520px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  text-align: center;

  h3 {
    margin: 0 0 0.75rem 0;
    color: #333;
  }

  p {
    margin: 0 0 1.5rem 0;
    color: #666;
  }
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.selection-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  text-align: left;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }
}

.member-select-btn {
  padding: 0.85rem 1rem;
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
  border-radius: 4px;
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

.zbon-preview-frame-shell {
  background: white;
  border-radius: 4px;
  max-height: 600px;
  overflow: hidden;
  border: 1px solid #eee;
}

.zbon-preview-frame {
  width: 100%;
  min-height: 600px;
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
  border-radius: 4px;

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
</style>
