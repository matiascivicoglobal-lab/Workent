"""
Método de estudio para parcial.

Genera una Google Sheet con:
  - Plan: cronograma día a día hasta el examen
  - Temas: lista de temas con prioridad y estado
  - Sesiones: registro de sesiones de estudio

Uso:
    python study_method.py setup                    # crea la sheet y el plan base
    python study_method.py add-tema "Tema X" alta   # agrega un tema (prioridad: alta/media/baja)
    python study_method.py log-sesion               # registra una sesión completada
    python study_method.py status                   # muestra el progreso actual
"""

import sys
from datetime import date, datetime

from sheets_client import SheetsClient

# Fechas del plan (ajustar si cambia la fecha del parcial)
EXAM_DATE = date(2026, 4, 16)  # miércoles
TODAY = date.today()

SPREADSHEET_TITLE = f"Plan de Estudio - Parcial {EXAM_DATE.strftime('%d/%m/%Y')}"

SHEET_PLAN = "Plan"
SHEET_TEMAS = "Temas"
SHEET_SESIONES = "Sesiones"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def days_until_exam() -> int:
    return (EXAM_DATE - TODAY).days


def build_schedule() -> list[list]:
    """
    Genera el cronograma de estudio día a día.

    Estructura de 3 fases:
      Fase 1 - Mapeo (hoy):        listar todos los temas y evaluarse brevemente
      Fase 2 - Estudio activo:     estudiar tema por tema con técnica activa
      Fase 3 - Repaso final:       repasar apuntes, hacer preguntas de práctica
    """
    headers = ["Fecha", "Día", "Fase", "Sesión", "Actividad sugerida", "Estado"]

    schedule = [headers]

    days_left = days_until_exam()

    # Definición de fases según días disponibles
    phase_map = []
    if days_left >= 3:
        phase_map = [
            (0, "Fase 1 – Mapeo",       "Mañana",  "Listar todos los temas del parcial. Puntuar del 1-5 cuánto sabés de cada uno."),
            (0, "Fase 1 – Mapeo",       "Tarde",   "Repasar apuntes/diapositivas generales. Identificar los temas de mayor peso."),
            (1, "Fase 2 – Estudio activo", "Mañana", "Estudiar los 2-3 temas de mayor dificultad. Escribir resúmenes con tus palabras."),
            (1, "Fase 2 – Estudio activo", "Tarde",  "Continuar con los temas de dificultad media. Hacer ejercicios o preguntas de práctica."),
            (1, "Fase 2 – Estudio activo", "Noche",  "Revisar lo estudiado hoy. Cerrar con un auto-quiz de 10 preguntas."),
            (2, "Fase 3 – Repaso final",   "Mañana", "Repasar los temas difíciles con esquemas/flashcards. No estudiar temas nuevos."),
            (2, "Fase 3 – Repaso final",   "Tarde",  "Leer los resúmenes propios. Enfocarse en fórmulas, definiciones o fechas clave."),
            (2, "Fase 3 – Repaso final",   "Noche",  "Descansar. Dejar el material listo. Dormir bien es parte del método."),
        ]
    elif days_left == 2:
        phase_map = [
            (0, "Fase 1+2",  "Mañana", "Listar temas y empezar por los más difíciles. Resúmenes concisos."),
            (0, "Fase 1+2",  "Tarde",  "Continuar con los temas restantes. Ejercicios de práctica."),
            (0, "Fase 1+2",  "Noche",  "Auto-quiz de los temas del día."),
            (1, "Fase 3",    "Mañana", "Repaso general con esquemas/resúmenes. No estudiar temas nuevos."),
            (1, "Fase 3",    "Tarde",  "Últimas dudas. Descansar temprano."),
        ]
    else:
        phase_map = [
            (0, "Repaso intensivo", "Mañana", "Repasar los temas más probables/importantes del parcial."),
            (0, "Repaso intensivo", "Tarde",  "Ejercicios de práctica. Revisar errores frecuentes."),
            (0, "Repaso intensivo", "Noche",  "Leer resúmenes. Dormir bien."),
        ]

    day_names = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

    for delta, fase, sesion, actividad in phase_map:
        target = TODAY
        from datetime import timedelta
        target = TODAY + timedelta(days=delta)
        if target >= EXAM_DATE:
            break
        day_name = day_names[target.weekday()]
        schedule.append([
            target.strftime("%d/%m/%Y"),
            day_name,
            fase,
            sesion,
            actividad,
            "Pendiente",
        ])

    return schedule


def build_temas_headers() -> list[list]:
    return [["Tema", "Prioridad", "Dificultad (1-5)", "% Completado", "Notas", "Estado"]]


def build_sesiones_headers() -> list[list]:
    return [["Fecha", "Hora inicio", "Hora fin", "Duración (min)", "Tema(s) estudiado(s)", "Notas"]]


# ------------------------------------------------------------------
# Comandos
# ------------------------------------------------------------------

