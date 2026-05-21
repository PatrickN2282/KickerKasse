"""HTML Templates for Z-Bon reports"""

ZBON_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kassenbericht {{ seq_number }} - {{ business_date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* Header */
        .header {
            text-align: center;
            border-bottom: 3px solid #333;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .header .subtitle {
            font-size: 16px;
            color: #666;
            margin-bottom: 10px;
        }
        
        .zbon-number {
            font-size: 18px;
            font-weight: bold;
            color: #d9534f;
            margin: 10px 0;
        }
        
        .business-info {
            text-align: center;
            font-size: 11px;
            color: #888;
            margin-top: 15px;
            line-height: 1.6;
        }
        
        /* Meta Info Section */
        .meta-section {
            background-color: #f9f9f9;
            border-left: 4px solid #0275d8;
            padding: 12px;
            margin: 20px 0;
            font-size: 12px;
        }
        
        .meta-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .meta-row:last-child {
            margin-bottom: 0;
        }
        
        .meta-label {
            font-weight: bold;
            width: 40%;
        }
        
        .meta-value {
            width: 60%;
            text-align: right;
        }
        
        /* Separator */
        .separator {
            border-top: 2px solid #ddd;
            margin: 20px 0;
        }
        
        .separator-heavy {
            border-top: 3px solid #333;
            margin: 20px 0;
        }
        
        /* Table Styles */
        .section-title {
            font-size: 14px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            background-color: #f0f0f0;
            padding: 8px;
            border-left: 3px solid #0275d8;
        }
        
        table {
            width: 100%;
            font-size: 12px;
            margin-bottom: 10px;
            border-collapse: collapse;
        }
        
        th {
            background-color: #f0f0f0;
            padding: 8px;
            text-align: left;
            font-weight: bold;
            border-bottom: 2px solid #333;
        }
        
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        .amount {
            text-align: right;
            font-family: 'Courier New', monospace;
            min-width: 100px;
        }
        
        .total-row {
            font-weight: bold;
            background-color: #f9f9f9;
            border-top: 2px solid #333;
            border-bottom: 2px solid #333;
        }
        
        .subtotal-row {
            border-top: 1px solid #ddd;
            background-color: #fafafa;
        }
        
        /* Summary Box */
        .summary-box {
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        
        .summary-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 13px;
        }
        
        .summary-row:last-child {
            margin-bottom: 0;
        }
        
        .summary-row .label {
            font-weight: bold;
        }
        
        .summary-row .value {
            text-align: right;
            font-family: 'Courier New', monospace;
            min-width: 120px;
        }
        
        .summary-total {
            font-size: 16px;
            font-weight: bold;
            color: #d9534f;
            border-top: 2px solid #ffc107;
            padding-top: 10px;
            margin-top: 10px;
        }
        
        /* Cash Count */
        .cash-count {
            background-color: #e8f4f8;
            border-left: 4px solid #0275d8;
            padding: 12px;
            margin: 15px 0;
            font-size: 11px;
        }
        
        .cash-line {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-family: 'Courier New', monospace;
        }
        
        .cash-line:last-child {
            margin-bottom: 0;
        }
        
        .denomination {
            text-align: right;
            min-width: 50px;
        }
        
        .count {
            text-align: right;
            min-width: 40px;
        }
        
        .subtotal {
            text-align: right;
            font-weight: bold;
            min-width: 60px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            font-size: 11px;
            color: #666;
        }
        
        .footer-text {
            margin: 5px 0;
            line-height: 1.5;
        }
        
        .page-break {
            page-break-after: always;
            margin-top: 40px;
        }
        
        /* Print Styles */
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 20px;
                max-width: 100%;
            }
            
            .page {
                page-break-after: always;
                margin-bottom: 40px;
            }
            
            .page:last-child {
                page-break-after: avoid;
            }
        }
        
        /* Highlights */
        .highlight-error {
            color: #d9534f;
            font-weight: bold;
        }
        
        .highlight-success {
            color: #28a745;
            font-weight: bold;
        }
        
        /* Column alignment */
        .text-left {
            text-align: left;
        }
        
        .text-right {
            text-align: right;
        }
        
        .text-center {
            text-align: center;
        }
        
        /* Line numbers */
        .line-number {
            color: #999;
            font-size: 10px;
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>KGB Zentrale</h1>
            <div class="subtitle">KickerKasse - Tagesabschluss</div>
            <div class="zbon-number">Kassenbericht {{ seq_number }}</div>
            <div class="business-info">
                <div>Krökel Gemeinschaft Badenstedt – Hannover e.V.</div>
                <div>Davenstedter Str. 115 | 30453 Hannover</div>
                <div>Vereinsregister: VR 203296</div>
            </div>
        </div>
        
        <!-- Meta Information -->
        <div class="meta-section">
            <div class="meta-row">
                <span class="meta-label">Geschäftstag:</span>
                <span class="meta-value">{{ business_date }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Erstellt am:</span>
                <span class="meta-value">{{ created_at }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Kasse:</span>
                <span class="meta-value">Kasse 1</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Zeitraum:</span>
                <span class="meta-value">{{ period_start }} - {{ period_end }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Belegnummern:</span>
                <span class="meta-value">#{{ receipt_min }} bis #{{ receipt_max }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Anzahl Transaktionen:</span>
                <span class="meta-value">{{ transaction_count_total|default(0) }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Mitarbeiter:</span>
                <span class="meta-value">{{ created_by_name|default('-') }}</span>
            </div>
            <div class="meta-row">
                <span class="meta-label">Sichtkontrolle:</span>
                <span class="meta-value">{{ cash_counted_by_name|default('-') }}</span>
            </div>
        </div>
        
        <div class="separator-heavy"></div>
        
        <!-- Sales Overview -->
        <div class="section-title">📊 Artikelumsatz</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Brutto</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Verkäufe (Bargeld)</td>
                    <td class="amount">{{ cash_sales_count }}</td>
                    <td class="amount"><strong>{{ article_cash_sales_gross }}</strong></td>
                </tr>
                <tr>
                    <td>Verkäufe (Guthaben)</td>
                    <td class="amount">{{ balance_sales_count }}</td>
                    <td class="amount"><strong>{{ balance_sales_gross }}</strong></td>
                </tr>
                <tr>
                    <td>Verkäufe (Gutscheine)</td>
                    <td class="amount">{{ voucher_sales_count|default(0) }}</td>
                    <td class="amount"><strong>{{ voucher_sales_total|default("0.00") }}</strong></td>
                </tr>
                <tr class="total-row">
                    <td>Gesamtumsatz Artikel</td>
                    <td class="amount">{{ total_items_count }}</td>
                    <td class="amount">{{ article_sales_total }}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="section-title">💳 Zahlungsarten</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Brutto</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Barzahlung</td>
                    <td class="amount"><strong>{{ article_cash_sales_gross }}</strong></td>
                </tr>
                <tr>
                    <td>Guthaben</td>
                    <td class="amount"><strong>{{ balance_sales_gross }}</strong></td>
                </tr>
                <tr>
                    <td>Gutscheine</td>
                    <td class="amount"><strong>{{ voucher_sales_total|default("0.00") }}</strong></td>
                </tr>
                <tr class="total-row">
                    <td>Gesamtsumme Zahlungsarten</td>
                    <td class="amount">{{ article_sales_total }}</td>
                </tr>
            </tbody>
        </table>

        {% if product_groups_breakdown %}
        <div class="section-title">📦 Umsatz nach Warengruppe</div>
        <table>
            <thead>
                <tr>
                    <th>Warengruppe</th>
                    <th class="amount">Gesamtumsatz</th>
                </tr>
            </thead>
            <tbody>
                {% for group_name, data in product_groups_breakdown.items() %}
                <tr>
                    <td>{{ group_name }}</td>
                    <td class="amount">{{ "%.2f"|format(data.gross_total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        <div class="section-title">🧰 Interne Materialverkäufe</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Anzahl Verkäufe</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Verbrauchsmaterial - Intern</td>
                    <td class="amount"><strong>{{ material_account_sales_count|default(0) }}</strong></td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">🏦 Gutscheinkonto</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Kontostand Gutscheinkonto</td>
                    <td class="amount"><strong>{{ club_account_total|default("0.00") }}</strong></td>
                </tr>
            </tbody>
        </table>
         
        <div class="section-title">💳 Mitgliedsguthaben</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Guthaben verkauft</td>
                    <td class="amount">{{ recharge_count }}</td>
                    <td class="amount"><strong>{{ recharge_total }}</strong></td>
                </tr>
                <tr>
                    <td>Guthaben eingelöst</td>
                    <td class="amount">{{ balance_sales_count }}</td>
                    <td class="amount"><strong>{{ balance_sales_gross }}</strong></td>
                </tr>
                <tr class="total-row">
                    <td>Offenes Guthaben</td>
                    <td class="amount">{{ member_balance_open_count|default(0) }}</td>
                    <td class="amount">{{ balance_open_total|default("0.00") }}</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">🎫 Verzehrkarten</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Verzehrkarten verkauft</td>
                    <td class="amount">{{ prepaid_voucher_sales_count|default(0) }}</td>
                    <td class="amount"><strong>{{ prepaid_voucher_sales_total|default("0.00") }}</strong></td>
                </tr>
                <tr>
                    <td>Verzehrkarten eingelöst</td>
                    <td class="amount">{{ prepaid_voucher_redeemed_count|default(0) }}</td>
                    <td class="amount"><strong>{{ prepaid_voucher_redeemed_total|default("0.00") }}</strong></td>
                </tr>
                <tr class="total-row">
                    <td>Offene Verzehrkarten</td>
                    <td class="amount">{{ prepaid_voucher_open_count|default(0) }}</td>
                    <td class="amount">{{ prepaid_voucher_open_total|default("0.00") }}</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">🎁 Gutscheine</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Gutscheine erstellt</td>
                    <td class="amount">{{ voucher_created_count|default(0) }}</td>
                    <td class="amount"><strong>{{ voucher_created_total|default("0.00") }}</strong></td>
                </tr>
                <tr>
                    <td>Gutscheine eingelöst</td>
                    <td class="amount">{{ voucher_redeemed_count|default(0) }}</td>
                    <td class="amount"><strong>{{ voucher_redeemed_total|default("0.00") }}</strong></td>
                </tr>
                <tr class="total-row">
                    <td>Offene Gutscheine</td>
                    <td class="amount">{{ voucher_open_count|default(0) }}</td>
                    <td class="amount">{{ voucher_open_total|default("0.00") }}</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">🏦 Kassenbestand</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Anfangsbestand</td>
                    <td class="amount">{{ cash_opening_balance|default("0.00") }}</td>
                </tr>
                <tr>
                    <td>Bareinnahmen aus Artikelverkäufen</td>
                    <td class="amount">{{ article_cash_revenue|default("0.00") }}</td>
                </tr>
                <tr>
                    <td>Einnahmen aus Guthabenverkäufen</td>
                    <td class="amount">{{ recharge_total }}</td>
                </tr>
                <tr>
                    <td>Einnahmen aus Verzehrkarten</td>
                    <td class="amount">{{ prepaid_voucher_sales_total|default("0.00") }}</td>
                </tr>
                <tr>
                    <td>Abschöpfung</td>
                    <td class="amount">{{ cash_withdrawals_total|default("0.00") }}</td>
                </tr>
                <tr class="total-row">
                    <td>Soll-Endbestand</td>
                    <td class="amount">{{ cash_calculated }}</td>
                </tr>
                <tr>
                    <td>Ist-Bestand</td>
                    <td class="amount">{{ cash_counted|default("-") }}</td>
                </tr>
                {% if cash_difference is not none %}
                <tr>
                    <td>Differenz</td>
                    <td class="amount">{{ cash_difference }}</td>
                </tr>
                {% endif %}
            </tbody>
        </table>

        <div class="section-title">💸 Abschöpfung</div>
        {% if withdrawals|default([]) %}
        <table>
            <thead>
                <tr>
                    <th>Beleg</th>
                    <th>Zeitpunkt</th>
                    <th>Grund</th>
                    <th>Person</th>
                    <th class="amount">Betrag</th>
                </tr>
            </thead>
            <tbody>
                {% for withdrawal in withdrawals %}
                <tr>
                    <td>{% if withdrawal.receipt_number %}#{{ withdrawal.receipt_number }}{% else %}-{% endif %}</td>
                    <td>{{ withdrawal.created_at }}</td>
                    <td>{{ withdrawal.reason }}</td>
                    <td>{{ withdrawal.performed_by|default("-") }}</td>
                    <td class="amount">{{ "%.2f"|format(withdrawal.amount) }} EUR</td>
                </tr>
                {% endfor %}
                <tr class="total-row">
                    <td colspan="4">Gesamt</td>
                    <td class="amount">{{ cash_withdrawals_total|default("0.00") }} EUR</td>
                </tr>
            </tbody>
        </table>
        {% else %}
        <div class="summary-box">
            <div class="summary-row">
                <span class="label">Keine Abschöpfungen im Zeitraum</span>
                <span class="value">0.00 EUR</span>
            </div>
        </div>
        {% endif %}

        <div class="section-title">❌ Stornos / Korrekturen</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Wert</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Anzahl Stornos</td>
                    <td class="amount">{{ storno_count|default(0) }}</td>
                </tr>
                <tr>
                    <td>Gesamtbetrag stornierter Umsätze</td>
                    <td class="amount">{{ storno_total|default("0.00") }}</td>
                </tr>
            </tbody>
        </table>

        {% if tip_count is defined and tip_count > 0 %}
        <div class="section-title">💝 Trinkgeld-Spenden</div>
        <table>
            <thead>
                <tr>
                    <th>Beschreibung</th>
                    <th class="amount">Wert</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Anzahl Trinkgeld-Spenden</td>
                    <td class="amount">{{ tip_count }}</td>
                </tr>
                <tr>
                    <td>Gesamt Trinkgeld-Spenden</td>
                    <td class="amount">{{ tip_total }} €</td>
                </tr>
            </tbody>
        </table>
        {% endif %}

        {% if cash_count %}
        <div class="page-break"></div>
        
        <!-- Cash Count Section -->
        <div class="section-title">🪙 Bargeldzählung</div>
        <div class="cash-count">
            <div style="margin-bottom: 12px; border-bottom: 1px solid #0275d8; padding-bottom: 8px;">
                <strong>Münzen</strong>
            </div>
            {% for denomination, details in coins.items() %}
            <div class="cash-line">
                <span>{{ denomination }} EUR × {{ details.count }}</span>
                <span class="subtotal">{{ details.subtotal }} EUR</span>
            </div>
            {% endfor %}
            
            {% if coins %}
            <div class="cash-line" style="border-top: 1px solid #0275d8; margin-top: 8px; padding-top: 8px; font-weight: bold;">
                <span>Münzen Summe</span>
                <span class="subtotal">{{ coins_total }} EUR</span>
            </div>
            {% endif %}
        </div>
        
        <div class="cash-count">
            <div style="margin-bottom: 12px; border-bottom: 1px solid #0275d8; padding-bottom: 8px;">
                <strong>Scheine</strong>
            </div>
            {% for denomination, details in notes.items() %}
            <div class="cash-line">
                <span>{{ denomination }} EUR × {{ details.count }}</span>
                <span class="subtotal">{{ details.subtotal }} EUR</span>
            </div>
            {% endfor %}
            
            {% if notes %}
            <div class="cash-line" style="border-top: 1px solid #0275d8; margin-top: 8px; padding-top: 8px; font-weight: bold;">
                <span>Scheine Summe</span>
                <span class="subtotal">{{ notes_total }} EUR</span>
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="page-break"></div>
        
        <!-- Breakdown by Category -->
        {% if categories_breakdown %}
        <div class="section-title">🏷️ Umsatz nach Kategorien</div>
        <table>
            <thead>
                <tr>
                    <th>Kategorie</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Netto</th>
                    <th class="amount">Brutto</th>
                </tr>
            </thead>
            <tbody>
                {% for category, data in categories_breakdown.items() %}
                <tr>
                    <td>{{ category }}</td>
                    <td class="amount">{{ data.count }}</td>
                    <td class="amount">{{ "%.2f"|format(data.net_total) }}</td>
                    <td class="amount">{{ "%.2f"|format(data.gross_total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <!-- Breakdown by Customer Group -->
        {% if customer_groups %}
        <div class="section-title">👥 Umsatz nach Kundengruppe</div>
        <table>
            <thead>
                <tr>
                    <th>Kundengruppe</th>
                    <th class="amount">Anzahl</th>
                    <th class="amount">Netto</th>
                    <th class="amount">Brutto</th>
                </tr>
            </thead>
            <tbody>
                {% for group, data in customer_groups.items() %}
                <tr>
                    <td>{{ group }}</td>
                    <td class="amount">{{ data.count }}</td>
                    <td class="amount">{{ "%.2f"|format(data.net_total) }}</td>
                    <td class="amount">{{ "%.2f"|format(data.gross_total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <!-- Breakdown by Customer -->
        {% if customers %}
        <div class="section-title">👤 Umsatz nach Kunden</div>
        <table>
            <thead>
                <tr>
                    <th>Kunde</th>
                    <th class="amount">Netto</th>
                    <th class="amount">Brutto</th>
                </tr>
            </thead>
            <tbody>
                {% for customer, data in customers.items() %}
                <tr>
                    <td>{{ customer }}</td>
                    <td class="amount">{{ "%.2f"|format(data.net_total) }}</td>
                    <td class="amount">{{ "%.2f"|format(data.gross_total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <!-- Stornos -->
        {% if stornos %}
        <div class="section-title">❌ Stornierungen & Retouren</div>
        <table>
            <thead>
                <tr>
                    <th>Beleg</th>
                    <th>Produkt</th>
                    <th class="amount">Menge</th>
                    <th class="amount">EUR</th>
                </tr>
            </thead>
            <tbody>
                {% for storno in stornos %}
                <tr>
                    <td>#{{ storno.receipt_number }}</td>
                    <td>{{ storno.product_name }}</td>
                    <td class="amount">{{ storno.quantity }}</td>
                    <td class="amount">-{{ "%.2f"|format(storno.unit_price * storno.quantity) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <div class="separator-heavy"></div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-text">Vielen Dank für Deinen Besuch!</div>
            <div class="footer-text">Berichtstyp: {{ report_type_label|default("KASSENBERICHT") }} | Geschäftsjahr 2026</div>
            <div class="footer-text">Erzeugt: {{ created_at }}</div>
            <div class="footer-text" style="margin-top: 15px; color: #999; font-size: 10px;">
                Dieser Kassenbericht wurde automatisch generiert und archiviert.
            </div>
        </div>
    </div>
</body>
</html>
"""
