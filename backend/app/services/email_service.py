"""Email service for sending Z-Bon and notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if email is enabled"""
        return settings.EMAIL_ENABLED
    
    @staticmethod
    def send_email(
        to_address: str,
        subject: str,
        body: str,
        html_body: str = None,
        attachments: list = None,
    ) -> bool:
        """
        Send an email
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of tuples (filename, file_content, mime_type)
        
        Returns:
            True if successful, False otherwise
        """
        if not EmailService.is_enabled():
            logger.warning("Email service is disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_SENDER
            msg['To'] = to_address
            
            # Attach plain text part
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Attach files if provided
            if attachments:
                for filename, content, mime_type in attachments:
                    maintype, subtype = mime_type.split('/')
                    if maintype == 'text':
                        attachment = MIMEText(content, _subtype=subtype)
                    else:
                        attachment = MIMEBase(maintype, subtype)
                        attachment.set_payload(content)
                        encoders.encode_base64(attachment)
                    
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_address}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_zbon_email(recipient: str, zbon_content: str, date: str) -> bool:
        """
        Send Z-Bon via email
        
        Args:
            recipient: Email address
            zbon_content: Z-Bon content (text)
            date: Date of Z-Bon (YYYY-MM-DD)
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Kassenbericht für {date}"
        
        body = f"""
Anbei erhalten Sie den Kassenbericht für {date}.

---
{zbon_content}
---

Diese E-Mail wurde automatisch generiert.
"""
        
        html_body = f"""
<html>
  <body>
    <p>Anbei erhalten Sie den Kassenbericht für <strong>{date}</strong>.</p>
    <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px; font-family: monospace;">
{zbon_content}
    </pre>
    <p><small>Diese E-Mail wurde automatisch generiert.</small></p>
  </body>
</html>
"""
        
        attachments = [
            (f"Kassenbericht_{date}.txt", zbon_content, "text/plain")
        ]
        
        return EmailService.send_email(
            recipient,
            subject,
            body,
            html_body=html_body,
            attachments=attachments,
        )
    
    @staticmethod
    def send_zbon_html_email(
        recipient: str,
        html_zbon: str,
        date: str,
        seq_number: int = None,
        include_pdf: bytes = None,
        use_email_template: bool = True,
    ) -> bool:
        """
        Send Z-Bon via email with professional HTML formatting
        
        Args:
            recipient: Email address
            html_zbon: Z-Bon HTML content
            date: Date of Z-Bon (YYYY-MM-DD)
            seq_number: Z-Bon sequence number (optional)
            include_pdf: Optional PDF bytes for attachment
            use_email_template: If True, optimize HTML for email clients
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Kassenbericht {seq_number or date} - {date}" if seq_number else f"Kassenbericht für {date}"
        
        # Create responsive wrapper HTML with email-safe styles
        body = f"Kassenbericht für {date}"
        
        # Use the provided HTML directly (already rendered from template)
        html_body = f"""
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
      .container {{ max-width: 900px; margin: 20px auto; padding: 20px; }}
      .greeting {{ margin-bottom: 20px; }}
      .zbon-container {{ border: 1px solid #ddd; border-radius: 4px; padding: 20px; background: #fff; }}
      .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 0.9em; color: #666; }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="greeting">
        <p>Anbei erhalten Sie den Kassenbericht für <strong>{date}</strong>.</p>
      </div>
      
      <div class="zbon-container">
        {html_zbon}
      </div>
      
      <div class="footer">
        <p>Diese E-Mail wurde automatisch generiert. Bitte speichern Sie diesen Kassenbericht für Ihre Unterlagen.</p>
      </div>
    </div>
  </body>
</html>
"""
        
        attachments = []
        
        # Add PDF if provided
        if include_pdf:
            filename = f"Kassenbericht_{seq_number}_{date}.pdf" if seq_number else f"Kassenbericht_{date}.pdf"
            attachments.append((filename, include_pdf, "application/pdf"))
        
        return EmailService.send_email(
            recipient,
            subject,
            body,
            html_body=html_body,
            attachments=attachments,
        )
