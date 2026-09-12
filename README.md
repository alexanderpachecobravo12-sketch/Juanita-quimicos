# Sistema de Control de Inventario — Tienda de Insecticidas

Aplicación web para uso en red local (LAN) desde las computadoras de caja y almacén.

## Regla central del sistema

El inventario se mueve **solo con la cantidad física contada** (guía + conteo del
almacenero). La factura del proveedor **nunca** actualiza el stock: solo se usa para
registrar incidencias contables cuando no coincide con lo recibido físicamente.

## Instalación

Requiere Python 3.10+.

```bash
cd insecticidas_inventario
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python run.py
```

El servidor queda disponible en:

- Desde la misma computadora: http://localhost:5000
- Desde las otras computadoras de la red local: http://IP-DE-ESTA-COMPUTADORA:5000

(Para ver la IP de esta computadora en Windows: `ipconfig` y busca "Dirección IPv4").

La base de datos SQLite se crea automáticamente en `instance/inventario.db` la
primera vez que se ejecuta. También se crea un usuario administrador inicial:

- **Usuario:** admin
- **Contraseña:** admin123

Cambia esta contraseña de inmediato desde el menú **Usuarios** una vez que ingreses,
y crea ahí las cuentas individuales de cada cajero y del almacenero.

### Datos de ejemplo (opcional)

Para no arrancar con el catálogo vacío, puedes sembrar productos típicos de una
tienda de insecticidas y usuarios de ejemplo (2 cajeros + 1 almacenero) con:

```bash
.venv\Scripts\python.exe seed_data.py
```

Es seguro ejecutarlo varias veces: no duplica nada que ya exista. Las contraseñas
de ejemplo que crea (`cajero123`, `almacen123`) deben cambiarse antes de usar el
sistema en producción, desde el menú Usuarios.

## Flujo de uso

1. **Administrador**: crea el catálogo de productos (menú Catálogo) y las cuentas de
   cajeros/almacenero (menú Usuarios).
2. **Almacenero**: registra cada guía que llega en **Recepción**, indicando tanto la
   cantidad de la guía como la cantidad física contada. El stock se mueve con la
   cantidad física. Si un número de guía ya fue registrado para ese producto, el
   sistema lo bloquea.
3. **Cajero**: registra ventas en **Venta**, elige la terminal (Caja 1 / Caja 2 /
   Almacén) y genera el ticket (imprimible desde el navegador).
4. **Almacenero**: una vez por semana, hace el conteo físico y lo registra en
   **Cotejo semanal**; el sistema muestra la diferencia contra el saldo del sistema.
5. **Administrador o almacenero**: cuando llega la factura del proveedor y no
   coincide con la guía/físico, se registra en **Incidencias** (no toca el stock).
   El administrador las marca como resueltas.
6. **Administrador**: en **Reportes** puede ver el historial de movimientos de cada
   producto y las incidencias pendientes, y exportarlos a Excel o CSV.

## Fuera de alcance de esta primera versión

- Integración directa con las ticketeras físicas (se imprime desde el navegador).
- Devoluciones y envíos.
- Múltiples sucursales.
- Integración automática con facturación electrónica del proveedor.
