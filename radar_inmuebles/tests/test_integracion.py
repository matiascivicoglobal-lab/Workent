"""Pipeline completo de punta a punta, con una fuente falsa y sin red."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from radar_inmuebles import radar as modulo_radar
from radar_inmuebles.ajustes import cargar
from radar_inmuebles.fuentes.base import Fuente
from radar_inmuebles.modelo import Aviso
from radar_inmuebles.notificadores.base import Notificador


class _FuenteFalsa(Fuente):
    nombre = "falsa"

    def __init__(self, avisos, *a, **kw):
        self._avisos = avisos
        self.log = __import__("logging").getLogger("test")

    def buscar(self, barrio):
        return [a for a in self._avisos if a.barrio.lower() == barrio.lower()]


class _NotificadorEspia(Notificador):
    nombre = "espia"

    def __init__(self, ajustes):
        super().__init__(ajustes)
        self.mensajes = []

    def enviar(self, mensaje):
        self.mensajes.append(mensaje)
        return True


def _aviso(id_externo, precio, m2=70.0, barrio="Caballito", desc="", amb=3):
    return Aviso(fuente="falsa", id_externo=id_externo, url=f"http://x/{id_externo}",
                 titulo=f"Depto {amb} ambientes en {barrio}", barrio=barrio,
                 precio=precio, moneda="USD", m2_totales=m2, ambientes=amb,
                 descripcion=desc, tipo="departamento")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.cfg = cargar(recargar=True)
        self.cfg.datos["salida"]["db"] = str(Path(self.dir.name) / "t.sqlite3")
        self.cfg.datos["fuentes"] = {"falsa": {"activa": True, "navegador": False}}
        self.cfg.datos["scraping"]["enriquecer_candidatos"] = False

        # Mercado de Caballito en ~2.000 USD/m² + una ganga clarísima.
        self.mercado = [_aviso(f"m{i}", 140000 + i * 300) for i in range(30)]
        self.ganga = _aviso("ganga", 84000.0, desc="A reciclar, dueño directo")
        self.cara = _aviso("cara", 210000.0)

        self.parches = [
            mock.patch.object(modulo_radar, "construir_fuentes",
                              lambda *a, **kw: [_FuenteFalsa(
                                  self.mercado + [self.ganga, self.cara])]),
            mock.patch.object(modulo_radar.fx, "obtener", lambda *a, **kw: 1450.0),
        ]
        for p in self.parches:
            p.start()

    def tearDown(self):
        for p in self.parches:
            p.stop()
        self.dir.cleanup()

    def _correr(self):
        r = modulo_radar.Radar(self.cfg, enviar=True)
        r.notificador = _NotificadorEspia(self.cfg)
        try:
            return r, r.correr()
        finally:
            r.cerrar()

    # ------------------------------------------------------------------
    def test_encuentra_la_ganga_y_solo_la_ganga(self):
        radar, res = self._correr()
        self.assertEqual(res.revisados, 32)
        self.assertEqual(res.nuevos, 32)
        ids = [ev.aviso.id_externo for ev in res.oportunidades]
        self.assertIn("ganga", ids)
        self.assertNotIn("cara", ids)
        self.assertNotIn("m0", ids)

    def test_manda_el_whatsapp(self):
        radar, res = self._correr()
        self.assertEqual(len(radar.notificador.mensajes), 1)
        mensaje = radar.notificador.mensajes[0]
        self.assertIn("Caballito", mensaje)
        self.assertIn("USD 84.000", mensaje)
        self.assertIn("más barata", mensaje)

    def test_no_repite_el_aviso_en_la_segunda_corrida(self):
        self._correr()
        radar2, res2 = self._correr()
        self.assertEqual(res2.nuevos, 0)
        self.assertEqual(len(radar2.notificador.mensajes), 0)

    def test_avisa_de_nuevo_si_baja_el_precio(self):
        self._correr()
        self.ganga.precio = 72000.0            # bajó 14%
        radar2, res2 = self._correr()
        self.assertEqual(len(radar2.notificador.mensajes), 1)
        self.assertIn("BAJÓ DE PRECIO", radar2.notificador.mensajes[0])

    def test_respeta_el_tope_por_corrida(self):
        self.cfg.datos["alertas"]["max_por_corrida"] = 2
        for i in range(5):
            self.mercado.append(_aviso(f"g{i}", 80000.0 + i * 100,
                                       desc="a reciclar"))
        radar, res = self._correr()
        self.assertEqual(len(radar.notificador.mensajes), 2)
        self.assertGreater(len(res.oportunidades), 2)

    def test_no_avisa_fuera_de_horario(self):
        self.cfg.datos["monitoreo"]["horario_activo"] = [3, 4]
        radar, res = self._correr()
        self.assertEqual(len(radar.notificador.mensajes), 0)
        self.assertTrue(res.oportunidades)      # la detectó igual

    def test_aviso_repetido_en_otro_portal_no_duplica(self):
        clon = _aviso("ganga", 84500.0, m2=71.0, desc="A reciclar")
        clon.fuente = "otra"
        self.mercado.append(clon)
        radar, res = self._correr()
        self.assertEqual(len(radar.notificador.mensajes), 1)

    def test_el_corpus_define_la_mediana(self):
        radar, res = self._correr()
        ref = radar.tasador.referencia("caballito")
        self.assertEqual(ref.origen, "propia")
        self.assertAlmostEqual(ref.mediana, 2000, delta=120)

    def test_sin_enviar_no_manda_nada(self):
        r = modulo_radar.Radar(self.cfg, enviar=False)
        r.notificador = _NotificadorEspia(self.cfg)
        try:
            res = r.correr()
        finally:
            r.cerrar()
        self.assertTrue(res.oportunidades)
        self.assertEqual(r.notificador.mensajes, [])

    def test_precio_en_pesos_se_convierte(self):
        en_pesos = _aviso("pesos", 84000.0 * 1450, barrio="Caballito")
        en_pesos.moneda = "ARS"
        self.mercado.append(en_pesos)
        radar, res = self._correr()
        from radar_inmuebles.almacen import Almacen
        with Almacen(self.cfg.db) as db:
            guardado = db.obtener("falsa:pesos")
        self.assertAlmostEqual(guardado.precio_usd, 84000.0, delta=1)
        self.assertIn("pesos", [ev.aviso.id_externo for ev in res.oportunidades])


if __name__ == "__main__":
    unittest.main()
