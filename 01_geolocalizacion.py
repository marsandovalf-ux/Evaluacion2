import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def preguntar(texto):
    valor = input(texto).strip()
    if valor.casefold() in {'s', 'salir'}:
        raise EOFError
    return valor


def consultar(recurso, parametros):
    url = 'https://graphhopper.com/api/1/' + recurso + '?' + urlencode(parametros)
    try:
        with urlopen(url, timeout=30) as respuesta:
            return json.load(respuesta)
    except HTTPError as error:
        raise ValueError(f'GraphHopper respondió con HTTP {error.code}. Revisa la clave, los lugares y el límite de consultas.') from None
    except (URLError, TimeoutError):
        raise ValueError('No se pudo conectar con GraphHopper.') from None


def localizar(lugar, clave):
    datos = consultar('geocode', {'q': lugar, 'locale': 'es', 'limit': 1, 'key': clave})
    if not datos.get('hits'):
        raise ValueError('No se encontró el lugar: ' + lugar)
    elegido = datos['hits'][0]
    print('Lugar encontrado: ' + ', '.join(str(elegido[c]) for c in ('name', 'city', 'country') if elegido.get(c)))
    punto = elegido['point']
    return f"{punto['lat']},{punto['lng']}"


def mostrar_ruta(ruta):
    print(f"Distancia total: {ruta['distance'] / 1000:.2f} km")
    print(f"Tiempo estimado: {ruta['time'] / 60000:.2f} minutos")
    print('Instrucciones del viaje:')
    for paso in ruta['instructions']:
        print(f"- {paso['text']} | {paso['distance'] / 1000:.2f} km | {paso['time'] / 60000:.2f} minutos")


def main():
    clave = os.environ.get('GRAPHHOPPER_API_KEY', '').strip()
    if not clave:
        print('Falta configurar GRAPHHOPPER_API_KEY con tu clave de GraphHopper.')
        return 1
    print("Planificador de viajes. Ingresa 's' o 'salir' para terminar.")
    try:
        while True:
            origen = preguntar('Origen (incluye ciudad y país): ')
            destino = preguntar('Destino (incluye ciudad y país): ')
            if not origen or not destino:
                print('Debes indicar origen y destino.')
                continue
            try:
                inicio = localizar(origen, clave)
                fin = localizar(destino, clave)
                datos = consultar('route', [('point', inicio), ('point', fin), ('profile', 'car'), ('locale', 'es'), ('instructions', 'true'), ('key', clave)])
                if not datos.get('paths'):
                    raise ValueError('No se encontró una ruta.')
                mostrar_ruta(datos['paths'][0])
            except ValueError as error:
                print('No se pudo calcular el viaje: ' + str(error))
    except (EOFError, KeyboardInterrupt):
        print('Programa finalizado. ¡Hasta pronto!')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
