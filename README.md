# Chat privado (dos participantes)

Aplicación Flask para mensajería entre dos participantes. Cada persona entra seleccionando un identificador de color (Rosa o Azul); no se solicitan nombres ni apodos.

## Funciones
- Diseño sobrio y formal en tonos oscuros con acentos suaves.
- Indicador de conexión activa/desconectada de la otra persona.
- Indicador de escritura en tiempo real aproximado.
- Mensajes con hora y opción para eliminar los propios.
- Interfaz adaptable a teléfonos y computadoras.
- Servidor local en el puerto 5000.

## Ejecutar en local
```bash
pip install -r requirements.txt
python app.py
```
Abre `http://127.0.0.1:5000`.

## Configuración importante
La contraseña inicial está en `app.py` como `SECRET_PASSWORD = "1234"`. Cámbiala antes de publicar el sitio.

**Nota:** esta versión conserva el almacenamiento en memoria del proyecto original. Los mensajes y estados se reinician si el servidor se reinicia o entra en reposo. Para conservar mensajes en Render se necesita conectar una base de datos. El estado activo se actualiza cada pocos segundos y pasa a desconectado tras aproximadamente 25 segundos sin señal.


### Eliminación de mensajes

Los dos participantes pueden eliminar cualquier mensaje de la conversación, tanto los propios como los enviados por la otra persona. Al eliminarlo, desaparece para ambos.
