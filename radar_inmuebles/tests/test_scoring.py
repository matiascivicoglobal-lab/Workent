import unittest

from radar_inmuebles.ajustes import cargar
from radar_inmuebles.modelo import Aviso
from radar_inmuebles.scoring import Evaluador, pasa_filtros_basicos
from radar_inmuebles.tasacion import Referencia


class _Tasador:
    """Zona fija en USD 2.000/m² (p75 = 2.400) para que las cuentas sean claras."""
    def __init__(self, mediana=2000.0, n=50, origen="propia"):
        self.ref = Referencia("Caballito", mediana, mediana * 0.88, mediana * 1.2,
                              n, origen)

    def referencia(self, barrio, ambientes=None):
        return self.ref


def _aviso(precio=100000.0, m2=70.0, descripcion="", ambientes=3, **kw):
    datos = dict(fuente="zonaprop", id_externo="1", url="http://x",
                 titulo="Departamento 3 ambientes", barrio="Caballito",
                 precio=precio, moneda="USD", precio_usd=precio, m2_totales=m2,
                 ambientes=ambientes, descripcion=descripcion, tipo="departamento")
    datos.update(kw)
    return Aviso(**datos)


class TestEvaluador(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(recargar=True)
        self.ev = Evaluador(_Tasador(), self.cfg)

    # -- descuento ------------------------------------------------------
    def test_a_precio_de_mercado_no_es_oportunidad(self):
        e = self.ev.evaluar(_aviso(precio=140000.0, m2=70.0))   # 2.000/m² = mediana
        self.assertAlmostEqual(e.descuento, 0.0, places=2)
        self.assertFalse(self.ev.merece_alerta(e))

    def test_descuento_bien_calculado(self):
        e = self.ev.evaluar(_aviso(precio=84000.0, m2=70.0))    # 1.200/m²
        self.assertAlmostEqual(e.descuento, 0.40, places=2)
        self.assertTrue(self.ev.merece_alerta(e))
        self.assertGreater(e.puntaje, 60)

    def test_mas_caro_que_la_zona_da_descuento_negativo(self):
        e = self.ev.evaluar(_aviso(precio=200000.0, m2=70.0))
        self.assertLess(e.descuento, 0)
        self.assertFalse(self.ev.merece_alerta(e))

    # -- economía del reciclado ------------------------------------------
    def test_cuenta_de_la_reforma(self):
        e = self.ev.evaluar(_aviso(precio=84000.0, m2=70.0))
        self.assertEqual(e.costo_reforma, 70 * 400)                       # 28.000
        self.assertAlmostEqual(e.inversion_total, 84000 * 1.06 + 28000)   # 117.040
        self.assertAlmostEqual(e.valor_objetivo, 70 * 2400)               # 168.000
        self.assertAlmostEqual(e.valor_neto, 168000 * 0.96)               # 161.280
        self.assertAlmostEqual(e.margen, 161280 - 117040)                 # 44.240
        self.assertGreater(e.margen_pct, 0.35)

    def test_descuento_chico_no_deja_margen(self):
        # 10% abajo de la mediana no paga la obra: margen flaco.
        e = self.ev.evaluar(_aviso(precio=126000.0, m2=70.0))
        self.assertLess(e.margen_pct, 0.12)
        self.assertFalse(self.ev.merece_alerta(e))

    # -- señales ---------------------------------------------------------
    def test_detecta_senales_de_oportunidad(self):
        e = self.ev.evaluar(_aviso(descripcion="A reciclar. Dueño directo, escucho ofertas"))
        self.assertIn("a reciclar", e.senales)
        self.assertIn("dueño directo", e.senales)
        self.assertIn("escucha ofertas", e.senales)

    def test_las_senales_suman_puntaje(self):
        sin = self.ev.evaluar(_aviso(precio=100000.0))
        con = self.ev.evaluar(_aviso(precio=100000.0,
                                     descripcion="A refaccionar, dueño directo, urge venta"))
        self.assertGreater(con.puntaje, sin.puntaje)

    def test_riesgo_excluyente_descarta(self):
        for texto in ("Se vende la nuda propiedad", "Depto con usufructo vitalicio",
                      "Unidad en pozo, entrega 2028"):
            with self.subTest(texto=texto):
                e = self.ev.evaluar(_aviso(precio=50000.0, descripcion=texto))
                self.assertTrue(e.motivo_descarte)
                self.assertFalse(self.ev.merece_alerta(e))

    def test_riesgo_no_excluyente_resta(self):
        limpio = self.ev.evaluar(_aviso(precio=84000.0))
        riesgo = self.ev.evaluar(_aviso(precio=84000.0,
                                        descripcion="Sucesión en trámite, no apto crédito"))
        self.assertLess(riesgo.puntaje, limpio.puntaje)
        self.assertTrue(riesgo.riesgos)

    # -- casos límite -----------------------------------------------------
    def test_precio_absurdo_se_marca_sospechoso(self):
        e = self.ev.evaluar(_aviso(precio=35000.0, m2=70.0))    # 500/m², -75%
        self.assertTrue(e.sospechoso)
        self.assertLessEqual(e.puntaje, 70)

    def test_sin_m2_no_se_puede_tasar(self):
        e = self.ev.evaluar(_aviso(m2=None))
        self.assertEqual(e.motivo_descarte, "sin superficie publicada")

    def test_sin_precio_no_se_puede_tasar(self):
        e = self.ev.evaluar(_aviso(precio=None, precio_usd=None))
        self.assertEqual(e.motivo_descarte, "sin precio publicado")

    def test_baja_de_precio_suma(self):
        sin = self.ev.evaluar(_aviso(precio=84000.0))
        con = self.ev.evaluar(_aviso(precio=84000.0),
                              baja_precio={"desde": 100000, "hasta": 84000,
                                           "pct": 0.16, "dias": 20})
        self.assertGreater(con.puntaje, sin.puntaje)

    def test_antiguedad_del_aviso_suma(self):
        nuevo = self.ev.evaluar(_aviso(precio=84000.0), dias_visible=1)
        viejo = self.ev.evaluar(_aviso(precio=84000.0), dias_visible=150)
        self.assertGreater(viejo.puntaje, nuevo.puntaje)

    def test_referencia_floja_baja_la_confianza(self):
        flojo = Evaluador(_Tasador(n=3, origen="semilla"), self.cfg)
        e_flojo = flojo.evaluar(_aviso(precio=84000.0))
        e_firme = self.ev.evaluar(_aviso(precio=84000.0))
        self.assertEqual(e_flojo.confianza, "baja")
        self.assertLess(e_flojo.puntaje, e_firme.puntaje)


class TestFiltrosBasicos(unittest.TestCase):
    def setUp(self):
        self.cfg = cargar(recargar=True)

    def test_pasa_lo_buscado(self):
        self.assertEqual(pasa_filtros_basicos(_aviso(), self.cfg), "")

    def test_rechaza_ambientes(self):
        self.assertIn("ambientes", pasa_filtros_basicos(_aviso(ambientes=2), self.cfg))
        self.assertIn("ambientes", pasa_filtros_basicos(_aviso(ambientes=5), self.cfg))

    def test_rechaza_fuera_de_presupuesto(self):
        self.assertIn("presupuesto", pasa_filtros_basicos(_aviso(precio=300000.0), self.cfg))

    def test_rechaza_palabras_excluidas(self):
        a = _aviso(descripcion="Excelente unidad a estrenar en pozo")
        self.assertTrue(pasa_filtros_basicos(a, self.cfg))

    def test_rechaza_otro_barrio(self):
        a = _aviso(barrio="Palermo", titulo="Depto en Palermo", descripcion="Palermo")
        self.assertIn("fuera de zona", pasa_filtros_basicos(a, self.cfg))

    def test_rechaza_m2_fuera_de_rango(self):
        self.assertIn("mínimo", pasa_filtros_basicos(_aviso(m2=30.0), self.cfg))


if __name__ == "__main__":
    unittest.main()
