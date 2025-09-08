#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de OMIE day-ahead.

Verifica que:
1) En db_sistema_electrico.omie_precios existan 23-25 registros para la fecha de mañana (zona='ES').
2) En db_Ncore.core_precios_omie_diario exista la fila agregada para esa fecha con precio_medio_mwh no nulo.

Exit codes:
- 0: OK
- 1: Falta day-ahead en origen
- 2: Falta agregado en Ncore
- 3: Error inesperado
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta
from email.message import EmailMessage
import smtplib

PSQL = "psql"
DB_ORIG = "db_sistema_electrico"
DB_CORE = "db_Ncore"
DB_USER = "postgres"

# Correo de destino por defecto (puede sobreescribirse con EMAIL_TO)
EMAIL_TO = os.getenv("EMAIL_TO", "a.diaz@energygreendata.com")


def send_email(subject: str, body: str) -> bool:
    """Envía email usando SMTP (si hay configuración en entorno) o fallback a 'mail' CLI.
    Variables de entorno soportadas para SMTP:
      SMTP_HOST, SMTP_PORT (por defecto 587), SMTP_USER, SMTP_PASS, SMTP_FROM (por defecto noreply@energygreendata.com)
      EMAIL_TO (opcional, ya fijado arriba por defecto)
    """
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("SMTP_FROM", "noreply@energygreendata.com")

    # Intento SMTP si hay host definido
    if host:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = EMAIL_TO
            msg.set_content(body)

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[WARN] SMTP fallo al enviar correo: {e}")

    # Fallback a 'mail' CLI si está disponible
    mail_bin = shutil.which("mail") or shutil.which("mailx")
    if mail_bin:
        try:
            p = subprocess.run(
                [mail_bin, "-s", subject, EMAIL_TO],
                input=body,
                text=True,
                capture_output=True,
            )
            if p.returncode == 0:
                return True
            print(f"[WARN] mail CLI devolvió código {p.returncode}: {p.stderr}")
        except Exception as e:
            print(f"[WARN] mail CLI fallo al enviar correo: {e}")

    print("[WARN] No se pudo enviar correo: configure SMTP_* o instale 'mail' CLI")
    return False


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def check_origen(tomorrow: str) -> tuple[bool, int, str]:
    sql = (
        "SELECT COUNT(*) FROM omie_precios "
        "WHERE zona='ES' AND fecha = DATE '%s';" % tomorrow
    )
    p = run([PSQL, "-U", DB_USER, "-d", DB_ORIG, "-tAc", sql])
    if p.returncode != 0:
        return False, -1, p.stderr.strip()
    try:
        n = int(p.stdout.strip() or 0)
    except Exception:
        n = 0
    ok = 23 <= n <= 25  # maneja DST
    return ok, n, ""


def check_ncore(tomorrow: str) -> tuple[bool, str]:
    sql = (
        "SELECT (precio_medio_mwh IS NOT NULL) AS ok FROM core_precios_omie_diario "
        "WHERE fecha = DATE '%s';" % tomorrow
    )
    p = run([PSQL, "-U", DB_USER, "-d", DB_CORE, "-tAc", sql])
    if p.returncode != 0:
        return False, p.stderr.strip()
    out = (p.stdout or "").strip()
    ok = out == "t" or out == "true"
    return ok, ""


def main():
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[MONITOR] Verificando OMIE day-ahead para {tomorrow}")

    ok_origen, n_rows, err = check_origen(tomorrow)
    if not ok_origen:
        if n_rows >= 0:
            msg = (
                f"Origen db_sistema_electrico.omie_precios incompleto para {tomorrow}: {n_rows} filas (esperado 23-25).\n"
                f"Acción: revisar ingesta 16:35 y disponibilidad REE."
            )
            print(f"[FAIL] {msg}")
            send_email(subject=f"[ALERTA] OMIE day-ahead incompleto {tomorrow}", body=msg)
            sys.exit(1)
        else:
            msg = f"Consulta a origen falló: {err}"
            print(f"[ERROR] {msg}")
            send_email(subject=f"[ALERTA] OMIE monitor error consulta origen {tomorrow}", body=msg)
            sys.exit(3)
    else:
        print(f"[OK] Origen: {n_rows} filas para {tomorrow}")

    ok_core, errc = check_ncore(tomorrow)
    if not ok_core:
        if errc:
            msg = f"Consulta Ncore falló: {errc}"
            print(f"[ERROR] {msg}")
            send_email(subject=f"[ALERTA] OMIE monitor error consulta Ncore {tomorrow}", body=msg)
            sys.exit(3)
        msg = (
            f"Ncore db_Ncore.core_precios_omie_diario: falta fila agregada para {tomorrow}.\n"
            f"Acción: ejecutar sync_omie_daily.sh (16:40) o lanzar manualmente el SQL de sincronización."
        )
        print(f"[FAIL] {msg}")
        send_email(subject=f"[ALERTA] OMIE day-ahead sin agregado Ncore {tomorrow}", body=msg)
        sys.exit(2)
    else:
        print(f"[OK] Ncore: core_precios_omie_diario tiene la fila de {tomorrow}")

    print("[MONITOR] Todo OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
