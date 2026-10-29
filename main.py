"""
Lyfta Weekly Workout Digest to Gmail.
Fetches workout logs from the Lyfta API for the past 7 days, formats a structured
summary (text and HTML), and sends it to a Gmail address via SMTP.
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import smtplib
import requests

# Cargar variables de entorno desde .env si existe (útil para desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Constantes de configuración
LYFTA_API_BASE_URL = "https://my.lyfta.app/community/api/v1/workouts"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def get_required_env_vars() -> dict:
    """
    Valida y recupera las variables de entorno requeridas.
    Termina el proceso si falta alguna variable.
    """
    lyfta_key = os.getenv("LYFTA_API_KEY") or os.getenv("LYFTA")
    gmail_addr = os.getenv("GMAIL_ADDRESS")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    missing = []
    if not lyfta_key or not lyfta_key.strip():
        missing.append("LYFTA_API_KEY (o LYFTA)")
    if not gmail_addr or not gmail_addr.strip():
        missing.append("GMAIL_ADDRESS")
    if not gmail_pass or not gmail_pass.strip():
        missing.append("GMAIL_APP_PASSWORD")

    if missing:
        logger.error("Faltan las siguientes variables de entorno requeridas: %s", ", ".join(missing))
        sys.exit(1)

    return {
        "LYFTA_API_KEY": lyfta_key.strip(),
        "GMAIL_ADDRESS": gmail_addr.strip(),
        "GMAIL_APP_PASSWORD": gmail_pass.strip().replace(" ", ""),
    }


def fetch_workouts(api_key: str, from_date_iso: str, to_date_iso: str) -> list:
    """
    Consulta la API de Lyfta para obtener los entrenamientos entre dos fechas.
    Retorna una lista de entrenamientos.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "LyftaWorkoutDigestBot/1.0"
    }

    params = {
        "from": from_date_iso,
        "to": to_date_iso
    }

    logger.info("Consultando la API de Lyfta (%s a %s)...", from_date_iso, to_date_iso)

    try:
        response = requests.get(
            LYFTA_API_BASE_URL,
            headers=headers,
            params=params,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        logger.error("Error de conexión al consultar la API de Lyfta: %s", e)
        raise

    if response.status_code == 401:
        logger.error("Error 401 No Autorizado: LYFTA_API_KEY no es válida o expiró.")
        response.raise_for_status()

    if not response.ok:
        logger.error(
            "La API de Lyfta respondió con código de estado %s: %s",
            response.status_code,
            response.text
        )
        response.raise_for_status()

    payload = response.json()

    # Normalizar respuesta (la API puede retornar directamente una lista o un dict con clave 'data' / 'workouts')
    if isinstance(payload, list):
        workouts = payload
    elif isinstance(payload, dict):
        workouts = payload.get("data") or payload.get("workouts") or []
    else:
        logger.warning("Formato de respuesta inesperado de la API: %s", type(payload))
        workouts = []

    logger.info("Se encontraron %d entrenamiento(s) en el período.", len(workouts))
    return workouts


def parse_workouts(workouts_raw: list) -> list:
    """
    Estructura y calcula métricas clave para cada entrenamiento:
    - Título de la rutina
    - Fecha
    - Volumen total (kg)
    - Duración
    - Lista de ejercicios con sus respectivas series y repeticiones
    """
    parsed_workouts = []

    for item in workouts_raw:
        title = item.get("title") or item.get("name") or "Entrenamiento sin título"
        date_str = item.get("workout_perform_date") or item.get("date") or item.get("created_at") or ""
        duration_sec = item.get("duration_seconds")
        api_total_volume = item.get("total_volume")

        calculated_volume = 0.0
        exercises_list = []

        raw_exercises = item.get("exercises") or []
        for ex in raw_exercises:
            ex_name = ex.get("name") or "Ejercicio"
            ex_sets = []

            for s in ex.get("sets", []):
                weight = float(s.get("weight") or 0.0)
                reps = int(s.get("reps") or 0)
                set_type = s.get("set_type", "working")
                set_volume = weight * reps
                calculated_volume += set_volume

                ex_sets.append({
                    "set_index": s.get("set_index", len(ex_sets) + 1),
                    "set_type": set_type,
                    "weight": weight,
                    "reps": reps,
                    "rpe": s.get("rpe"),
                    "volume": set_volume
                })

            exercises_list.append({
                "name": ex_name,
                "sets": ex_sets,
                "total_sets": len(ex_sets)
            })

        # Usar el volumen de la API si viene provisto, sino el calculado
        total_volume = float(api_total_volume) if api_total_volume is not None else calculated_volume

        parsed_workouts.append({
            "title": title,
            "date": date_str,
            "duration_seconds": duration_sec,
            "total_volume": round(total_volume, 2),
            "exercises": exercises_list
        })

    return parsed_workouts


def format_duration(seconds: int | None) -> str:
    """Formatea segundos en formato legible Xh Ym."""
    if not seconds:
        return "N/A"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def build_email_contents(
    parsed_workouts: list,
    from_date_str: str,
    to_date_str: str
) -> tuple[str, str]:
    """
    Genera el contenido del correo en formato texto plano y HTML responsive.
    """
    total_workouts = len(parsed_workouts)
    grand_total_volume = sum(w["total_volume"] for w in parsed_workouts)
    total_exercises_count = sum(len(w["exercises"]) for w in parsed_workouts)

    # -----------------------------
    # 1. VERSIÓN TEXTO PLANO
    # -----------------------------
    text_lines = [
        "=" * 60,
        " RESUMEN SEMANAL DE ENTRENAMIENTOS (LYFTA)",
        f" Período: {from_date_str} al {to_date_str}",
        "=" * 60,
        f"- Entrenamientos completados: {total_workouts}",
        f"- Volumen total movido: {grand_total_volume:,.1f} kg",
        f"- Ejercicios realizados: {total_exercises_count}",
        "-" * 60,
    ]

    if total_workouts == 0:
        text_lines.append("\nNo se registraron entrenamientos en los últimos 7 días.")
    else:
        for idx, w in enumerate(parsed_workouts, 1):
            text_lines.append(f"\n[{idx}] {w['title']}")
            if w['date']:
                text_lines.append(f"    Fecha: {w['date']}")
            text_lines.append(f"    Duración: {format_duration(w['duration_seconds'])}")
            text_lines.append(f"    Volumen: {w['total_volume']:,.1f} kg")
            text_lines.append("    Detalle de ejercicios:")

            for ex in w["exercises"]:
                sets_summary = ", ".join(
                    f"{s['reps']}x{s['weight']}kg" for s in ex["sets"]
                ) or "Sin series"
                text_lines.append(f"      • {ex['name']}: {sets_summary}")

    text_lines.append("\n" + "=" * 60)
    text_lines.append("Enviado automáticamente mediante CI/CD.")
    text_content = "\n".join(text_lines)

    # -----------------------------
    # 2. VERSIÓN HTML RESPONSIVE
    # -----------------------------
    cards_html = ""
    if total_workouts == 0:
        cards_html = """
        <div style="background-color: #f8f9fa; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 24px; text-align: center; color: #64748b; margin: 20px 0;">
            <p style="margin: 0; font-size: 16px;">No se registraron entrenamientos en los últimos 7 días.</p>
            <p style="margin: 8px 0 0 0; font-size: 13px;">¡Buen momento para planificar la próxima semana!</p>
        </div>
        """
    else:
        for w in parsed_workouts:
            exercises_rows = ""
            for ex in w["exercises"]:
                sets_badges = "".join(
                    f'<span style="display:inline-block; background-color:#eff6ff; color:#1d4ed8; font-size:12px; padding:3px 8px; border-radius:4px; margin:2px 4px 2px 0;">'
                    f'{s["reps"]} reps @ {s["weight"]}kg'
                    f'</span>'
                    for s in ex["sets"]
                ) or '<span style="color:#94a3b8; font-size:12px;">Sin series registradas</span>'

                exercises_rows += f"""
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 10px 12px; font-weight: 600; color: #1e293b; font-size: 14px; vertical-align: top; width: 40%;">{ex['name']}</td>
                    <td style="padding: 10px 12px; font-size: 13px; color: #334155; vertical-align: top;">{sets_badges}</td>
                </tr>
                """

            cards_html += f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #ffffff; padding: 14px 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <h3 style="margin: 0; font-size: 17px; font-weight: 700; letter-spacing: -0.3px;">{w['title']}</h3>
                        <span style="font-size: 13px; color: #94a3b8; margin-top: 4px;">{w['date'][:10] if w['date'] else ''}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 13px; color: #cbd5e1;">
                        <span>⏱ Duración: <strong>{format_duration(w['duration_seconds'])}</strong></span>
                        <span style="margin: 0 10px;">•</span>
                        <span>📊 Volumen: <strong>{w['total_volume']:,.1f} kg</strong></span>
                    </div>
                </div>
                <div style="padding: 12px 16px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 2px solid #e2e8f0; color: #64748b; font-size: 12px; text-transform: uppercase;">
                                <th style="padding: 8px 12px;">Ejercicio</th>
                                <th style="padding: 8px 12px;">Series y Repeticiones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {exercises_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resumen Semanal de Entrenamientos</title>
    </head>
    <body style="margin:0; padding:20px; background-color:#f1f5f9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#0f172a;">
        <div style="max-width: 680px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            
            <!-- HEADER -->
            <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 28px 24px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">🏋️ Resumen Semanal Lyfta</h1>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #e0f2fe; opacity: 0.95;">
                    Período: {from_date_str} &mdash; {to_date_str}
                </p>
            </div>

            <!-- METRIC CARDS -->
            <div style="padding: 20px 24px 10px 24px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="width: 33.3%; padding: 8px; text-align: center;">
                            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px;">
                                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Sesiones</div>
                                <div style="font-size: 22px; font-weight: 800; color: #0284c7; margin-top: 4px;">{total_workouts}</div>
                            </div>
                        </td>
                        <td style="width: 33.3%; padding: 8px; text-align: center;">
                            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px;">
                                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Volumen Total</div>
                                <div style="font-size: 22px; font-weight: 800; color: #0f172a; margin-top: 4px;">{grand_total_volume:,.0f} <span style="font-size: 12px; font-weight: normal; color: #64748b;">kg</span></div>
                            </div>
                        </td>
                        <td style="width: 33.3%; padding: 8px; text-align: center;">
                            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 8px;">
                                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Ejercicios</div>
                                <div style="font-size: 22px; font-weight: 800; color: #10b981; margin-top: 4px;">{total_exercises_count}</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- WORKOUT DETAILS -->
            <div style="padding: 24px;">
                <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #1e293b; font-weight: 700;">Detalle de Rutinas</h2>
                {cards_html}
            </div>

            <!-- FOOTER -->
            <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8;">
                Generado automáticamente por tu pipeline CI/CD en la nube &bull; Lyfta API Sync
            </div>
        </div>
    </body>
    </html>
    """

    return text_content, html_content


def send_email(
    gmail_address: str,
    gmail_app_password: str,
    subject: str,
    text_content: str,
    html_content: str
) -> None:
    """
    Envía el resumen por correo electrónico a través de smtp.gmail.com usando TLS en el puerto 587.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = gmail_address

    # Contenido principal en texto plano
    msg.set_content(text_content)

    # Alternativa en HTML con formato visual enriquecido
    msg.add_alternative(html_content, subtype="html")

    logger.info("Conectando con el servidor SMTP de Gmail (%s:%d)...", SMTP_SERVER, SMTP_PORT)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)
            logger.info("¡Correo enviado con éxito a %s!", gmail_address)
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            "Fallo de autenticación con Gmail. Verifica GMAIL_ADDRESS y "
            "que GMAIL_APP_PASSWORD sea una 'Contraseña de aplicación' válida (16 caracteres): %s",
            e
        )
        raise
    except Exception as e:
        logger.error("Error al enviar el correo por SMTP: %s", e)
        raise


