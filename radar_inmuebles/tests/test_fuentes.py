"""Los parsers contra HTML/JSON de muestra, sin tocar la red."""

import json
import unittest
from pathlib import Path

from radar_inmuebles.fuentes.argenprop import Argenprop
from radar_inmuebles.fuentes.comun import datos_desde_texto, buscar_avisos_json
from radar_inmuebles.fuentes.mercadolibre import MercadoLibre
from radar_inmuebles.fuentes.properati import Properati, _parece_aviso
from radar_inmuebles.fuentes.zonaprop import Zonaprop
from radar_inmuebles.tests import cfg_test

FIXTURES = Path(__file__).parent / "fixtures"


def leer(nombre):
    return (FIXTURES / nombre).read_text(encoding="utf-8")


class _ClienteFalso:
    """Devuelve siempre el mismo contenido: no hay red en los tests."""
    def __init__(self, contenido=None, json_datos=None, ultimo_codigo=200):
        self.contenido, self.json_datos = contenido, json_datos
        self.ultimo_codigo = ultimo_codigo
        self.urls = []

    def html(self, url, **kw):
        self.urls.append(url)
        return self.contenido

    def json(self, url, **kw):
        self.urls.append(url)
        return self.json_datos


class TestDatosDesdeTexto(unittest.TestCase):
    def test_tarjeta_tipica(self):
        d = datos_desde_texto("USD 96.000 · 72 m² tot. 68 m² cub. · 3 amb. 2 dorm. 1 baño")
        self.assertEqual(d["precio"], 96000)
        self.assertEqual(d["moneda"], "USD")
        self.assertEqual(d["m2_totales"], 72)
        self.assertEqual(d["m2_cubiertos"], 68)
        self.assertEqual(d["ambientes"], 3)
        self.assertEqual(d["dormitorios"], 2)
        self.assertEqual(d["banios"], 1)

    def test_pesos(self):
        d = datos_desde_texto("$ 165.000.000 · 88 m² · 3 amb.")
        self.assertEqual(d["precio"], 165000000)
        self.assertEqual(d["moneda"], "ARS")

    def test_expensas(self):
        d = datos_desde_texto("USD 96.000 Expensas: $ 85.000")
        self.assertEqual(d["expensas_ars"], 85000)


class TestArgenprop(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()
        self.fuente = Argenprop(_ClienteFalso(leer("argenprop_listado.html")), self.cfg)

    def test_parsea_el_listado(self):
        avisos = self.fuente._parsear_listado(leer("argenprop_listado.html"),
                                              "caballito", "departamento")
        self.assertEqual(len(avisos), 3)

    def test_datos_del_primer_aviso(self):
        a = self.fuente._parsear_listado(leer("argenprop_listado.html"),
                                         "caballito", "departamento")[0]
        self.assertEqual(a.id_externo, "12345678")
        self.assertEqual(a.precio, 96000)
        self.assertEqual(a.moneda, "USD")
        self.assertEqual(a.m2_totales, 72)
        self.assertEqual(a.m2_cubiertos, 68)
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.banios, 1)
        self.assertIn("Rivadavia", a.direccion)
        self.assertTrue(a.url.startswith("https://www.argenprop.com/"))
        self.assertIn("reciclar", a.descripcion.lower())

    def test_detecta_ph(self):
        avisos = self.fuente._parsear_listado(leer("argenprop_listado.html"),
                                              "caballito", "departamento")
        self.assertEqual(avisos[1].tipo, "ph")

    def test_sin_precio_se_parsea_igual(self):
        a = self.fuente._parsear_listado(leer("argenprop_listado.html"),
                                         "caballito", "departamento")[2]
        self.assertIsNone(a.precio)
        self.assertEqual(a.ambientes, 3)

    def test_url_de_busqueda(self):
        url = self.fuente._url("departamento", "villa luro", 2)
        self.assertIn("villa-luro", url)
        self.assertIn("3-ambientes", url)
        self.assertIn("pagina-2", url)


class TestZonaprop(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()
        self.fuente = Zonaprop(_ClienteFalso(), self.cfg)

    def test_parsea_tarjetas_data_qa(self):
        avisos = self.fuente._desde_html(leer("zonaprop_listado.html"),
                                         "caballito", "departamento")
        self.assertEqual(len(avisos), 2)
        a = avisos[0]
        self.assertEqual(a.id_externo, "51234567")
        self.assertEqual(a.precio, 94000)
        self.assertEqual(a.moneda, "USD")
        self.assertEqual(a.m2_totales, 70)
        self.assertEqual(a.m2_cubiertos, 64)
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.expensas_ars, 92000)
        self.assertIn("refaccionar", a.descripcion.lower())

    def test_precio_en_pesos(self):
        a = self.fuente._desde_html(leer("zonaprop_listado.html"),
                                    "caballito", "departamento")[1]
        self.assertEqual(a.precio, 165000000)
        self.assertEqual(a.moneda, "ARS")

    def test_url_de_busqueda(self):
        url = self.fuente._url("departamento", "villa luro", 1)
        self.assertIn("departamentos-venta-villa-luro-3-ambientes", url)
        self.assertNotIn("pagina", url)


