"""Email service for sending Z-Bon and notifications"""
import logging
import socket
import smtplib
import ssl
import time
from html import escape
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.database import SessionLocal
from app.services.app_settings_service import AppSettingsService

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    def _subject_suffix(config: dict) -> str:
        suffix = (config.get("email_subject_suffix") or "").strip()
        return f" - {suffix}" if suffix else ""

    @classmethod
    def _report_subject(cls, base: str, config: dict | None = None) -> str:
        current_config = config or cls._load_email_settings()
        return f"{base}{cls._subject_suffix(current_config)}"

    @staticmethod
    def _load_email_settings() -> dict:
        db = SessionLocal()
        try:
            return AppSettingsService(db).get_email_settings()
        finally:
            db.close()

    @classmethod
    def is_enabled(cls) -> bool:
        return bool(cls._load_email_settings().get("email_enabled"))

    @classmethod
    def send_email(
        cls,
        to_address: str,
        subject: str,
        body: str,
        html_body: str = None,
        attachments: list = None,
    ) -> bool:
        config = cls._load_email_settings()
        if not config.get("email_enabled"):
            logger.warning("Email service is disabled")
            return False

        sender = (config.get("email_sender") or "").strip()
        smtp_host = (config.get("smtp_host") or "").strip()
        if not sender or not smtp_host:
            logger.warning("Email settings incomplete: sender or SMTP host missing")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = to_address
            msg.attach(MIMEText(body, 'plain'))

            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

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

            with cls._open_smtp_client(config) as server:
                server.ehlo()

                if cls._uses_starttls(config):
                    server.starttls()
                    server.ehlo()

                username = (config.get("smtp_username") or "").strip()
                password = config.get("smtp_password") or ""
                if username and password:
                    server.login(username, password)

                server.send_message(msg)

            logger.info("Email sent to %s", to_address)
            return True
        except Exception as e:
            logger.error("Failed to send email: %s", str(e))
            return False

    @staticmethod
    def _uses_starttls(config: dict) -> bool:
        smtp_use_tls = bool(config.get("smtp_use_tls", True))
        smtp_port = int(config.get("smtp_port") or 587)
        # Port 465 typically expects implicit TLS (SMTP_SSL), not STARTTLS upgrade.
        return smtp_use_tls and smtp_port != 465

    @staticmethod
    def _open_smtp_client(config: dict, timeout: int = 10):
        smtp_host = (config.get("smtp_host") or "").strip()
        smtp_port = int(config.get("smtp_port") or 587)
        smtp_use_tls = bool(config.get("smtp_use_tls", True))

        if smtp_use_tls and smtp_port == 465:
            return smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        return smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)

    @staticmethod
    def _connection_hint_for_host(host: str) -> str:
        if host in {"localhost", "127.0.0.1"}:
            return "Hinweis: In Docker verweist localhost auf den Container selbst. Nutze den externen SMTP-Hostnamen."
        return ""

    @staticmethod
    def test_smtp_connection(config: dict) -> tuple[bool, str]:
        sender = (config.get("email_sender") or "").strip()
        smtp_host = (config.get("smtp_host") or "").strip()
        smtp_port = int(config.get("smtp_port") or 587)
        smtp_use_tls = bool(config.get("smtp_use_tls", True))
        username = (config.get("smtp_username") or "").strip()
        password = config.get("smtp_password") or ""

        if not sender:
            return False, "Absender fehlt"
        if not smtp_host:
            return False, "SMTP-Host fehlt"
        if bool(username) != bool(password):
            return False, "SMTP-Benutzer und SMTP-Passwort muessen gemeinsam gesetzt sein"

        stage = "init"
        resolved_targets = []
        tcp_probe_ms = None
        try:
            logger.info(
                "SMTP test started: host=%s port=%s tls=%s auth=%s sender=%s",
                smtp_host,
                smtp_port,
                smtp_use_tls,
                bool(username and password),
                bool(sender),
            )

            stage = "dns_resolve"
            dns_started_at = time.monotonic()
            resolved = socket.getaddrinfo(smtp_host, smtp_port, type=socket.SOCK_STREAM)
            resolved_targets = sorted({entry[4][0] for entry in resolved if entry and entry[4]})
            dns_elapsed_ms = int((time.monotonic() - dns_started_at) * 1000)
            logger.info(
                "SMTP test DNS resolved: host=%s resolved_count=%s duration_ms=%s targets=%s",
                smtp_host,
                len(resolved_targets),
                dns_elapsed_ms,
                ", ".join(resolved_targets[:5]) if resolved_targets else "none",
            )

            stage = "tcp_probe"
            tcp_started_at = time.monotonic()
            with socket.create_connection((smtp_host, smtp_port), timeout=6):
                pass
            tcp_probe_ms = int((time.monotonic() - tcp_started_at) * 1000)
            logger.info(
                "SMTP test TCP probe successful: host=%s port=%s duration_ms=%s",
                smtp_host,
                smtp_port,
                tcp_probe_ms,
            )

            stage = "smtp_connect"
            with EmailService._open_smtp_client(config, timeout=12) as server:
                stage = "ehlo_initial"
                code, _ = server.ehlo()
                logger.info("SMTP test EHLO response: code=%s", code)

                if EmailService._uses_starttls(config):
                    stage = "starttls"
                    server.starttls()
                    logger.info("SMTP test STARTTLS established")

                    stage = "ehlo_after_starttls"
                    server.ehlo()

                if username and password:
                    stage = "auth_login"
                    server.login(username, password)
                    logger.info("SMTP test AUTH login successful")

                stage = "noop"
                server.noop()

            logger.info(
                "SMTP test successful: host=%s port=%s tls=%s targets=%s tcp_probe_ms=%s",
                smtp_host,
                smtp_port,
                smtp_use_tls,
                ", ".join(resolved_targets[:5]) if resolved_targets else "none",
                tcp_probe_ms,
            )
            return True, "SMTP-Verbindung erfolgreich getestet"
        except socket.gaierror as e:
            logger.error("SMTP test failed at %s: DNS resolution error for host=%s (%s)", stage, smtp_host, str(e))
            return False, f"SMTP-Verbindung fehlgeschlagen ({stage}): Host nicht aufloesbar ({smtp_host})"
        except (TimeoutError, socket.timeout) as e:
            logger.error(
                "SMTP test failed at %s: timeout host=%s port=%s targets=%s tcp_probe_ms=%s error_type=%s message=%s",
                stage,
                smtp_host,
                smtp_port,
                ", ".join(resolved_targets[:5]) if resolved_targets else "none",
                tcp_probe_ms,
                type(e).__name__,
                str(e),
            )
            return False, (
                f"SMTP-Verbindung fehlgeschlagen ({stage}): Zeitueberschreitung bei {smtp_host}:{smtp_port}. "
                "Pruefe Host, Port, TLS-Modus, Firewall und Docker-Netzwerk."
            )
        except ConnectionRefusedError as e:
            logger.error("SMTP test failed at %s: connection refused host=%s port=%s (%s)", stage, smtp_host, smtp_port, str(e))
            return False, (
                f"SMTP-Verbindung fehlgeschlagen ({stage}): Verbindung verweigert bei {smtp_host}:{smtp_port}. "
                "Pruefe Port und SMTP-Server."
            )
        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP test failed at %s: authentication failed (%s)", stage, str(e))
            return False, f"SMTP-Verbindung fehlgeschlagen ({stage}): Authentifizierung fehlgeschlagen"
        except smtplib.SMTPNotSupportedError as e:
            logger.error("SMTP test failed at %s: operation not supported (%s)", stage, str(e))
            return False, (
                f"SMTP-Verbindung fehlgeschlagen ({stage}): STARTTLS oder AUTH wird vom Server nicht unterstuetzt"
            )
        except smtplib.SMTPConnectError as e:
            logger.error("SMTP test failed at %s: SMTP connect error (%s)", stage, str(e))
            return False, f"SMTP-Verbindung fehlgeschlagen ({stage}): SMTP-Connect-Fehler"
        except smtplib.SMTPServerDisconnected as e:
            logger.error(
                "SMTP test failed at %s: server disconnected host=%s port=%s targets=%s tcp_probe_ms=%s error_type=%s message=%s",
                stage,
                smtp_host,
                smtp_port,
                ", ".join(resolved_targets[:5]) if resolved_targets else "none",
                tcp_probe_ms,
                type(e).__name__,
                str(e),
            )
            hint = EmailService._connection_hint_for_host(smtp_host)
            return False, (
                f"SMTP-Verbindung fehlgeschlagen ({stage}): Server hat die Verbindung unerwartet geschlossen. "
                f"Wenn Port 465 verwendet wird, pruefe SSL/TLS-Konfiguration. {hint}".strip()
            )
        except ssl.SSLError as e:
            logger.error("SMTP test failed at %s: TLS/SSL error (%s)", stage, str(e))
            return False, f"SMTP-Verbindung fehlgeschlagen ({stage}): TLS/SSL-Fehler"
        except Exception as e:
            logger.exception("SMTP test failed at %s: unexpected error", stage)
            return False, f"SMTP-Verbindung fehlgeschlagen ({stage}): {str(e)}"

    @classmethod
    def send_zbon_email(cls, recipient: str, zbon_content: str, date: str) -> bool:
        config = cls._load_email_settings()
        subject = cls._report_subject(f"Kassenbericht für {date}", config)
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
        return cls.send_email(recipient, subject, body, html_body=html_body, attachments=attachments)

    @classmethod
    def send_zbon_html_email(
        cls,
        recipient: str,
        html_zbon: str,
        date: str,
        seq_number: int = None,
        include_pdf: bytes = None,
        use_email_template: bool = True,
        informational_only: bool = False,
    ) -> bool:
        config = cls._load_email_settings()
        if informational_only:
            subject = cls._report_subject(f"Tagesupdate Kassenbewegungen - {date}", config)
            body = (
                f"Tagesupdate fuer {date}. Dieser Versand ersetzt keinen manuell erstellten "
                "Kassenbericht mit Kassenzaehlung und Pruefer."
            )
            intro_line = (
                f"Anbei erhalten Sie das Tagesupdate fuer <strong>{date}</strong>. "
                "Dies ist eine reine Information ueber die Tagesbewegung."
            )
            footer_line = (
                "Dieses Tagesupdate ersetzt keinen manuell erstellten Kassenbericht "
                "mit Kassenzaehlung und Sichtkontrolle."
            )
        else:
            base_subject = f"Kassenbericht {seq_number or date} - {date}" if seq_number else f"Kassenbericht für {date}"
            subject = cls._report_subject(base_subject, config)
            body = f"Kassenbericht für {date}"
            intro_line = f"Anbei erhalten Sie den Kassenbericht fuer <strong>{date}</strong>."
            footer_line = "Diese E-Mail wurde automatisch generiert. Bitte speichern Sie diesen Kassenbericht fuer Ihre Unterlagen."

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
                <p>{intro_line}</p>
      </div>
      <div class="zbon-container">
        {html_zbon}
      </div>
      <div class="footer">
                <p>{footer_line}</p>
      </div>
    </div>
  </body>
