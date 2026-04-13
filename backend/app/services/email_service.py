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
        subject = f"Z-Bon für {date}"
        
        body = f"""
Anbei erhalten Sie den Z-Bon für {date}.

---
{zbon_content}
---

Diese E-Mail wurde automatisch generiert.
"""
        
        html_body = f"""
<html>
  <body>
    <p>Anbei erhalten Sie den Z-Bon für <strong>{date}</strong>.</p>
    <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px; font-family: monospace;">
{zbon_content}
    </pre>
    <p><small>Diese E-Mail wurde automatisch generiert.</small></p>
  </body>
</html>
"""
        
        attachments = [
            (f"Z-Bon_{date}.txt", zbon_content, "text/plain")
        ]
        
        return EmailService.send_email(
            recipient,
            subject,
            body,
            html_body=html_body,
            attachments=attachments,
        )
