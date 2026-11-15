import tempfile
import unittest
from pathlib import Path

from radar_inmuebles.almacen import Almacen
from radar_inmuebles.modelo import Aviso
from radar_inmuebles.tasacion import Tasador
from radar_inmuebles.tests import cfg_test


class TestTasador(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = Almacen(Path(self.dir.name) / "t.sqlite3")
        self.cfg = cfg_test()

    def tearDown(self):
        self.db.cerrar()
        self.dir.cleanup()

    def _cargar(self, n, pm2, barrio="Caballito", m2=70.0):
        for i in range(n):
            precio = pm2 * m2 + (i % 5) * 500      # un poco de dispersión
            self.db.guardar(Aviso(fuente="t", id_externo=f"{barrio}{i}",
                                  url=f"http://x/{barrio}{i}", barrio=barrio,
                                  precio_usd=precio, m2_totales=m2, ambientes=3,
                                  tipo="departamento"))

    def test_usa_semilla_sin_muestra(self):
        ref = Tasador(self.db, self.cfg).referencia("caballito")
        self.assertEqual(ref.origen, "semilla")
        self.assertEqual(ref.mediana, 2250)
        self.assertEqual(ref.confianza, "baja")

    def test_muestra_propia_cuando_alcanza(self):
        self._cargar(30, 2000)
        ref = Tasador(self.db, self.cfg).referencia("caballito")
        self.assertEqual(ref.origen, "propia")
        self.assertAlmostEqual(ref.mediana, 2000, delta=40)
        self.assertEqual(ref.n, 30)

    def test_mezcla_con_muestra_parcial(self):
        self._cargar(12, 1800)
        ref = Tasador(self.db, self.cfg).referencia("caballito")
        self.assertEqual(ref.origen, "mixta")
        self.assertGreater(ref.mediana, 1800)       # tira hacia la semilla
        self.assertLess(ref.mediana, 2250)

    def test_las_gangas_no_bajan_la_mediana(self):
        self._cargar(30, 2000)
        # Dos chollos extremos que son justamente lo que buscamos detectar.
        for i, pm2 in enumerate((600, 700)):
            self.db.guardar(Aviso(fuente="t", id_externo=f"ganga{i}",
                                  url="http://g", barrio="Caballito",
                                  precio_usd=pm2 * 70, m2_totales=70.0,
                                  ambientes=3, tipo="departamento"))
        ref = Tasador(self.db, self.cfg).referencia("caballito")
        self.assertAlmostEqual(ref.mediana, 2000, delta=60)

    def test_ignora_precios_imposibles(self):
        self._cargar(25, 2000)
        self.db.guardar(Aviso(fuente="t", id_externo="error", url="http://e",
                              barrio="Caballito", precio_usd=50.0, m2_totales=70.0,
                              ambientes=3, tipo="departamento"))
        ref = Tasador(self.db, self.cfg).referencia("caballito")
        self.assertAlmostEqual(ref.mediana, 2000, delta=60)

    def test_cada_barrio_tiene_su_valor(self):
        self._cargar(30, 2200, "Caballito")
        self._cargar(30, 1500, "Liniers")
        t = Tasador(self.db, self.cfg)
        self.assertGreater(t.referencia("caballito").mediana,
                           t.referencia("liniers").mediana)

    def test_barrio_desconocido_sin_referencia(self):
        self.assertIsNone(Tasador(self.db, self.cfg).referencia("tristan suarez"))


if __name__ == "__main__":
    unittest.main()
