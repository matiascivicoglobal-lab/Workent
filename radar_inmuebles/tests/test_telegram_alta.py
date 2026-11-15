import tempfile
import unittest
from pathlib import Path

from radar_inmuebles.telegram_alta import (enmascarar, extraer_chats,
                                           guardar_clave, guardar_en_env)

# Token de mentira, con la misma forma que los de BotFather.
# Nunca pongas el token real en un test: este archivo sí se sube a git.
TOKEN_FALSO = "1234567890:AAFalsoFalsoFalsoFalsoFalsoFalsoFal"


def _update(chat_id, **chat):
    base = {"id": chat_id, "type": "private", "first_name": "Matías"}
    base.update(chat)
    return {"update_id": abs(hash(str(chat_id))) % 10**6,
            "message": {"message_id": 1, "chat": base, "text": "hola"}}


class TestEnmascarar(unittest.TestCase):
    def test_no_muestra_el_token_entero(self):
        salida = enmascarar(TOKEN_FALSO)
        self.assertNotIn("AAFalsoFalso", salida)
        self.assertIn("…", salida)
        self.assertLess(len(salida), len(TOKEN_FALSO))

    def test_token_vacio(self):
        self.assertEqual(enmascarar(""), "(vacío)")
        self.assertEqual(enmascarar("corto"), "(vacío)")


class TestExtraerChats(unittest.TestCase):
    def test_un_chat(self):
        chats = extraer_chats({"ok": True, "result": [_update(123456789)]})
        self.assertEqual(len(chats), 1)
        self.assertEqual(chats[0]["id"], 123456789)
        self.assertEqual(chats[0]["nombre"], "Matías")
        self.assertEqual(chats[0]["tipo"], "private")

    def test_no_repite_el_mismo_chat(self):
        datos = {"ok": True, "result": [_update(111), _update(111), _update(222)]}
        self.assertEqual([c["id"] for c in extraer_chats(datos)], [111, 222])

    def test_sin_mensajes(self):
        self.assertEqual(extraer_chats({"ok": True, "result": []}), [])
        self.assertEqual(extraer_chats({}), [])
        self.assertEqual(extraer_chats(None), [])

    def test_grupo_usa_el_titulo(self):
        datos = {"result": [{"message": {"chat": {"id": -100, "type": "group",
                                                  "title": "Deptos CABA"}}}]}
        chats = extraer_chats(datos)
        self.assertEqual(chats[0]["nombre"], "Deptos CABA")
        self.assertEqual(chats[0]["id"], -100)

    def test_mensaje_editado_tambien_cuenta(self):
        datos = {"result": [{"edited_message": {"chat": {"id": 77, "type": "private",
                                                         "username": "mati"}}}]}
        self.assertEqual(extraer_chats(datos)[0]["nombre"], "mati")

    def test_update_sin_chat_no_rompe(self):
        datos = {"result": [{"update_id": 1}, {"message": {}}, _update(5)]}
        self.assertEqual([c["id"] for c in extraer_chats(datos)], [5])


class TestGuardarEnEnv(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / ".env"

    def tearDown(self):
        self.dir.cleanup()

    def test_crea_el_archivo_si_no_existe(self):
        guardar_en_env(self.ruta, 123)
        self.assertIn("TELEGRAM_CHAT_ID=123", self.ruta.read_text())

    def test_reemplaza_el_valor_existente(self):
        self.ruta.write_text("TELEGRAM_TOKEN=abc\nTELEGRAM_CHAT_ID=viejo\nOTRA=1\n")
        guardar_en_env(self.ruta, 999)
        texto = self.ruta.read_text()
        self.assertIn("TELEGRAM_CHAT_ID=999", texto)
        self.assertNotIn("viejo", texto)
        self.assertIn("TELEGRAM_TOKEN=abc", texto, "no debe pisar el resto del .env")
        self.assertIn("OTRA=1", texto)
        self.assertEqual(texto.count("TELEGRAM_CHAT_ID"), 1)

    def test_agrega_si_falta_la_clave(self):
        self.ruta.write_text("TELEGRAM_TOKEN=abc\n")
        guardar_en_env(self.ruta, 55)
        texto = self.ruta.read_text()
        self.assertIn("TELEGRAM_TOKEN=abc", texto)
        self.assertIn("TELEGRAM_CHAT_ID=55", texto)

    def test_no_pisa_una_clave_parecida(self):
        self.ruta.write_text("OTRO_TELEGRAM_CHAT_ID_VIEJO=1\nTELEGRAM_CHAT_ID=2\n")
        guardar_en_env(self.ruta, 7)
        texto = self.ruta.read_text()
        self.assertIn("OTRO_TELEGRAM_CHAT_ID_VIEJO=1", texto)
        self.assertIn("TELEGRAM_CHAT_ID=7", texto)

    def test_chat_id_negativo_de_grupo(self):
        guardar_en_env(self.ruta, -1001234567890)
        self.assertIn("TELEGRAM_CHAT_ID=-1001234567890", self.ruta.read_text())


class TestGuardarClave(unittest.TestCase):
    """El caso que rompió la instalación: la línea venía comentada."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / ".env"

    def tearDown(self):
        self.dir.cleanup()

    def test_descomenta_la_linea(self):
        self.ruta.write_text("# TELEGRAM_TOKEN=\nOTRA=1\n")
        guardar_clave(self.ruta, "TELEGRAM_TOKEN", TOKEN_FALSO)
        texto = self.ruta.read_text()
        self.assertIn(f"TELEGRAM_TOKEN={TOKEN_FALSO}", texto)
        self.assertNotIn("# TELEGRAM_TOKEN", texto)
        self.assertIn("OTRA=1", texto)

    def test_borra_duplicados(self):
        self.ruta.write_text("# TELEGRAM_TOKEN=\nTELEGRAM_TOKEN=viejo\nOTRA=1\n")
        guardar_clave(self.ruta, "TELEGRAM_TOKEN", "nuevo")
        texto = self.ruta.read_text()
        self.assertEqual(texto.count("TELEGRAM_TOKEN"), 1)
        self.assertIn("TELEGRAM_TOKEN=nuevo", texto)
        self.assertNotIn("viejo", texto)
        self.assertIn("OTRA=1", texto)

    def test_respeta_claves_con_prefijo_parecido(self):
        self.ruta.write_text("TELEGRAM_TOKEN_VIEJO=x\nTELEGRAM_TOKEN=y\n")
        guardar_clave(self.ruta, "TELEGRAM_TOKEN", "z")
        texto = self.ruta.read_text()
        self.assertIn("TELEGRAM_TOKEN_VIEJO=x", texto)
        self.assertIn("TELEGRAM_TOKEN=z", texto)

    def test_agrega_si_no_estaba(self):
        self.ruta.write_text("OTRA=1\n")
        guardar_clave(self.ruta, "TELEGRAM_TOKEN", "abc")
        self.assertIn("TELEGRAM_TOKEN=abc", self.ruta.read_text())

    def test_el_env_de_ejemplo_no_trae_telegram_comentado(self):
        """Si viene comentado, el usuario pega el token y no toma efecto."""
        from radar_inmuebles.ajustes import RAIZ
        lineas = (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines()
        for clave in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"):
            activas = [l for l in lineas
                       if l.strip().startswith(f"{clave}=")]
            with self.subTest(clave=clave):
                self.assertTrue(activas, f"{clave} tiene que estar sin comentar")


if __name__ == "__main__":
    unittest.main()
