# Evaluacion2

Autor: Marcelo Sandoval.

## Archivos

- 01_geolocalizacion.py: consulta lugares y rutas de GraphHopper en español, muestra distancia y tiempo con dos decimales y permite salir con s o salir.
- 02_preparar_postman.py: genera la colección de solicitudes para los tres libros, consulta, actualización y catálogo.
- 03_cargar_50_libros.py: crea un lote de 50 libros aleatorios y verifica el catálogo completo con paginación.

## Ejecución en DEVASC

Requiere Python 3.8 o posterior. No necesita instalar paquetes adicionales.

Para rutas, configura la clave en la misma sesión desde la que iniciarás el programa:

```sh
export GRAPHHOPPER_API_KEY='TU_CLAVE'
python3 01_geolocalizacion.py
```

Escribe lugares con ciudad y país. Se utiliza la primera coincidencia y el perfil de automóvil. Puedes escribir s o salir en origen o destino.

Para preparar Postman:

```sh
python3 02_preparar_postman.py
```

Ingresa el RUT sin puntos ni guion. Importa la colección generada en Postman y completa usuario y contrasena con las credenciales de la biblioteca. El token de biblioteca se obtiene con la primera solicitud; es distinto de la clave de GraphHopper. No repitas las altas si los IDs 5, 6 y 7 ya existen.

El catálogo acepta includeISBN=true, sortBy=author y page. Devuelve diez libros por página. Para revisar todo en Postman, avanza page desde 1 hasta que no haya enlace next. Mantén el cuerpo de las solicitudes GET en none.

Para el lote de libros:

```sh
python3 03_cargar_50_libros.py
```

Ingresa las credenciales de biblioteca cuando se soliciten. El programa guarda el lote en 03_libros_creados.json. Si ese archivo contiene los 50 registros, las siguientes ejecuciones solo verifican el lote. Conserva ese archivo para evitar duplicar la carga. Una carga parcial requiere revisión antes de continuar.

El listado recorre los enlaces next, mantiene ISBN en cada página, ordena el resultado completo por autor y compara título, autor e ISBN de los 50 registros. Las respuestas HTTP 429 se reintentan respetando Retry-After.

## Pruebas realizadas

En DEVASC se confirmaron con HTTP 200 las altas 5, 6 y 7, la consulta de 5 y la actualización de su título. Se crearon 50 libros, IDs 8 a 57. El catálogo completo contiene 57 registros en seis páginas. Una segunda ejecución verificó el lote sin crear registros adicionales.

GraphHopper devolvió una ruta real entre Plaza de Armas y Biblioteca Nacional de Chile, Santiago: 3,17 km y 6,22 minutos. Se comprobaron instrucciones en español y salidas con s y salir. Los resultados pueden cambiar en futuras consultas.

Las pruebas automatizadas suministraron los valores de entrada al programa y usaron los servicios reales. Los archivos temporales de prueba no forman parte del código de entrega.

## Capturas y entrega

Repositorio: https://github.com/marsandovalf-ux/Evaluacion2 . Las capturas y el informe se entregan por separado.

Las claves se configuran fuera del código. No subas claves, contraseñas, la colección con el RUT ni el archivo privado del lote a GitHub.

