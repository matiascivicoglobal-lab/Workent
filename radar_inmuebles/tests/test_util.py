import unittest
from datetime import timedelta

from radar_inmuebles.util import (ahora, dias_desde, mediana, parse_ambientes,
                                  parse_fecha, parse_m2, parse_numero,
                                  parse_precio, percentil, sin_outliers, slug)


class TestNumeros(unittest.TestCase):
    def test_formato_argentino(self):
        self.assertEqual(parse_numero("1.234.567"), 1234567)
        self.assertEqual(parse_numero("1.234,56"), 1234.56)
        self.assertEqual(parse_numero("68,5"), 68.5)
        self.assertEqual(parse_numero("95000"), 95000)
        self.assertIsNone(parse_numero("sin numeros"))

    def test_precios(self):
        casos = [
            ("U$S 95.000", 95000, "USD"),
            ("us$ 120.000", 120000, "USD"),
            ("USD 89.900", 89900, "USD"),
            ("$ 120.000.000", 120000000, "ARS"),
            ("AR$ 95.500.000", 95500000, "ARS"),
        ]
        for texto, monto, moneda in casos:
            with self.subTest(texto=texto):
                self.assertEqual(parse_precio(texto), (monto, moneda))

    def test_precio_a_consultar(self):
        self.assertEqual(parse_precio("Precio a consultar"), (None, None))
        self.assertEqual(parse_precio(""), (None, None))

    def test_m2(self):
        self.assertEqual(parse_m2("68 m²"), 68)
        self.assertEqual(parse_m2("72,5 m2 totales"), 72.5)
        self.assertEqual(parse_m2("120 mts2"), 120)
        self.assertIsNone(parse_m2("5 m²"), "5 m² no es un departamento")
        self.assertIsNone(parse_m2("sin dato"))

    def test_ambientes(self):
        self.assertEqual(parse_ambientes("3 amb."), 3)
        self.assertEqual(parse_ambientes("4 ambientes"), 4)
        self.assertEqual(parse_ambientes("Monoambiente"), 1)
        self.assertEqual(parse_ambientes(3), 3)
        self.assertIsNone(parse_ambientes("99 ambientes"))


class TestFechas(unittest.TestCase):
    def test_relativas(self):
        d = parse_fecha("Publicado hace 45 días")
        self.assertIsNotNone(d)
        self.assertAlmostEqual(dias_desde(d), 45, delta=1)

    def test_iso_y_epoch(self):
        self.assertEqual(parse_fecha("2026-03-15T10:00:00Z").year, 2026)
        self.assertEqual(parse_fecha("15/03/2026").month, 3)
        self.assertIsNotNone(parse_fecha(1710500000))
        self.assertIsNotNone(parse_fecha(1710500000000))

    def test_dias_desde(self):
        self.assertEqual(dias_desde(ahora() - timedelta(days=10)), 10)
        self.assertIsNone(dias_desde(None))


class TestEstadistica(unittest.TestCase):
    def test_mediana_y_percentiles(self):
        xs = [1, 2, 3, 4, 5]
        self.assertEqual(mediana(xs), 3)
        self.assertEqual(percentil(xs, 0.0), 1)
        self.assertEqual(percentil(xs, 1.0), 5)
        self.assertIsNone(mediana([]))

    def test_outliers_fuera(self):
        # Una ganga y un delirio no deben mover la mediana de la zona.
        xs = [2000, 2100, 2200, 2150, 2050, 2250, 2180, 2120, 300, 9000]
        limpio = sin_outliers(xs)
        self.assertNotIn(300, limpio)
        self.assertNotIn(9000, limpio)
        self.assertGreater(mediana(limpio), 2000)

    def test_muestra_chica_no_se_recorta(self):
        self.assertEqual(len(sin_outliers([1, 500])), 2)


class TestSlug(unittest.TestCase):
    def test_barrios(self):
        self.assertEqual(slug("Villa Luro"), "villa-luro")
        self.assertEqual(slug("Caballito"), "caballito")
        self.assertEqual(slug("Pompeya / Nva Pompeya"), "pompeya-nva-pompeya")


if __name__ == "__main__":
    unittest.main()
