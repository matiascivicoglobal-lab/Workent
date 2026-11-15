"""Guarda que el config.yaml real siga siendo válido y coherente."""

import unittest

from radar_inmuebles.ajustes import cargar
from radar_inmuebles.notificadores import construir_notificador


class TestConfigDelUsuario(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(recargar=True)

    def test_carga_sin_errores(self):
        self.assertTrue(self.cfg.barrios)
        self.assertTrue(self.cfg.fuentes_activas)

    def test_rango_de_precios_coherente(self):
        minimo = float(self.cfg.get("busqueda.precio_usd_min"))
        maximo = float(self.cfg.get("busqueda.precio_usd_max"))
        self.assertGreater(maximo, minimo)

    def test_todos_los_barrios_tienen_valor_semilla(self):
        # Sin semilla, un barrio nuevo no puede evaluarse hasta juntar muestra.
        refs = self.cfg.valores_referencia
        for barrio in self.cfg.barrios:
            with self.subTest(barrio=barrio):
                self.assertTrue(any(barrio in k or k in barrio for k in refs),
                                f"falta valores_referencia para '{barrio}'")

    def test_las_fuentes_existen(self):
        from radar_inmuebles.fuentes import REGISTRO
        for nombre in self.cfg.fuentes_activas:
            self.assertIn(nombre, REGISTRO)

    def test_telefono_valido(self):
        n = construir_notificador(self.cfg)
        destino = n.e164(str(self.cfg.get("alertas.telefono")))
        self.assertTrue(destino.startswith("+549"), destino)
        self.assertEqual(len(destino), 14, f"{destino} no parece un celular argentino")

    def test_facebook_espaciado_si_esta_activo(self):
        if self.cfg.get("fuentes.facebook.activa"):
            cada = self.cfg.get("fuentes.facebook.cada_minutos")
            self.assertIsNotNone(cada, "Facebook activo sin cada_minutos")
            self.assertGreaterEqual(float(cada), 60,
                                    "consultar Facebook más seguido que cada 60 min "
                                    "aumenta el riesgo de bloqueo de cuenta")

    def test_umbrales_en_rango(self):
        self.assertTrue(0 < float(self.cfg.get("oportunidad.descuento_minimo")) < 1)
        self.assertTrue(0 < float(self.cfg.get("oportunidad.puntaje_minimo")) <= 100)
        self.assertGreater(float(self.cfg.get("oportunidad.descuento_sospechoso")),
                           float(self.cfg.get("oportunidad.descuento_minimo")))


if __name__ == "__main__":
    unittest.main()
