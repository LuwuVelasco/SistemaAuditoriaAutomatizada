"""Servicio de envío de email vía Gmail SMTP."""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List

from app.core.config import settings


_MIME_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf":  "application/pdf",
}

_MONTH_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _build_html(audit_name: str, attachments: List[dict]) -> str:
    now = datetime.now()
    date_str = f"{now.day} de {_MONTH_ES[now.month]} de {now.year}"

    rows = ""
    for att in attachments:
        ext = att["filename"].rsplit(".", 1)[-1].upper()
        rows += f"""
        <tr>
          <td style="padding:10px 16px;border-bottom:1px solid #1e293b;font-size:13px;color:#e2e8f0;">
            {att['label']}
          </td>
          <td style="padding:10px 16px;border-bottom:1px solid #1e293b;font-size:11px;font-family:monospace;color:#22d3ee;text-align:center;">
            {ext}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Reportes de Auditoría — COSFI</title>
</head>
<body style="margin:0;padding:0;background:#07070d;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#07070d;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0d0d18 0%,#111827 100%);
                        border:1px solid rgba(34,211,238,0.2);
                        border-radius:16px 16px 0 0;
                        padding:36px 40px 28px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <div style="display:inline-flex;align-items:center;gap:10px;
                                background:rgba(34,211,238,0.08);
                                border:1px solid rgba(34,211,238,0.25);
                                border-radius:8px;padding:8px 14px;">
                      <span style="font-family:monospace;font-size:18px;font-weight:700;
                                   letter-spacing:3px;color:#f1f5f9;">COSFI</span>
                    </div>
                    <p style="margin:16px 0 0;font-size:11px;letter-spacing:2px;
                               text-transform:uppercase;color:#22d3ee;">
                      Plataforma de Auditoría con IA
                    </p>
                  </td>
                  <td align="right" style="vertical-align:top;">
                    <span style="font-size:11px;color:#475569;font-family:monospace;">{date_str}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="background:#0d0d18;
                        border-left:1px solid rgba(34,211,238,0.2);
                        border-right:1px solid rgba(34,211,238,0.2);
                        padding:32px 40px;">

              <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#f8fafc;line-height:1.3;">
                Reportes de Auditoría
              </h1>
              <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;">
                Se adjuntan los documentos generados para la auditoría
                <strong style="color:#94a3b8;">"{audit_name}"</strong>.
              </p>

              <!-- Divider -->
              <div style="height:1px;background:linear-gradient(90deg,rgba(34,211,238,0.3),transparent);
                           margin-bottom:24px;"></div>

              <!-- Files table -->
              <p style="margin:0 0 12px;font-size:11px;letter-spacing:1px;text-transform:uppercase;
                          color:#475569;font-weight:600;">Documentos adjuntos</p>
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="border:1px solid #1e293b;border-radius:10px;overflow:hidden;border-collapse:collapse;">
                <thead>
                  <tr style="background:#111827;">
                    <th style="padding:10px 16px;font-size:11px;text-transform:uppercase;letter-spacing:1px;
                                color:#475569;text-align:left;font-weight:600;">Documento</th>
                    <th style="padding:10px 16px;font-size:11px;text-transform:uppercase;letter-spacing:1px;
                                color:#475569;text-align:center;font-weight:600;width:70px;">Formato</th>
                  </tr>
                </thead>
                <tbody>{rows}
                </tbody>
              </table>

              <!-- Note -->
              <div style="margin-top:24px;padding:16px;background:rgba(34,211,238,0.05);
                           border:1px solid rgba(34,211,238,0.15);border-radius:10px;">
                <p style="margin:0;font-size:12px;color:#64748b;line-height:1.6;">
                  Los archivos adjuntos han sido generados automáticamente por COSFI.
                  Para consultas sobre el contenido, accede a la plataforma.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#070710;
                        border:1px solid rgba(34,211,238,0.2);
                        border-top:none;
                        border-radius:0 0 16px 16px;
                        padding:20px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <p style="margin:4px 0 0;font-size:10px;color:#1e293b;">
                      COSO 2013 · COBIT 2019 · RGSI-ASFI
                    </p>
                  </td>
                  <td align="right">
                    <span style="font-family:monospace;font-size:11px;color:#1e293b;letter-spacing:2px;">COSFI</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _send_sync(
    recipient: str,
    audit_name: str,
    attachments: List[dict],  # [{"filename": "...", "label": "...", "content": bytes}]
) -> None:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Reportes de Auditoría — {audit_name} | COSFI"
    msg["From"]    = settings.EMAIL_USER
    msg["To"]      = recipient

    msg.attach(MIMEText(_build_html(audit_name, attachments), "html", "utf-8"))

    for att in attachments:
        ext = att["filename"].rsplit(".", 1)[-1].lower()
        mime_type = _MIME_TYPES.get(ext, "application/octet-stream")
        main_type, sub_type = mime_type.split("/", 1)

        part = MIMEBase(main_type, sub_type)
        part.set_payload(att["content"])
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=att["filename"])
        msg.attach(part)

    user     = (settings.EMAIL_USER or "").strip()
    password = (settings.EMAIL_APP_PASSWORD or "").strip().replace(" ", "")
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(user, recipient, msg.as_bytes())


async def send_reports_email(
    recipient: str,
    audit_name: str,
    attachments: List[dict],
) -> None:
    await asyncio.to_thread(_send_sync, recipient, audit_name, attachments)
