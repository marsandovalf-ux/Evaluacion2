import base64
import getpass
import json
import random
import re
import string
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qsl
from urllib.request import Request, urlopen

BASE_URL = 'http://library.demo.local/api/v1'


def solicitar(metodo, ruta, token=None, cuerpo=None, basic=None, incluir_encabezados=False, intento=0):
    headers = {'Accept': 'application/json'}
    if token:
        headers['X-API-Key'] = token
    if basic:
        headers['Authorization'] = 'Basic ' + base64.b64encode(basic.encode()).decode()
    datos = None
    if cuerpo is not None:
        headers['Content-Type'] = 'application/json'
        datos = json.dumps(cuerpo, ensure_ascii=False).encode('utf-8')
    try:
        with urlopen(Request(BASE_URL + ruta, data=datos, headers=headers, method=metodo), timeout=30) as respuesta:
            raw = respuesta.read()
            print(f'{metodo} {ruta.split("?")[0]} -> HTTP {respuesta.status}')
            contenido = json.loads(raw) if raw else None
            return (contenido, dict(respuesta.headers)) if incluir_encabezados else contenido
    except HTTPError as error:
        if error.code == 429 and intento < 3:
            try:
                espera = min(120, max(1, float(error.headers.get('Retry-After', '60'))))
            except ValueError:
                espera = 60
            print(f'Límite de consultas HTTP 429. Se reintentará en {espera:.0f} segundos.')
            time.sleep(espera)
            return solicitar(metodo, ruta, token, cuerpo, basic, incluir_encabezados, intento + 1)
        raise ValueError(f'La biblioteca respondió con HTTP {error.code}. Revisa autenticación, IDs y documentación de la API.') from None
    except (URLError, TimeoutError):
        raise ValueError('No se pudo conectar a la biblioteca. Ejecuta dentro de DEVASC y verifica que esté activa.') from None


def listar(token):
                                                                              
    ruta = '/books?' + urlencode({'includeISBN': 'true', 'sortBy': 'author'})
    catalogo = []
    paginas = set()
    ids = set()
    while ruta:
        if ruta in paginas:
            raise ValueError('La API repitió un enlace de paginación.')
        paginas.add(ruta)
        datos, encabezados = solicitar('GET', ruta, token, incluir_encabezados=True)
        if not isinstance(datos, list):
            raise ValueError('El catálogo no tiene el formato esperado.')
        for libro in datos:
            identificador = int(libro['id'])
            if identificador in ids:
                raise ValueError('Se repitió un libro entre páginas del catálogo.')
            ids.add(identificador)
            catalogo.append(libro)
        enlace = next((v for k, v in encabezados.items() if k.lower() == 'link'), '')
        siguiente = re.search(r'<([^>]+)>;\s*rel="?next"?', enlace)
        ruta = None
        if siguiente:
            partes = urlsplit(siguiente.group(1))
            if partes.netloc and partes.netloc != urlsplit(BASE_URL).netloc:
                raise ValueError('La paginación apunta fuera de la biblioteca.')
            parametros = dict(parse_qsl(partes.query))
            parametros.update(includeISBN='true', sortBy='author')
            camino = partes.path
            prefijo = urlsplit(BASE_URL).path
            if camino.startswith(prefijo + '/'):
                camino = camino[len(prefijo):]
            ruta = camino + '?' + urlencode(parametros)
    catalogo.sort(key=lambda libro: str(libro.get('author', '')).casefold())
    print(f'Catálogo completo: {len(catalogo)} libros en {len(paginas)} páginas.')
    return catalogo


def isbn_aleatorio(usados):
    while True:
        base = '978' + ''.join(random.choices(string.digits, k=9))
        control = (-sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(base))) % 10
        isbn = base + str(control)
        if isbn not in usados:
            usados.add(isbn)
            return isbn


def generar(catalogo):
    autores = ['Ana', 'Bruno', 'Camila', 'Daniel', 'Elena', 'Felipe', 'Gabriela', 'Hugo', 'Inés', 'Javier']
    apellidos = ['Arias', 'Bravo', 'Castro', 'Díaz', 'Espinoza', 'Fuentes', 'García', 'Herrera', 'Ibarra', 'Lagos']
    temas = ['Redes', 'Python', 'Automatización', 'Seguridad', 'Microservicios', 'Telepresencia', 'Enrutamiento', 'APIs']
    enfoques = ['en la práctica', 'para profesionales', 'desde cero', 'en profundidad', 'con ejemplos', 'y sus fundamentos']
    usados = {str(libro.get('isbn', '')) for libro in catalogo}
    siguiente = max([7] + [int(libro['id']) for libro in catalogo]) + 1
    titulos = set()
    libros = []
    while len(libros) < 50:
        titulo = random.choice(temas) + ' ' + random.choice(enfoques) + ' - ' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if titulo in titulos:
            continue
        titulos.add(titulo)
        libros.append({'id': siguiente + len(libros), 'title': titulo, 'author': random.choice(autores) + ' ' + random.choice(apellidos), 'isbn': isbn_aleatorio(usados)})
    return libros


def main():
    print('Carga de 50 libros en la biblioteca DEVASC. Si existe el lote guardado, solo se verifica.')
    usuario = input('Usuario del laboratorio [cisco]: ').strip() or 'cisco'
    contrasena = getpass.getpass('Contraseña del laboratorio (no se muestra): ')
    try:
        sesion = solicitar('POST', '/loginViaBasic', basic=usuario + ':' + contrasena)
        token = sesion['token']
        destino = Path(__file__).with_name('03_libros_creados.json')
        if destino.exists():
            creados = json.loads(destino.read_text(encoding='utf-8'))
            if len(creados) != 50:
                raise ValueError(f'Hay un lote parcial de {len(creados)} libros. Revisar antes de agregar más.')
            print('El lote ya existe: se verificará sin crear libros adicionales.')
        else:
            anteriores = listar(token)
            lote = generar(anteriores)
            creados = []
            for libro in lote:
                solicitar('POST', '/books', token, libro)
                creados.append(libro)
                destino.write_text(json.dumps(creados, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f'Creado {len(creados)}/50 | ID {libro["id"]} | {libro["title"]} | {libro["author"]} | ISBN {libro["isbn"]}')
        catalogo = listar(token)
        por_id = {int(libro['id']): libro for libro in catalogo}
        for libro in creados:
            encontrado = por_id.get(libro['id'], {})
            if any(str(encontrado.get(campo)) != str(libro[campo]) for campo in ('title', 'author', 'isbn')):
                raise ValueError('El listado no confirmó todos los libros. Revisa el límite o la paginación de la API antes de repetir la carga.')
        print('\nVERIFICADO: los 50 libros del lote están en el catálogo.')
        print('Catálogo completo ordenado por autor, incluyendo ISBN:')
        print(json.dumps(catalogo, ensure_ascii=False, indent=2))
        destino = Path(__file__).with_name('03_libros_creados.json')
        destino.write_text(json.dumps(creados, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Lote guardado en:', destino.name)
    except (ValueError, KeyError) as error:
        print('No se completó la verificación:', error)
        print('Puede existir una carga parcial. Revisa el catálogo antes de volver a ejecutar.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
