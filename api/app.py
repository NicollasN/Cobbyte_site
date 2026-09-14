import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def normalize_env_value(value):
    if value is None:
        return ""
    return str(value).strip().replace(" ", "").replace("\n", "").replace("\r", "")


def has_email_config(smtp_host, smtp_port, smtp_user, smtp_password, contact_email):
    return all(
        (
            normalize_env_value(smtp_host),
            normalize_env_value(smtp_port),
            normalize_env_value(smtp_user),
            normalize_env_value(smtp_password),
            normalize_env_value(contact_email),
        )
    )


def build_email_html(name, sender_email, service, message):
    return f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
</head>
<body style="margin:0; padding:0; background-color:#f4f4f7; font-family: Arial, Helvetica, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7; padding: 30px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">

          <!-- Banner -->
          <tr>
            <td style="background-color:#1a1a1a; padding: 24px 32px; text-align:center;">
              <img src="cid:banner_cobbyte"
                   alt="Cobbyte"
                   width="180"
                   style="display:block; margin:0 auto; max-width:180px; height:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 32px;">
              <h2 style="margin:0 0 20px; color:#1a1a2e; font-size:18px;">Nova solicitação de serviço</h2>

              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                <tr>
                  <td style="padding: 8px 0; color:#666; font-size:14px; width:140px;"><strong>Nome:</strong></td>
                  <td style="padding: 8px 0; color:#1a1a2e; font-size:14px;">{name}</td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; color:#666; font-size:14px;"><strong>E-mail:</strong></td>
                  <td style="padding: 8px 0; font-size:14px;">
                    <a href="mailto:{sender_email}" style="color:#7c5cff; text-decoration:none;">{sender_email}</a>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; color:#666; font-size:14px;"><strong>Tipo de serviço:</strong></td>
                  <td style="padding: 8px 0; font-size:14px;">
                    <span style="background-color:#f0ecff; color:#7c5cff; padding: 4px 10px; border-radius: 12px; font-size:12px; font-weight:bold;">{service}</span>
                  </td>
                </tr>
              </table>

              <div style="background-color:#f9f9fb; border-left: 4px solid #7c5cff; padding: 16px 20px; border-radius: 4px;">
                <p style="margin:0 0 6px; color:#666; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Descrição</p>
                <p style="margin:0; color:#1a1a2e; font-size:14px; line-height:1.5;">{message}</p>
              </div>

              <div style="margin-top: 28px;">
                <a href="mailto:{sender_email}" style="display:inline-block; background-color:#7c5cff; color:#ffffff; text-decoration:none; padding: 12px 24px; border-radius: 6px; font-size:14px; font-weight:bold;">Responder ao cliente</a>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color:#f9f9fb; border-top:1px solid #eee;">
              <p style="margin:0; color:#999; font-size:12px;">Este e-mail foi gerado automaticamente pelo site da Cobbyte.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

@app.after_request
def allow_local_frontend(response):
    origin = request.headers.get("Origin")
    if origin in {"http://127.0.0.1:5501", "http://localhost:5501"}:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    sender_email = str(data.get("email", "")).strip()
    service = str(data.get("service", "")).strip()
    message = str(data.get("message", "")).strip()

    if not all((name, sender_email, service, message)):
        return jsonify(error="Preencha todos os campos obrigatórios."), 400

    if len(name) > 120 or len(sender_email) > 254 or len(service) > 120 or len(message) > 5000:
        return jsonify(error="Um dos campos excede o tamanho permitido."), 400

    smtp_host = normalize_env_value(os.getenv("SMTP_HOST"))
    smtp_port = int(normalize_env_value(os.getenv("SMTP_PORT", "587")) or "587")
    smtp_user = normalize_env_value(os.getenv("SMTP_USER"))
    smtp_password = normalize_env_value(os.getenv("SMTP_PASSWORD"))
    contact_email = normalize_env_value(os.getenv("CONTACT_EMAIL"))

    if not has_email_config(smtp_host, smtp_port, smtp_user, smtp_password, contact_email):
        return jsonify(error="O envio de e-mail ainda não está configurado no servidor."), 500

    email = EmailMessage()
    email["Subject"] = f"Solicitação de serviço - {service} | Cobbyte"
    email["From"] = smtp_user
    email["To"] = contact_email
    email["Reply-To"] = sender_email

    # Versão texto simples (fallback)
    email.set_content(
        f"Nome: {name}\n"
        f"E-mail: {sender_email}\n"
        f"Tipo de serviço: {service}\n\n"
        f"Descrição:\n{message}"
    )

    # Versão HTML (preferida pela maioria dos clientes de e-mail)
    email.add_alternative(build_email_html(name, sender_email, service, message), subtype="html")

    # Embute o banner na parte HTML, referenciado via cid:banner_cobbyte
    banner_path = BASE_DIR / "api" / "assets" / "banner_cobbyte.png"
    try:
        with open(banner_path, "rb") as f:
            html_part = email.get_payload()[1]  # a parte "text/html" criada acima
            html_part.add_related(f.read(), maintype="image", subtype="png", cid="banner_cobbyte")
    except FileNotFoundError:
        app.logger.warning("Banner não encontrado em %s. E-mail será enviado sem imagem.", banner_path)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(email)
    except (OSError, smtplib.SMTPException):
        app.logger.exception("Falha ao enviar solicitação por e-mail")
        return jsonify(error="Não foi possível enviar a solicitação agora."), 502

    return jsonify(message="Solicitação enviada com sucesso.")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)