def cmd_setup(client: SheetsClient) -> None:
    """Crea la spreadsheet y configura las hojas."""
    print(f"Creando '{SPREADSHEET_TITLE}'...")
    ss = client.create_spreadsheet(SPREADSHEET_TITLE)
    sid = ss.id

    # Renombrar la hoja por defecto y crear las demás
    default_ws = ss.sheet1
    default_ws.update_title(SHEET_PLAN)

    plan_ws = ss.worksheet(SHEET_PLAN)
    temas_ws = ss.add_worksheet(title=SHEET_TEMAS, rows=200, cols=10)
    sesiones_ws = ss.add_worksheet(title=SHEET_SESIONES, rows=500, cols=10)

    # Llenar Plan
    schedule = build_schedule()
    plan_ws.update("A1", schedule, value_input_option="USER_ENTERED")
    plan_ws.freeze(rows=1)

    # Llenar encabezados de Temas
    temas_ws.update("A1", build_temas_headers(), value_input_option="USER_ENTERED")
    temas_ws.freeze(rows=1)

    # Llenar encabezados de Sesiones
    sesiones_ws.update("A1", build_sesiones_headers(), value_input_option="USER_ENTERED")
    sesiones_ws.freeze(rows=1)

    print(f"\n✓ Spreadsheet creada correctamente.")
    print(f"  ID: {sid}")
    print(f"  URL: https://docs.google.com/spreadsheets/d/{sid}")
    print(f"\nDías hasta el parcial: {days_until_exam()}")
    print(f"Agregá tus temas con: python study_method.py add-tema \"Nombre del tema\" alta|media|baja")


def cmd_add_tema(client: SheetsClient, nombre: str, prioridad: str = "media") -> None:
    """Agrega un tema a la hoja Temas."""
    prioridad = prioridad.strip().lower()
    if prioridad not in ("alta", "media", "baja"):
        print("Prioridad inválida. Usá: alta, media o baja")
        sys.exit(1)

    row = [nombre, prioridad.capitalize(), "", "0%", "", "Pendiente"]
    result = client.append_rows([row], sheet_name=SHEET_TEMAS)
    print(f"✓ Tema agregado: '{nombre}' (prioridad {prioridad})")


def cmd_log_sesion(client: SheetsClient) -> None:
    """Registra una sesión de estudio de forma interactiva."""
    print("--- Registrar sesión de estudio ---")
    fecha = input(f"Fecha (Enter para hoy {TODAY.strftime('%d/%m/%Y')}): ").strip() or TODAY.strftime("%d/%m/%Y")
    hora_inicio = input("Hora inicio (ej: 10:00): ").strip()
    hora_fin = input("Hora fin   (ej: 11:30): ").strip()
    temas = input("Tema(s) estudiado(s): ").strip()
    notas = input("Notas / observaciones: ").strip()

    duracion = ""
    try:
        fmt = "%H:%M"
        delta = datetime.strptime(hora_fin, fmt) - datetime.strptime(hora_inicio, fmt)
        duracion = str(int(delta.total_seconds() / 60))
    except Exception:
        pass

    row = [fecha, hora_inicio, hora_fin, duracion, temas, notas]
    client.append_rows([row], sheet_name=SHEET_SESIONES)
    print(f"✓ Sesión registrada ({duracion} min de '{temas}')")


def cmd_status(client: SheetsClient) -> None:
    """Muestra un resumen del progreso."""
    days_left = days_until_exam()

    print(f"\n=== Estado del plan de estudio ===")
    print(f"Días hasta el parcial: {days_left}")
    print(f"Fecha del parcial: {EXAM_DATE.strftime('%d/%m/%Y')}\n")

    try:
        temas = client.read_all(sheet_name=SHEET_TEMAS)
        total = len(temas)
        completados = sum(1 for t in temas if str(t.get("Estado", "")).lower() in ("completado", "listo", "✓"))
        print(f"Temas registrados : {total}")
        print(f"Temas completados : {completados}")
        if total:
            print(f"Progreso          : {int(completados / total * 100)}%")

        pendientes_alta = [t["Tema"] for t in temas if str(t.get("Prioridad", "")).lower() == "alta"
                           and str(t.get("Estado", "")).lower() not in ("completado", "listo", "✓")]
        if pendientes_alta:
            print(f"\nTemas alta prioridad pendientes:")
            for t in pendientes_alta:
                print(f"  - {t}")
    except Exception as e:
        print(f"(No se pudo leer la hoja Temas: {e})")

    try:
        sesiones = client.read_all(sheet_name=SHEET_SESIONES)
        total_min = sum(int(s.get("Duración (min)", 0) or 0) for s in sesiones)
        print(f"\nSesiones registradas : {len(sesiones)}")
        print(f"Tiempo total         : {total_min // 60}h {total_min % 60}min")
    except Exception as e:
        print(f"(No se pudo leer la hoja Sesiones: {e})")


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

COMMANDS = {
    "setup": cmd_setup,
    "add-tema": cmd_add_tema,
    "log-sesion": cmd_log_sesion,
    "status": cmd_status,
}

USAGE = """
Uso:
  python study_method.py setup
  python study_method.py add-tema "Nombre del tema" alta|media|baja
  python study_method.py log-sesion
  python study_method.py status
"""

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(USAGE)
        sys.exit(1)

    cmd = sys.argv[1]
    client = SheetsClient()

    if cmd == "setup":
        cmd_setup(client)
    elif cmd == "add-tema":
        if len(sys.argv) < 3:
            print("Falta el nombre del tema.\nUso: python study_method.py add-tema \"Nombre\" alta|media|baja")
            sys.exit(1)
        prioridad = sys.argv[3] if len(sys.argv) > 3 else "media"
        cmd_add_tema(client, sys.argv[2], prioridad)
    elif cmd == "log-sesion":
        cmd_log_sesion(client)
    elif cmd == "status":
        cmd_status(client)
