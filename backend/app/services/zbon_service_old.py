"""Z-Bon Generation Service with TSE compliance and daily report"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Transaction, TransactionType, PaymentMethod, BalanceLog
from app.repositories import TransactionRepository
import logging

logger = logging.getLogger(__name__)


class ZBonService:
    """Service for generating Z-Bon reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.trans_repo = TransactionRepository(db)
    
    def generate_zbon(
        self,
        target_date: date = None,
        include_cash_count: dict = None,
        report_type: str = "zbon"  # "zbon" or "daily-report"
    ) -> dict:
        """
        Generate Z-Bon or daily report
        
        Args:
            target_date: Date to generate report for (default: today)
            include_cash_count: Dict with cash count {'coins': {...}, 'notes': {...}} (optional)
            report_type: Type of report ("zbon" for TSE-compliant Z-Bon, "daily-report" for protocol)
        
        Returns:
            Dict with report data and formatted text
        """
        if not target_date:
            target_date = date.today()
        
        # Get all transactions for the day
        transactions = self.db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        # Calculate statistics
        stats = self._calculate_stats(transactions)
        meta = self._collect_meta(target_date, transactions)
        
        # Generate report content
        if report_type == "daily-report":
            content = self._generate_daily_report(target_date, stats, meta, include_cash_count, transactions)
        else:
            content = self._generate_zbon(target_date, stats, meta, include_cash_count, transactions)
        
        return {
            "content": content,
            "date": target_date.isoformat(),
            "type": report_type,
            "stats": stats,
            "meta": meta,
            "has_cash_count": include_cash_count is not None,
        }
    
    def _calculate_stats(self, transactions: list) -> dict:
        """Calculate statistics from transactions"""
        cash_sales = [t for t in transactions if t.payment_method == PaymentMethod.CASH and t.type == TransactionType.SALE]
        balance_sales = [t for t in transactions if t.payment_method == PaymentMethod.BALANCE and t.type == TransactionType.SALE]
        recharges = [t for t in transactions if t.type == TransactionType.RECHARGE]
        stornos = [t for t in transactions if t.type == TransactionType.STORNO]
        
        cash_total = sum(t.total_amount_cents for t in cash_sales) // 100
        balance_total = sum(t.total_amount_cents for t in balance_sales) // 100
        recharge_total = sum(t.total_amount_cents for t in recharges) // 100
        storno_total = sum(t.total_amount_cents for t in stornos) // 100
        
        return {
            "cash_sales_count": len(cash_sales),
            "cash_sales_total": cash_total,
            "balance_sales_count": len(balance_sales),
            "balance_sales_total": balance_total,
            "recharge_count": len(recharges),
            "recharge_total": recharge_total,
            "storno_count": len(stornos),
            "storno_total": storno_total,
            "total_transactions": len(transactions),
            "gross_revenue": (cash_total + balance_total) - storno_total,
            "total_member_recharge": recharge_total,
        }

    def _collect_meta(self, target_date: date, transactions: list) -> dict:
        """Collect additional metadata for report transparency and audit."""
        sorted_transactions = sorted(transactions, key=lambda t: t.created_at) if transactions else []
        first_tx = sorted_transactions[0] if sorted_transactions else None
        last_tx = sorted_transactions[-1] if sorted_transactions else None

        receipt_numbers = [t.receipt_number for t in sorted_transactions if t.receipt_number is not None]

        return {
            "business_date": target_date.strftime("%d.%m.%Y"),
            "report_generated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "report_id": f"ZB-{target_date.strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
            "first_tx_time": first_tx.created_at.strftime("%H:%M:%S") if first_tx else "-",
            "last_tx_time": last_tx.created_at.strftime("%H:%M:%S") if last_tx else "-",
            "receipt_min": min(receipt_numbers) if receipt_numbers else "-",
            "receipt_max": max(receipt_numbers) if receipt_numbers else "-",
            "has_tse_signature": False,
        }
    
    def _generate_zbon(
        self,
        target_date: date,
        stats: dict,
        meta: dict,
        cash_count: dict = None,
        transactions: list = None
    ) -> str:
        """
        Generate TSE-compliant Z-Bon
        
        Format based on German TSE (Technische Sicherheitseinrichtung) guidelines
        """
        now = datetime.now()
        date_str = target_date.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")
        
        lines = []
        lines.append("=" * 60)
        lines.append("KGB - KICKERKASSE - Z-BON (TAGESABSCHLUSS)")
        lines.append("=" * 60)
        lines.append("")
        lines.append("Geschäftsadresse:")
        lines.append("Krökel Gemeinschaft Badenstedt – Hannover e.V.")
        lines.append("Davenstedter Str. 115")
        lines.append("30453 Hannover")
        lines.append("Vereinsregister: VR 203296")
        lines.append("Registergericht: Amtsgericht Hannover")
        lines.append("")
        lines.append("Kontakt: info@kgbhannover.de")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")
        lines.append(f"Datum:                {meta['business_date']}")
        lines.append(f"Erstellt am:          {meta['report_generated_at']}")
        lines.append(f"Report-ID:            {meta['report_id']}")
        lines.append(f"Transaktionszeitraum: {meta['first_tx_time']} - {meta['last_tx_time']}")
        lines.append(f"Belegnummern:         {meta['receipt_min']} - {meta['receipt_max']}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("UMSÄTZE")
        lines.append("-" * 60)
        lines.append("")
        
        lines.append("Verkäufe (Bargeld):")
        lines.append(f"  Anzahl:             {stats['cash_sales_count']:>6}")
        lines.append(f"  Summe:              {stats['cash_sales_total']:>8.2f} EUR")
        lines.append("")
        
        lines.append("Verkäufe (Guthaben):")
        lines.append(f"  Anzahl:             {stats['balance_sales_count']:>6}")
        lines.append(f"  Summe:              {stats['balance_sales_total']:>8.2f} EUR")
        lines.append(f"  (Keine Kasseneinnahme)")
        lines.append("")
        
        lines.append("Guthabenaufladungen:")
        lines.append(f"  Anzahl:             {stats['recharge_count']:>6}")
        lines.append(f"  Summe:              {stats['recharge_total']:>8.2f} EUR")
        lines.append(f"  (Kasseneinnahme)")
        lines.append("")
        
        if stats['storno_count'] > 0:
            lines.append("Stornierungen:")
            lines.append(f"  Anzahl:             {stats['storno_count']:>6}")
            lines.append(f"  Summe:              {stats['storno_total']:>8.2f} EUR")
            lines.append("")
        
        lines.append("-" * 60)
        lines.append("ZUSAMMENFASSUNG")
        lines.append("-" * 60)
        lines.append("")
        
        total_cash_in_register = stats['cash_sales_total'] + stats['recharge_total']
        lines.append(f"Kasseneinnahme (BAR):         {total_cash_in_register:>8.2f} EUR")
        lines.append(f"  - Verkäufe:                 {stats['cash_sales_total']:>8.2f} EUR")
        lines.append(f"  - Guthabenaufladungen:      {stats['recharge_total']:>8.2f} EUR")
        lines.append("")
        
        lines.append(f"Guthabentransaktionen:        {stats['balance_sales_total']:>8.2f} EUR")
        lines.append(f"  (außerkassig)")
        lines.append("")
        
        if cash_count:
            lines.append("-" * 60)
            lines.append("KASSENZÄHLUNG")
            lines.append("-" * 60)
            lines.append("")
            
            counted_total = self._format_cash_count(cash_count, lines)
            lines.append("")
            lines.append(f"Gezählter Betrag:             {counted_total:>8.2f} EUR")
            lines.append(f"Sollbestand:                  {total_cash_in_register:>8.2f} EUR")
            lines.append(f"Differenz:                    {counted_total - total_cash_in_register:>8.2f} EUR")
            lines.append("")
        
        lines.append("-" * 60)
        lines.append("ZUSÄTZLICHE INFORMATIONEN")
        lines.append("-" * 60)
        lines.append("")
        lines.append("Gesamttransaktionen:          {count:>6}".format(count=stats['total_transactions']))
        lines.append("Berichtstyp:                  Z-BON / Tagesabschluss")
        lines.append("Rechtliche Grundlage:         KassenSichV / GoBD (Pruefstatus)")
        lines.append("")
        lines.append("TSE-/KassenSichV-Pflichtangaben (Status):")
        lines.append("  - Laufende Belegnummer:     vorhanden")
        lines.append("  - Zeitangabe Beleg:         vorhanden")
        lines.append("  - Zahlungsart:              vorhanden")
        lines.append("  - Transaktionsbetrag:       vorhanden")
        lines.append("  - TSE-Seriennummer:         NICHT vorhanden")
        lines.append("  - Signaturzaehler:          NICHT vorhanden")
        lines.append("  - Pruefwert/Signatur:       NICHT vorhanden")
        lines.append("")
        lines.append("Wichtiger Hinweis:")
        lines.append("Dieser Ausdruck ist ein interner Tagesabschlussbericht.")
        lines.append("Ohne zertifizierte TSE-Signaturdaten ist dies kein vollstaendig")
        lines.append("TSE-signierter Kassenbeleg im Sinne der KassenSichV.")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_daily_report(
        self,
        target_date: date,
        stats: dict,
        meta: dict,
        cash_count: dict = None,
        transactions: list = None
    ) -> str:
        """
        Generate detailed daily protocol report
        """
        now = datetime.now()
        date_str = target_date.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")
        
        lines = []
        lines.append("=" * 70)
        lines.append("KGB - KICKERKASSE - TAGESBERICHTSPROTOKOLL")
        lines.append("=" * 70)
        lines.append("")
        lines.append("Geschäftsadresse:")
        lines.append("Krökel Gemeinschaft Badenstedt – Hannover e.V.")
        lines.append("Davenstedter Str. 115")
        lines.append("30453 Hannover")
        lines.append("Vereinsregister: VR 203296")
        lines.append("Registergericht: Amtsgericht Hannover")
        lines.append("")
        lines.append("Kontakt: info@kgbhannover.de")
        lines.append("")
        lines.append("-" * 70)
        lines.append("")
        lines.append(f"Datum:                      {meta['business_date']}")
        lines.append(f"Berichtszeit:               {meta['report_generated_at']}")
        lines.append(f"Report-ID:                  {meta['report_id']}")
        lines.append(f"Belegnummern:               {meta['receipt_min']} - {meta['receipt_max']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("TAGESSTATISTIK")
        lines.append("-" * 70)
        lines.append("")
        
        lines.append(f"Gesamttransaktionen:        {stats['total_transactions']:>6}")
        lines.append("")
        
        lines.append("Nach Transaktionstyp:")
        lines.append(f"  Verkäufe (Bargeld):       {stats['cash_sales_count']:>6}")
        lines.append(f"  Verkäufe (Guthaben):      {stats['balance_sales_count']:>6}")
        lines.append(f"  Guthabenaufladungen:      {stats['recharge_count']:>6}")
        lines.append(f"  Stornierungen:            {stats['storno_count']:>6}")
        lines.append("")
        
        lines.append("-" * 70)
        lines.append("UMSATZAUSZUG")
        lines.append("-" * 70)
        lines.append("")
        
        lines.append(f"Bruttoumsatz (Bargeld):       {stats['cash_sales_total']:>10.2f} EUR")
        lines.append(f"Bruttoumsatz (Guthaben):      {stats['balance_sales_total']:>10.2f} EUR")
        lines.append(f"Guthabenaufladungen:          {stats['recharge_total']:>10.2f} EUR")
        
        if stats['storno_total'] > 0:
            lines.append(f"Stornierungen:                {-stats['storno_total']:>10.2f} EUR")
        
        lines.append("")
        
        net_value = (stats['cash_sales_total'] + stats['recharge_total'])
        lines.append(f"KASSENEINNAHME (BAR):         {net_value:>10.2f} EUR")
        lines.append("-" * 70)
        lines.append("")
        
        if cash_count:
            lines.append("KASSENZÄHLUNG & VERGLEICH")
            lines.append("-" * 70)
            lines.append("")
            
            counted_total = self._format_cash_count(cash_count, lines)
            lines.append("")
            lines.append(f"Gezählter Bestand:            {counted_total:>10.2f} EUR")
            lines.append(f"Sollbestand (Umsätze):        {net_value:>10.2f} EUR")
            diff = counted_total - net_value
            lines.append(f"Differenz:                    {diff:>10.2f} EUR")
            
            if abs(diff) < 0.01:
                lines.append("")
                lines.append("✓ Kasse stimmt überein")
            else:
                lines.append("")
                lines.append("⚠ Abweichung erkannt - bitte überprüfen")
            
            lines.append("")
        
        # Transaction details
        if transactions:
            lines.append("-" * 70)
            lines.append("TRANSAKTIONSDETAILS")
            lines.append("-" * 70)
            lines.append("")
            
            for trans in sorted(transactions, key=lambda t: t.created_at)[:50]:  # First 50
                time = trans.created_at.strftime("%H:%M:%S")
                type_str = "SALE" if trans.type == TransactionType.SALE else "RECHARGE" if trans.type == TransactionType.RECHARGE else "STORNO"
                payment = "BAR" if trans.payment_method == PaymentMethod.CASH else "GUTHABEN"
                
                lines.append(f"{time} | Belegnr. {trans.receipt_number:>6} | {type_str:>8} | {payment:>8} | {trans.total_amount_cents/100:>8.2f} EUR")
            
            if len(transactions) > 50:
                lines.append(f"... und {len(transactions) - 50} weitere Transaktionen")
            
            lines.append("")

        lines.append("TSE-Hinweis: Dieser Bericht enthaelt keine TSE-Signaturdaten")
        lines.append("(Seriennummer, Signaturzaehler, Pruefwert) und dient als")
        lines.append("interner Tagesabschluss-/Pruefbericht.")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _format_cash_count(self, cash_count: dict, lines: list) -> float:
        """Format cash count details and return total"""
        total = 0.0
        
        if 'coins' in cash_count:
            lines.append("Münzen:")
            for denomination, count in sorted(cash_count['coins'].items(), key=lambda x: float(x[0]), reverse=True):
                value = float(denomination) * count
                total += value
                lines.append(f"  {denomination:>6} EUR × {count:>3} St. = {value:>8.2f} EUR")
        
        if 'notes' in cash_count:
            lines.append("")
            lines.append("Scheine:")
            for denomination, count in sorted(cash_count['notes'].items(), key=lambda x: float(x[0]), reverse=True):
                value = float(denomination) * count
                total += value
                lines.append(f"  {denomination:>6} EUR × {count:>3} St. = {value:>8.2f} EUR")
        
        return total
