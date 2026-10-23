import json
import re
from pathlib import Path


def peticion(nombre, metodo, ruta, cuerpo=None, autenticada=True):
    encabezados = [{'key': 'Accept', 'value': 'application/json'}]
    if autenticada:
        encabezados.append({'key': 'X-API-Key', 'value': '{{token_biblioteca}}'})
    solicitud = {'method': metodo, 'header': encabezados, 'url': '{{base_url}}' + ruta}
    if cuerpo is not None:
        encabezados.append({'key': 'Content-Type', 'value': 'application/json'})
        solicitud['body'] = {'mode': 'raw', 'raw': json.dumps(cuerpo, ensure_ascii=False, indent=2), 'options': {'raw': {'language': 'json'}}}
    return {'name': nombre, 'request': solicitud}


def preparar(rut):
    autor = 'Marcelo_Sandoval'
    titulos = ['Guía de Estudio Para la Certificación Ccna Security', 'Redes Cisco. CCNA Routing y Switching.', 'Redes Avanzadas 1. DEVNET.']
    libros = [{'id': i, 'title': titulo, 'author': autor, 'isbn': rut} for i, titulo in enumerate(titulos, 5)]
    login = peticion('01 - Obtener token de biblioteca', 'POST', '/loginViaBasic', autenticada=False)
    login['request']['auth'] = {'type': 'basic', 'basic': [{'key': 'username', 'value': '{{usuario}}', 'type': 'string'}, {'key': 'password', 'value': '{{contrasena}}', 'type': 'string'}]}
    login['event'] = [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': ['pm.test("Autenticación correcta", () => pm.expect(pm.response.code).to.be.within(200, 299));', 'if (pm.response.code >= 200 && pm.response.code < 300) { const d = pm.response.json(); if (d.token) pm.collectionVariables.set("token_biblioteca", d.token); }']}}]
    items = [login]
    for numero, libro in enumerate(libros, 2):
        items.append(peticion(f'{numero:02} - Crear libro {libro["id"]}', 'POST', '/books', libro))
    items.append(peticion('05 - Consultar libro 5', 'GET', '/books/5?includeISBN=true'))
    actualizado = dict(libros[0], title='Guía de Estudio para la Certificación CCNA Security V2.0')
    items.append(peticion('06 - Actualizar libro 5', 'PUT', '/books/5', actualizado))
    items.append(peticion('07 - Catálogo por autor con ISBN', 'GET', '/books?includeISBN=true&sortBy=author&page=1'))
    for item in items[1:]:
        item['event'] = [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': ['pm.test("Operación correcta", () => pm.expect(pm.response.code).to.be.within(200, 299));']}}]
    return {'info': {'name': 'Evaluacion2 - Marcelo Sandoval', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'}, 'variable': [{'key': 'base_url', 'value': 'http://library.demo.local/api/v1'}, {'key': 'usuario', 'value': 'cisco'}, {'key': 'contrasena', 'value': ''}, {'key': 'token_biblioteca', 'value': ''}], 'item': items}


def main():
    rut = input('Ingresa tu RUT sin puntos ni guion (se usará como ISBN): ').strip().upper()
    if not re.fullmatch(r'[0-9]{7,8}[0-9K]', rut):
        print('Formato inválido. Usa solo los números y el dígito verificador, sin puntos ni guion.')
        return 1
    destino = Path(__file__).with_name('02_biblioteca.postman_collection.json')
    destino.write_text(json.dumps(preparar(rut), ensure_ascii=False, indent=2), encoding='utf-8')
    print('Colección preparada:', destino.name)
    print('Importa la colección en Postman dentro de DEVASC. Completa la variable contrasena del laboratorio y ejecuta las solicitudes en orden.')
    print('Revisa la documentación local /api/v1/docs si algún parámetro es rechazado.')
    print('La colección contiene tu RUT: no la subas al repositorio público.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