def main() -> None:
    """
    Función principal que coordina la extracción, procesamiento y envío.
    """
    logger.info("Iniciando proceso de extracción y resumen semanal de entrenamientos...")

    # 1. Validar variables de entorno
    config = get_required_env_vars()

    # 2. Calcular rango de fechas (últimos 7 días en ISO 8601 UTC)
    now_utc = datetime.now(timezone.utc)
    seven_days_ago_utc = now_utc - timedelta(days=7)

    # Formato ISO requerido por la API de Lyfta
    from_iso = seven_days_ago_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info("Ventana de tiempo: %s -> %s", from_iso, to_iso)

    # 3. Consultar entrenamientos desde la API de Lyfta
    workouts_raw = fetch_workouts(
        api_key=config["LYFTA_API_KEY"],
        from_date_iso=from_iso,
        to_date_iso=to_iso
    )

    # 4. Procesar y calcular volumen/series/repeticiones
    parsed_workouts = parse_workouts(workouts_raw)

    # 5. Generar formato de correo
    from_readable = seven_days_ago_utc.strftime("%d/%m/%Y")
    to_readable = now_utc.strftime("%d/%m/%Y")
    subject = f"🏋️ Resumen Semanal Lyfta ({from_readable} - {to_readable})"

    text_body, html_body = build_email_contents(
        parsed_workouts=parsed_workouts,
        from_date_str=from_readable,
        to_date_str=to_readable
    )

    # 6. Enviar correo vía Gmail SMTP
    send_email(
        gmail_address=config["GMAIL_ADDRESS"],
        gmail_app_password=config["GMAIL_APP_PASSWORD"],
        subject=subject,
        text_content=text_body,
        html_content=html_body
    )

    logger.info("Proceso completado exitosamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error crítico durante la ejecución: %s", exc)
        sys.exit(1)