</html>
"""
        attachments = []
        if include_pdf:
            filename = f"Kassenbericht_{seq_number}_{date}.pdf" if seq_number else f"Kassenbericht_{date}.pdf"
            attachments.append((filename, include_pdf, "application/pdf"))
        return cls.send_email(recipient, subject, body, html_body=html_body, attachments=attachments)

    @classmethod
    def send_critical_stock_email(cls, recipient: str, low_stock_products: list[dict]) -> bool:
        if not low_stock_products:
            return True

        config = cls._load_email_settings()
        subject = cls._report_subject("Kritischer Lagerbestand", config)
        body_lines = [
            "Die folgenden Artikel haben den Mindestbestand unterschritten:",
            "",
        ]
        for product in low_stock_products:
            body_lines.append(
                f"- {product['name']}: Ist {product['stock_quantity']}, Mindestbestand {product['minimum_stock_quantity']}"
            )
        body = "\n".join(body_lines)

        rows = "".join(
            f"""
            <tr>
              <td style="padding:10px 12px;border-bottom:1px solid #e2e8f0;">{escape(str(product['name']))}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #e2e8f0;text-align:right;">{product['stock_quantity']}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #e2e8f0;text-align:right;">{product['minimum_stock_quantity']}</td>
            </tr>
            """
            for product in low_stock_products
        )
        html_body = f"""
<html>
  <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
    <div style="max-width:680px;margin:24px auto;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="padding:18px 22px;border-bottom:1px solid #e2e8f0;">
        <h2 style="margin:0;font-size:18px;font-weight:700;">Benachrichtigung kritischer Lagerbestand</h2>
      </div>
      <div style="padding:18px 22px;">
        <p style="margin:0 0 14px 0;font-size:14px;line-height:1.5;">
          Folgende Artikel liegen unter dem konfigurierten Mindestbestand:
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f1f5f9;">
              <th style="text-align:left;padding:10px 12px;">Artikel</th>
              <th style="text-align:right;padding:10px 12px;">Ist-Bestand</th>
              <th style="text-align:right;padding:10px 12px;">Mindestbestand</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    </div>
  </body>
</html>
"""
        return cls.send_email(recipient, subject, body, html_body=html_body)
