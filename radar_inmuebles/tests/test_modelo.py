import unittest

from radar_inmuebles.modelo import Aviso, construir


def _aviso(**kw):
    base = dict(fuente="zonaprop", id_externo="1", url="http://x", barrio="Caballito",
                precio_usd=96000.0, m2_totales=70.0, ambientes=3)
    base.update(kw)
    return Aviso(**base)


class TestAviso(unittest.TestCase):
    def test_precio_m2_usa_cubiertos(self):
        a = _aviso(m2_totales=80.0, m2_cubiertos=70.0)
        self.assertEqual(a.m2_ref(), 70.0)
        self.assertAlmostEqual(a.precio_m2(), 96000 / 70)

    def test_sin_datos_no_hay_precio_m2(self):
        self.assertIsNone(_aviso(m2_totales=None).precio_m2())
        self.assertIsNone(_aviso(precio_usd=None).precio_m2())

    def test_dedupe_agrupa_el_mismo_depto_en_dos_portales(self):
        a = _aviso(fuente="zonaprop", id_externo="111", precio_usd=96000.0, m2_totales=70.0)
        b = _aviso(fuente="argenprop", id_externo="222", precio_usd=95500.0, m2_totales=71.0)
        self.assertEqual(a.clave_dedupe(), b.clave_dedupe())

    def test_dedupe_separa_deptos_distintos(self):
        a = _aviso(precio_usd=96000.0, m2_totales=70.0)
        b = _aviso(fuente="argenprop", id_externo="2", precio_usd=140000.0, m2_totales=95.0)
        self.assertNotEqual(a.clave_dedupe(), b.clave_dedupe())

    def test_dedupe_sin_datos_cae_al_id(self):
        a = _aviso(m2_totales=None)
        self.assertEqual(a.clave_dedupe(), a.id)

    def test_ida_y_vuelta_a_dict(self):
        a = construir("ml", "99", "http://y", titulo="Depto", precio="U$S 95.000",
                      m2_totales="68 m²", ambientes="3 amb", publicado="2026-01-10")
        b = Aviso.desde_dict(a.a_dict())
        self.assertEqual(b.ambientes, 3)
        self.assertEqual(b.m2_totales, 68)
        self.assertEqual(b.publicado.year, 2026)


class TestConstructor(unittest.TestCase):
    def test_parsea_strings_crudos(self):
        a = construir("argenprop", "7", "http://z", ambientes="3 amb.",
                      m2_totales="72 m² tot.", m2_cubiertos="65 m² cub.")
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.m2_totales, 72)
        self.assertEqual(a.m2_cubiertos, 65)

    def test_ignora_campos_desconocidos(self):
        a = construir("x", "1", "u", campo_inventado="chau")
        self.assertFalse(hasattr(a, "campo_inventado"))


if __name__ == "__main__":
    unittest.main()
