import unittest

from radar_inmuebles.notificadores import (Cadena, Consola, Telegram, TwilioWhatsApp,
                                           construir_canal, construir_notificador,
                                           parsear_canal)
from radar_inmuebles.notificadores.base import Notificador
from radar_inmuebles.notificadores.callmebot import CallMeBot
from radar_inmuebles.tests import cfg_test


class _Canal(Notificador):
    def __init__(self, ajustes, nombre, listo=True, funciona=True):
        super().__init__(ajustes)
        self.nombre = nombre
        self._listo, self._funciona = listo, funciona
        self.recibidos = []

    def configurado(self):
        return (True, "") if self._listo else (False, f"falta algo en {self.nombre}")

    def enviar(self, mensaje):
        if not self._funciona:
            return False
        self.recibidos.append(mensaje)
        return True


class TestTelefono(unittest.TestCase):
    def test_variantes_argentinas(self):
        for entrada in ("1123549925", "+5491123549925", "01123549925",
                        "541123549925", "5491123549925", "11 2354-9925"):
            with self.subTest(entrada=entrada):
                self.assertEqual(Notificador.e164(entrada), "+5491123549925")


class TestSeleccionDeCanal(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()

    def test_parsear(self):
        self.assertEqual(parsear_canal("whatsapp:twilio"), ("whatsapp", "twilio"))
        self.assertEqual(parsear_canal("telegram"), ("telegram", ""))
        self.assertEqual(parsear_canal(""), ("", ""))

    def test_construye_cada_proveedor(self):
        self.assertIsInstance(construir_canal(self.cfg, "whatsapp", "callmebot"), CallMeBot)
        self.assertIsInstance(construir_canal(self.cfg, "whatsapp", "twilio"), TwilioWhatsApp)
        self.assertIsInstance(construir_canal(self.cfg, "telegram"), Telegram)
        self.assertIsInstance(construir_canal(self.cfg, "consola"), Consola)

    def test_proveedor_invalido_cae_a_consola(self):
        self.assertIsInstance(construir_canal(self.cfg, "whatsapp", "inventado"), Consola)
        self.assertIsInstance(construir_canal(self.cfg, "paloma-mensajera"), Consola)

    def test_el_flag_canal_pisa_la_config(self):
        self.cfg.datos["alertas"]["destino"] = "whatsapp"
        n = construir_notificador(self.cfg, canal="telegram")
        self.assertIsInstance(n, Telegram)

    def test_sin_respaldo_devuelve_canal_suelto(self):
        self.cfg.datos["alertas"]["destino"] = "consola"
        self.cfg.datos["alertas"]["respaldo"] = ""
        self.assertIsInstance(construir_notificador(self.cfg), Consola)

    def test_con_respaldo_devuelve_cadena(self):
        self.cfg.datos["alertas"]["destino"] = "whatsapp"
        self.cfg.datos["alertas"]["respaldo"] = "consola"
        self.assertIsInstance(construir_notificador(self.cfg), Cadena)

    def test_respaldo_igual_al_principal_no_duplica(self):
        self.cfg.datos["alertas"]["destino"] = "consola"
        self.cfg.datos["alertas"]["respaldo"] = "consola"
        self.assertIsInstance(construir_notificador(self.cfg), Consola)


class TestCadena(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()

    def test_usa_el_principal_si_anda(self):
        a = _Canal(self.cfg, "principal")
        b = _Canal(self.cfg, "respaldo")
        self.assertTrue(Cadena(self.cfg, [a, b]).enviar("hola"))
        self.assertEqual(a.recibidos, ["hola"])
        self.assertEqual(b.recibidos, [])

    def test_cae_al_respaldo_si_el_principal_falla(self):
        a = _Canal(self.cfg, "principal", funciona=False)
        b = _Canal(self.cfg, "respaldo")
        self.assertTrue(Cadena(self.cfg, [a, b]).enviar("hola"))
        self.assertEqual(b.recibidos, ["hola"])

    def test_saltea_el_que_no_esta_configurado(self):
        a = _Canal(self.cfg, "principal", listo=False)
        b = _Canal(self.cfg, "respaldo")
        self.assertTrue(Cadena(self.cfg, [a, b]).enviar("hola"))
        self.assertEqual(b.recibidos, ["hola"])

    def test_falla_si_fallan_todos(self):
        a = _Canal(self.cfg, "a", funciona=False)
        b = _Canal(self.cfg, "b", funciona=False)
        self.assertFalse(Cadena(self.cfg, [a, b]).enviar("hola"))

    def test_configurado_si_al_menos_uno_lo_esta(self):
        cadena = Cadena(self.cfg, [_Canal(self.cfg, "a", listo=False),
                                   _Canal(self.cfg, "b", listo=True)])
        self.assertTrue(cadena.configurado()[0])

    def test_sin_ninguno_configurado_explica_que_falta(self):
        cadena = Cadena(self.cfg, [_Canal(self.cfg, "a", listo=False),
                                   _Canal(self.cfg, "b", listo=False)])
        listo, falta = cadena.configurado()
        self.assertFalse(listo)
        self.assertIn("falta algo en a", falta)
        self.assertIn("falta algo en b", falta)


class TestPlantillaCloud(unittest.TestCase):
    """WhatsApp rechaza variables de plantilla con saltos de línea."""

    def setUp(self):
        from radar_inmuebles.mensajes import alerta
        from radar_inmuebles.modelo import Aviso
        from radar_inmuebles.scoring import Evaluador
        from radar_inmuebles.tasacion import Referencia

        class _T:
            def referencia(self, barrio, ambientes=None):
                return Referencia("Caballito", 2000.0, 1760.0, 2400.0, 50, "propia")

        aviso = Aviso(fuente="zonaprop", id_externo="1", url="https://zp.com.ar/x-1.html",
                      titulo="3 ambientes a reciclar", barrio="Caballito",
                      precio=84000, moneda="USD", precio_usd=84000.0,
                      m2_totales=70.0, ambientes=3, expensas_ars=85000.0,
                      descripcion="A reciclar, dueño directo")
        ev = Evaluador(_T(), cfg_test()).evaluar(aviso, dias_visible=90)
        self.original = alerta(ev)

    def test_aplana_un_aviso_real(self):
        from radar_inmuebles.notificadores.cloud_wa import aplanar
        plano = aplanar(self.original)
        self.assertNotIn("\n", plano)
        self.assertNotIn("\t", plano)
        self.assertNotIn("    ", plano)
        self.assertLessEqual(len(plano), 900)

    def test_no_pierde_lo_importante(self):
        from radar_inmuebles.notificadores.cloud_wa import aplanar
        plano = aplanar(self.original)
        for dato in ("Caballito", "USD 84.000", "zp.com.ar/x-1.html"):
            with self.subTest(dato=dato):
                self.assertIn(dato, plano)

    def test_no_deja_separadores_repetidos(self):
        from radar_inmuebles.notificadores.cloud_wa import aplanar
        self.assertNotIn(" ·  · ", aplanar("a\n\n──────\n\nb"))

    def test_recorta_mensajes_largos(self):
        from radar_inmuebles.notificadores.cloud_wa import aplanar
        self.assertLessEqual(len(aplanar("x" * 5000)), 900)


if __name__ == "__main__":
    unittest.main()
