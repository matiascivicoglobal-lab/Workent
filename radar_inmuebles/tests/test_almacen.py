import tempfile
import unittest
from pathlib import Path

from radar_inmuebles.almacen import Almacen
from radar_inmuebles.modelo import Aviso


def _aviso(id_externo="1", precio=96000.0, fuente="zonaprop", m2=70.0):
    return Aviso(fuente=fuente, id_externo=id_externo, url=f"http://x/{id_externo}",
                 titulo="Depto 3 amb", barrio="Caballito", precio=precio,
                 moneda="USD", precio_usd=precio, m2_totales=m2, ambientes=3)


class TestAlmacen(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = Almacen(Path(self.dir.name) / "t.sqlite3")

    def tearDown(self):
        self.db.cerrar()
        self.dir.cleanup()

    def test_insert_y_update(self):
        c1 = self.db.guardar(_aviso())
        self.assertTrue(c1["nuevo"])
        c2 = self.db.guardar(_aviso())
        self.assertFalse(c2["nuevo"])
        self.assertEqual(len(self.db.avisos()), 1)

    def test_detecta_baja_de_precio(self):
        self.db.guardar(_aviso(precio=112000.0))
        import time; time.sleep(0.01)
        cambio = self.db.guardar(_aviso(precio=96000.0))
        self.assertAlmostEqual(cambio["variacion"], -0.1428, places=3)

        baja = self.db.baja_de_precio("zonaprop:1")
        self.assertIsNotNone(baja)
        self.assertAlmostEqual(baja["pct"], 0.1428, places=3)
        self.assertEqual(baja["desde"], 112000)
        self.assertEqual(baja["hasta"], 96000)

    def test_sin_baja_si_subio(self):
        self.db.guardar(_aviso(precio=90000.0))
        import time; time.sleep(0.01)
        self.db.guardar(_aviso(precio=99000.0))
        self.assertIsNone(self.db.baja_de_precio("zonaprop:1"))

    def test_historial_acumula(self):
        for p in (110000.0, 105000.0, 99000.0):
            self.db.guardar(_aviso(precio=p))
            import time; time.sleep(0.01)
        self.assertEqual(len(self.db.historial("zonaprop:1")), 3)

    def test_duplicados_entre_portales(self):
        self.db.guardar(_aviso("111", 96000.0, "zonaprop", 70.0))
        self.db.guardar(_aviso("222", 95500.0, "argenprop", 71.0))
        dups = self.db.duplicados_de(_aviso("111", 96000.0, "zonaprop", 70.0))
        self.assertIn("argenprop:222", dups)

    def test_alertas_no_se_repiten(self):
        self.db.guardar(_aviso())
        self.assertFalse(self.db.ya_alertado("zonaprop:1"))
        self.db.registrar_alerta("zonaprop:1", "nueva", 82.0)
        self.assertTrue(self.db.ya_alertado("zonaprop:1"))
        self.assertFalse(self.db.ya_alertado("zonaprop:1", "baja_precio"))

    def test_filtra_por_barrio(self):
        self.db.guardar(_aviso("1"))
        otro = _aviso("2"); otro.barrio = "Liniers"
        self.db.guardar(otro)
        self.assertEqual(len(self.db.avisos(barrio="caballito")), 1)
        self.assertEqual(len(self.db.avisos(barrio="liniers")), 1)

    def test_cotizacion_cacheada(self):
        self.assertIsNone(self.db.cotizacion_de_hoy())
        self.db.guardar_cotizacion("blue", 1480.0)
        self.assertEqual(self.db.cotizacion_de_hoy(), 1480.0)

    def test_cuenta_los_nuevos_del_dia(self):
        self.assertEqual(self.db.nuevos_desde(24), 0)
        self.db.guardar(_aviso("1"))
        self.db.guardar(_aviso("2"))
        self.assertEqual(self.db.nuevos_desde(24), 2)
        self.db.guardar(_aviso("1", precio=90000.0))   # actualizar no suma
        self.assertEqual(self.db.nuevos_desde(24), 2)

    def test_primera_vez_persiste(self):
        self.db.guardar(_aviso())
        primera = self.db.primera_vez("zonaprop:1")
        self.db.guardar(_aviso(precio=90000.0))
        self.assertEqual(self.db.primera_vez("zonaprop:1"), primera)


if __name__ == "__main__":
    unittest.main()