class TestProperati(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()
        self.fuente = Properati(_ClienteFalso(leer("properati_listado.html")), self.cfg)

    def test_encuentra_los_avisos_en_el_json(self):
        crudos = buscar_avisos_json(leer("properati_listado.html"), _parece_aviso)
        self.assertEqual(len(crudos), 2)

    def test_parsea_precio_plano_y_anidado(self):
        crudos = buscar_avisos_json(leer("properati_listado.html"), _parece_aviso)
        a = self.fuente._parsear(crudos[0], "villa luro", "departamento")
        self.assertEqual(a.precio, 79000)
        self.assertEqual(a.moneda, "USD")
        self.assertEqual(a.m2_totales, 68)
        self.assertEqual(a.m2_cubiertos, 62)
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.publicado.year, 2026)
        self.assertIn("refaccionar", a.descripcion.lower())

        b = self.fuente._parsear(crudos[1], "villa luro", "departamento")
        self.assertEqual(b.precio, 112000)
        self.assertEqual(b.moneda, "USD")


class TestMercadoLibre(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_test()
        self.datos = json.loads(leer("mercadolibre_busqueda.json"))
        self.fuente = MercadoLibre(_ClienteFalso(json_datos=self.datos), self.cfg)

    def test_parsea_atributos(self):
        a = self.fuente._parsear(self.datos["results"][0], "liniers", "departamento")
        self.assertEqual(a.id_externo, "MLA1234567890")
        self.assertEqual(a.precio, 72000)
        self.assertEqual(a.moneda, "USD")
        self.assertEqual(a.m2_totales, 65)
        self.assertEqual(a.m2_cubiertos, 60)
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.dormitorios, 2)
        self.assertEqual(a.banios, 1)
        self.assertEqual(a.barrio, "Liniers")
        self.assertEqual(a.publicado.year, 2026)

    def test_descarta_otro_barrio(self):
        # ML mete resultados de toda la ciudad con el mismo `q`.
        a = self.fuente._parsear(self.datos["results"][1], "liniers", "departamento")
        self.assertIsNone(a)


class TestMercadoLibreWeb(unittest.TestCase):
    """Desde 2024 la API pública pide token: hay que leer el sitio."""

    def setUp(self):
        self.cfg = cfg_test()
        self.html = leer("mercadolibre_web.html")
        self.fuente = MercadoLibre(_ClienteFalso(self.html), self.cfg)

    def test_parsea_las_tarjetas(self):
        avisos = self.fuente._parsear_web(self.html, "caballito", "departamento")
        # El de Palermo y el que no tiene precio quedan afuera.
        self.assertEqual(len(avisos), 2)

    def test_datos_del_aviso_en_dolares(self):
        a = self.fuente._parsear_web(self.html, "caballito", "departamento")[0]
        self.assertEqual(a.id_externo, "MLA1234567890")
        self.assertEqual(a.precio, 96000)
        self.assertEqual(a.moneda, "USD")
        self.assertEqual(a.m2_totales, 65)
        self.assertEqual(a.ambientes, 3)
        self.assertEqual(a.banios, 1)
        self.assertIn("Caballito", a.barrio)
        self.assertNotIn("#position", a.url, "la url tiene que venir limpia")
        self.assertTrue(a.imagen)

    def test_precio_en_pesos_y_ph(self):
        a = self.fuente._parsear_web(self.html, "caballito", "departamento")[1]
        self.assertEqual(a.precio, 165000000)
        self.assertEqual(a.moneda, "ARS")
        self.assertEqual(a.m2_totales, 88)
        self.assertEqual(a.m2_cubiertos, 72)
        self.assertEqual(a.tipo, "ph")

    def test_descarta_otro_barrio(self):
        ids = [a.id_externo for a in
               self.fuente._parsear_web(self.html, "caballito", "departamento")]
        self.assertNotIn("MLA5555555555", ids)

    def test_descarta_sin_precio(self):
        ids = [a.id_externo for a in
               self.fuente._parsear_web(self.html, "caballito", "departamento")]
        self.assertNotIn("MLA4444444444", ids)

    def test_url_de_busqueda(self):
        url = self.fuente._url_web("departamento", "villa luro", 0)
        self.assertIn("departamentos/venta/capital-federal/villa-luro", url)
        self.assertIn("3-ambientes", url)
        self.assertNotIn("_Desde_", url)
        self.assertIn("_Desde_51", self.fuente._url_web("departamento", "liniers", 1))

    def test_pasa_a_web_si_la_api_bloquea(self):
        cliente = _ClienteFalso(self.html, json_datos=None, ultimo_codigo=403)
        fuente = MercadoLibre(cliente, self.cfg)
        avisos = fuente.buscar("caballito")
        self.assertTrue(fuente._modo_web, "debería haber cambiado de camino")
        self.assertTrue(avisos)

    def test_no_pasa_a_web_si_la_api_anda(self):
        datos = json.loads(leer("mercadolibre_busqueda.json"))
        fuente = MercadoLibre(_ClienteFalso(json_datos=datos, ultimo_codigo=200), self.cfg)
        fuente.buscar("liniers")
        self.assertFalse(fuente._modo_web)


if __name__ == "__main__":
    unittest.main()
