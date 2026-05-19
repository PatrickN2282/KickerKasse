"""Email-optimized Z-Bon HTML template
Optimized for maximum compatibility with email clients (Gmail, Outlook, etc.)
Uses inline styles and simple table-based layout
"""

ZBON_EMAIL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kassenbericht {{ business_date }}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f5f5f5;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; background-color: #f5f5f5;">
        <tr>
            <td style="padding: 20px 0;">
                <!-- Main container -->
                <table cellpadding="0" cellspacing="0" style="width: 600px; max-width: 100%; margin: 0 auto; background-color: #ffffff; border: 1px solid #ddd; border-radius: 4px;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 20px; background-color: #f8f9fa; border-bottom: 2px solid #0275d8;">
                            <h2 style="margin: 0 0 10px 0; color: #333; font-size: 24px;">Kassenbericht #{{ seq_number }}</h2>
                            <p style="margin: 0; color: #666; font-size: 14px;">Tagesabschluss vom {{ business_date }}</p>
                        </td>
                    </tr>
                    
                    <!-- Meta Information -->
                    <tr>
                        <td style="padding: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; font-size: 13px; color: #666;">
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Erstellungsdatum:</strong></td>
                                    <td style="text-align: right;">{{ created_at }}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Zeitraum:</strong></td>
                                    <td style="text-align: right;">{{ period_start }} - {{ period_end }}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 5px 0;"><strong>Belegnummern:</strong></td>
                                    <td style="text-align: right;">#{{ receipt_min }} - #{{ receipt_max }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Sales Summary -->
                    <tr>
                        <td style="padding: 20px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px; border-bottom: 2px solid #0275d8; padding-bottom: 10px;">Umsatzübersicht</h3>
                            <table cellpadding="8" cellspacing="0" style="width: 100%; font-size: 13px;">
                                <tr style="background-color: #f5f5f5;">
                                    <th style="text-align: left; padding: 8px;">Kategorie</th>
                                    <th style="text-align: right; padding: 8px;">Anzahl</th>
                                    <th style="text-align: right; padding: 8px;">Betrag</th>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">Bargeldverkäufe</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee;">{{ cash_sales_count }}</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">€ {{ cash_sales_gross }}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">Guthabenverkäufe</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee;">{{ balance_sales_count }}</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">€ {{ guthaben_gross }}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">Aufladungen</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee;">{{ recharge_count }}</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">€ {{ recharge_total }}</td>
                                </tr>
                                <tr style="background-color: #fff3cd; border-top: 2px solid #ffc107; border-bottom: 2px solid #ffc107;">
                                    <td style="padding: 10px; font-weight: bold;">GESAMTSUMME</td>
                                    <td style="text-align: right; padding: 10px; font-weight: bold;">{{ total_items_count }}</td>
                                    <td style="text-align: right; padding: 10px; font-weight: bold; font-size: 16px;">€ {{ total_gross }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Categories breakdown -->
                    {% if categories_breakdown %}
                    <tr>
                        <td style="padding: 20px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; font-size: 16px; border-bottom: 2px solid #0275d8; padding-bottom: 10px;">Umsatz nach Kategorie</h3>
                            <table cellpadding="8" cellspacing="0" style="width: 100%; font-size: 13px;">
                                <tr style="background-color: #f5f5f5;">
                                    <th style="text-align: left; padding: 8px;">Kategorie</th>
                                    <th style="text-align: right; padding: 8px;">Anzahl</th>
                                    <th style="text-align: right; padding: 8px;">Summe</th>
                                </tr>
                                {% for category, data in categories_breakdown.items() %}
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{{ category }}</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee;">{{ data.count }}</td>
                                    <td style="text-align: right; padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">€ {{ data.total }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </td>
                    </tr>
                    {% endif %}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px; background-color: #f8f9fa; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center;">
                            <p style="margin: 0;">Diese E-Mail wurde automatisch generiert.</p>
                            <p style="margin: 5px 0 0 0;">Bitte speichern Sie diesen Kassenbericht für Ihre Unterlagen.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
