import unittest

from radar_inmuebles.mensajes import alerta, recortar, resumen_diario
from radar_inmuebles.modelo import Aviso
from radar_inmuebles.scoring import Evaluador
from radar_inmuebles.tasacion import Referencia
from radar_inmuebles.tests import cfg_test


class _Tasador:
    def referencia(self, barrio, ambientes=None):
        return Referencia("Caballito", 2000.0, 1760.0, 2400.0, 50, "propia")


class TestAlerta(unittest.TestCase):
    def setUp(self):
        cfg = cfg_test()
        aviso = Aviso(fuente="zonaprop", id_externo="1",
                      url="https://www.zonaprop.com.ar/x-1.html",
                      titulo="3 ambientes a reciclar", barrio="Caballito",
                      direccion="Rivadavia 5200", precio=84000, moneda="USD",
                      precio_usd=84000.0, m2_totales=70.0, ambientes=3,
                      expensas_ars=85000.0,
                      descripcion="A reciclar, dueño directo")
        self.ev = Evaluador(_Tasador(), cfg).evaluar(aviso, dias_visible=90)
        self.texto = alerta(self.ev)

    def test_tiene_lo_que_importa(self):
        for esperado in ("Caballito", "USD 84.000", "USD 2.000/m²", "USD 1.200/m²",
                         "40% más barata", "zonaprop.com.ar/x-1.html", "3 amb", "70 m²"):
            with self.subTest(esperado=esperado):
                self.assertIn(esperado, self.texto)

    def test_muestra_la_cuenta_del_reciclado(self):
        self.assertIn("Obra estimada", self.texto)
        self.assertIn("Margen", self.texto)

    def test_muestra_las_senales(self):
        self.assertIn("a reciclar", self.texto)
        self.assertIn("dueño directo", self.texto)

    def test_entra_en_un_whatsapp(self):
        self.assertLess(len(self.texto), 1600)

    def test_avisa_cuando_es_sospechoso(self):
        cfg = cfg_test()
        aviso = Aviso(fuente="x", id_externo="2", url="http://y", barrio="Caballito",
                      precio_usd=30000.0, m2_totales=70.0, ambientes=3)
        ev = Evaluador(_Tasador(), cfg).evaluar(aviso)
        self.assertIn("Verificá", alerta(ev))

    def test_titulo_de_baja_de_precio(self):
        self.ev.baja_precio = {"desde": 100000, "hasta": 84000, "pct": 0.16, "dias": 12}
        texto = alerta(self.ev, tipo="baja_precio")
        self.assertIn("BAJÓ DE PRECIO", texto)
        self.assertIn("Bajó 16%", texto)


class TestResumen(unittest.TestCase):
    def test_resumen_con_y_sin_oportunidades(self):
        refs = [Referencia("Caballito", 2000.0, 1800.0, 2300.0, 44, "propia")]
        vacio = resumen_diario([], refs, {"revisados": 120, "nuevos": 8})
        self.assertIn("Caballito", vacio)
        self.assertIn("120 avisos revisados", vacio)
        self.assertIn("no apareció nada", vacio)


class TestRecorte(unittest.TestCase):
    def test_recorta_largos(self):
        largo = "\n".join(f"linea {i}" * 20 for i in range(500))
        self.assertLessEqual(len(recortar(largo, 1000)), 1000)

    def test_no_toca_cortos(self):
        self.assertEqual(recortar("hola"), "hola")


if __name__ == "__main__":
    unittest.main()
