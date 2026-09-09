import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    contact_email = os.getenv("CONTACT_EMAIL")

    if not all((smtp_host, smtp_user, smtp_password, contact_email)):
        return jsonify(error="O envio de e-mail ainda não está configurado no servidor."), 500

    email = EmailMessage()
    email["Subject"] = f"Solicitação de serviço - {service} | Cobbyte"
    email["From"] = smtp_user
    email["To"] = contact_email
    email["Reply-To"] = sender_email
    email.set_content(
        f"Nome: {name}\n"
        f"E-mail: {sender_email}\n"
        f"Tipo de serviço: {service}\n\n"
        f"Descrição:\n{message}"
    )

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