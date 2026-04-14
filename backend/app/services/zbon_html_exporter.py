"""Z-Bon HTML and PDF Export Service"""

from datetime import datetime, date
from jinja2 import Template
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not available - PDF export disabled")


class ZBonHTMLExporter:
    """Handles HTML rendering and PDF export for Z-Bon reports"""
    
    @staticmethod
    def get_template():
        """Get the Z-Bon HTML template"""
        from app.templates.zbon_template import ZBON_HTML_TEMPLATE
        return ZBON_HTML_TEMPLATE
    
    @staticmethod
    def get_email_template():
        """Get the Z-Bon email-optimized HTML template"""
        from app.templates.zbon_email_template import ZBON_EMAIL_HTML_TEMPLATE
        return ZBON_EMAIL_HTML_TEMPLATE
    
    @staticmethod
    def render_html(
        seq_number: int,
        business_date: str,
        created_at: str,
        period_start: str,
        period_end: str,
        receipt_min: int,
        receipt_max: int,
        cash_sales_count: int,
        cash_sales_net: float,
        cash_sales_tax: float,
        cash_sales_gross: float,
        balance_sales_count: int,
        balance_sales_net: float,
        balance_sales_tax: float,
        balance_sales_gross: float,
        recharge_count: int,
        recharge_total: float,
        total_items_count: int,
        total_net: float,
        total_tax: float,
        total_gross: float,
        cash_revenue: float,
        guthaben_net: float,
        guthaben_gross: float,
        total_revenue: float,
        categories_breakdown: dict = None,
        customer_groups: dict = None,
        customers: dict = None,
        stornos: list = None,
        cash_count: dict = None,
        coins: dict = None,
        notes: dict = None,
        coins_total: float = 0,
        notes_total: float = 0,
        cash_counted: float = 0,
        cash_calculated: float = 0,
        cash_difference: float = 0,
    ) -> str:
        """
        Render Z-Bon HTML template with data
        
        Returns:
            Rendered HTML string
        """
        template_str = ZBonHTMLExporter.get_template()
        template = Template(template_str)
        
        # Prepare cash denomination breakdown
        coins_formatted = {}
        if coins:
            for denom, count in coins.items():
                coins_formatted[denom] = {
                    "count": count,
                    "subtotal": float(denom) * count
                }
        
        notes_formatted = {}
        if notes:
            for denom, count in notes.items():
                notes_formatted[denom] = {
                    "count": count,
                    "subtotal": float(denom) * count
                }
        
        html_content = template.render(
            seq_number=seq_number,
            business_date=business_date,
            created_at=created_at,
            period_start=period_start,
            period_end=period_end,
            receipt_min=receipt_min,
            receipt_max=receipt_max,
            cash_sales_count=cash_sales_count,
            cash_sales_net=f"{cash_sales_net:.2f}",
            cash_sales_tax=f"{cash_sales_tax:.2f}",
            cash_sales_gross=f"{cash_sales_gross:.2f}",
            balance_sales_count=balance_sales_count,
            balance_sales_net=f"{balance_sales_net:.2f}",
            balance_sales_tax=f"{balance_sales_tax:.2f}",
            balance_sales_gross=f"{balance_sales_gross:.2f}",
            recharge_count=recharge_count,
            recharge_total=f"{recharge_total:.2f}",
            total_items_count=total_items_count,
            total_net=f"{total_net:.2f}",
            total_tax=f"{total_tax:.2f}",
            total_gross=f"{total_gross:.2f}",
            cash_revenue=f"{cash_revenue:.2f}",
            guthaben_net=f"{guthaben_net:.2f}",
            guthaben_gross=f"{guthaben_gross:.2f}",
            total_revenue=f"{total_revenue:.2f}",
            categories_breakdown=categories_breakdown or {},
            customer_groups=customer_groups or {},
            customers=customers or {},
            stornos=stornos or [],
            coins=coins_formatted,
            notes=notes_formatted,
            coins_total=f"{coins_total:.2f}",
            notes_total=f"{notes_total:.2f}",
            cash_counted=f"{cash_counted:.2f}",
            cash_calculated=f"{cash_calculated:.2f}",
            cash_difference=f"{cash_difference:.2f}",
        )
        
        return html_content
    
    @staticmethod
    def render_email_html(
        seq_number: int,
        business_date: str,
        created_at: str,
        period_start: str,
        period_end: str,
        receipt_min: int,
        receipt_max: int,
        cash_sales_count: int,
        cash_sales_gross: float,
        balance_sales_count: int,
        balance_sales_gross: float,
        recharge_count: int,
        recharge_total: float,
        total_items_count: int,
        total_gross: float,
        guthaben_gross: float,
        categories_breakdown: dict = None,
        **kwargs
    ) -> str:
        """
        Render Z-Bon as email-optimized HTML
        
        Uses table-based layout for maximum email client compatibility
        
        Returns:
            Email-safe HTML string
        """
        template_str = ZBonHTMLExporter.get_email_template()
        template = Template(template_str)
        
        html_content = template.render(
            seq_number=seq_number,
            business_date=business_date,
            created_at=created_at,
            period_start=period_start,
            period_end=period_end,
            receipt_min=receipt_min,
            receipt_max=receipt_max,
            cash_sales_count=cash_sales_count,
            cash_sales_gross=f"{cash_sales_gross:.2f}",
            balance_sales_count=balance_sales_count,
            balance_sales_gross=f"{balance_sales_gross:.2f}",
            recharge_count=recharge_count,
            recharge_total=f"{recharge_total:.2f}",
            total_items_count=total_items_count,
            total_gross=f"{total_gross:.2f}",
            guthaben_gross=f"{guthaben_gross:.2f}",
            categories_breakdown=categories_breakdown or {},
        )
        
        return html_content
    
    @staticmethod
    def export_pdf(html_content: str, filename: str = None) -> BytesIO:
        """
        Export HTML to PDF using WeasyPrint
        
        Args:
            html_content: HTML string to convert
            filename: Optional filename for the PDF
            
        Returns:
            BytesIO object containing the PDF
            
        Raises:
            RuntimeError if WeasyPrint is not available
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                "WeasyPrint is not installed. "
                "Install it with: pip install weasyprint"
            )
        
        try:
            # Convert HTML to PDF
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            # Return as BytesIO for file transmission
            pdf_file = BytesIO(pdf_bytes)
            pdf_file.seek(0)
            
            logger.info(f"✓ PDF generated successfully ({len(pdf_bytes)} bytes)")
            return pdf_file
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise RuntimeError(f"PDF generation failed: {str(e)}")
    
    @staticmethod
    def export_pdf_to_file(html_content: str, output_path: str) -> bool:
        """
        Export HTML to PDF file
        
        Args:
            html_content: HTML string to convert
            output_path: Path where PDF should be saved
            
        Returns:
            True if successful, False otherwise
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint not available")
            return False
        
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            
            logger.info(f"✓ PDF saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving PDF: {str(e)}")
            return False
