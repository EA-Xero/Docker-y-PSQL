# 🌐 Taller de Redes — Proyecto General

> **Objetivo general:** Explorar de forma práctica el comportamiento de una arquitectura cliente-servidor de base de datos (PostgreSQL) sobre una red virtualizada con Docker, avanzando desde la **observación pasiva** del tráfico hasta la **manipulación activa** del mismo.

Este repositorio agrupa dos entregas independientes pero complementarias, cada una en su propia carpeta, ya que abordan objetivos y niveles de complejidad distintos dentro del mismo taller.

```
.
├── Tarea-2/
│   └── Readme.md      → Captura y análisis pasivo de tráfico (sniffing con Wireshark/tshark)
└── Tarea-3/
    └── Readme.md      → Interceptación y modificación activa de tráfico (ataque MitM con Scapy)
```

---

## 📋 Tabla de Contenidos

1. [Relación entre ambas tareas](#1--relación-entre-ambas-tareas)
2. [Tarea-2: Captura y análisis pasivo de tráfico](#2--tarea-2-captura-y-análisis-pasivo-de-tráfico)
3. [Tarea-3: Ataque MitM (interceptación activa)](#3--tarea-3-ataque-mitm-interceptación-activa)
4. [Comparación de requerimientos](#4--comparación-de-requerimientos)
5. [Estructura completa del repositorio](#5--estructura-completa-del-repositorio)

---

## 1. 🔗 Relación entre ambas tareas

Ambas tareas comparten la misma base conceptual (un servidor PostgreSQL y un cliente conectándose a él dentro de una red Docker), pero difieren en **el rol que cumple la red** y **qué tan invasiva es la observación**:

| | Tarea-2 | Tarea-3 |
|---|---|---|
| **Rol de la red** | Punto de escucha pasivo (sniffer) | Punto de intermediación activa (router/MitM) |
| **Acción sobre el tráfico** | Solo se observa y se guarda | Se intercepta, se reconstruye y se modifica |
| **Herramienta principal** | `tshark` / Wireshark | `Scapy` + `NetfilterQueue` |
| **¿El tráfico llega intacto al destino?** | Sí, siempre | No necesariamente — puede alterarse antes de reenviarse |
| **Entorno de ejecución** | Windows + WSL + Docker Desktop | Contenedores Linux (Alpine) puros |
| **Pregunta que responde** | *"¿Qué información viaja por la red y en qué formato?"* | *"¿Qué tan fácil es alterar esa información sin que las partes lo detecten?"* |

En otras palabras: **Tarea-2 es el diagnóstico** (ver que las contraseñas y consultas SQL viajan en texto plano) y **Tarea-3 es la demostración de la consecuencia** (si viaja en texto plano, un intermediario no solo puede leerlo, sino modificarlo).

---

## 2. 📡 Tarea-2: Captura y análisis pasivo de tráfico

📁 Ver detalle completo en [`Tarea-2/Readme.md`](./Tarea-2/Readme.md)

### Intención del apartado
El objetivo de esta tarea **no es alterar nada**, sino comprobar, mediante un sniffer, que el tráfico entre el cliente y el servidor PostgreSQL viaja **sin cifrado**. Se busca que las consultas SQL, los datos insertados y la contraseña de conexión queden visibles en una captura `.pcapng`, evidenciando el riesgo de no usar SSL/TLS.

### Requerimientos específicos de esta tarea
- Entorno **Windows** con WSL, Docker Desktop, Git Bash y Wireshark instalados aparte.
- Tres servicios definidos en `docker-compose.yml`: `db-server`, `db-client` y `network_analyzer`, unidos por una red `bridge` (`red-taller`).
- El contenedor `network_analyzer` actúa como un **sniffer pasivo**: solo escucha el tráfico que ya existe en la red, sin modificar rutas ni reenvíos.
- Uso de `tshark` para capturar el tráfico del puerto 5432 y guardarlo en disco.
- Ejecución de operaciones SQL reales (`CREATE TABLE`, `INSERT`, `UPDATE`, `SELECT`) mientras la captura está activa, para generar tráfico representativo.
- Análisis posterior del archivo `.pcapng` en Wireshark (patrones de comunicación, estadísticas, anomalías).

### Resultado esperado
Un archivo `.pcapng` que, al abrirse en Wireshark, permite **leer en texto plano** el contenido de las consultas SQL y las credenciales usadas, demostrando la falta de cifrado del protocolo tal como se configuró.

---

## 3. 🕵️ Tarea-3: Ataque MitM (interceptación activa)

📁 Ver detalle completo en [`Tarea-3/Readme.md`](./Tarea-3/Readme.md)

### Intención del apartado
A diferencia de la Tarea-2, aquí el objetivo es **intervenir activamente** el tráfico: forzar a que los paquetes pasen obligatoriamente por un tercer contenedor (`psql_firewall`) que actúa como intermediario de red, y usar ese punto de control para **interceptar, reconstruir y modificar** paquetes TCP dirigidos al puerto 5432 antes de reenviarlos a su destino.

### Requerimientos específicos de esta tarea
- Entorno basado en contenedores Linux **Alpine** (`psql_client`, `psql_server`, `psql_firewall`), sin dependencia de Windows/WSL.
- Redes segmentadas en **dos subredes distintas** (una para el cliente, otra para el servidor), con `psql_firewall` puenteando ambas.
- Reconfiguración manual de las **rutas por defecto** del cliente y del servidor para que todo el tráfico pase forzosamente por el firewall.
- Instalación de herramientas de compilación y librerías de bajo nivel (`libnetfilter_queue-dev`, `linux-headers`, `gcc`, etc.) necesarias para `NetfilterQueue`.
- Uso de `iptables` con `NFQUEUE` para desviar el tráfico del puerto 5432 hacia el script de intercepción, deteniendo momentáneamente el reenvío automático del kernel.
- Script propio en **Scapy/Python** (`MitM_psql.py`) que recibe los paquetes desde la cola, los modifica y decide si reenviarlos.
- Prueba de la intercepción realizando una consulta real desde `pgcli` y observando el efecto provocado sobre esa consulta.

### Resultado esperado
Evidencia de que un paquete PostgreSQL fue capturado, alterado por el script y reenviado (o descartado), junto con un análisis de la falla o comportamiento anómalo que esto provoca en el cliente o el servidor, y una reflexión sobre las mitigaciones posibles (por ejemplo, forzar `sslmode=require`).

---

## 4. ⚖️ Comparación de requerimientos

| Requerimiento | Tarea-2 | Tarea-3 |
|---|:---:|:---:|
| Docker Compose | ✅ | ✅ (implícito, contenedores propios) |
| Sistema operativo host | Windows + WSL | Independiente del host (Linux en contenedores) |
| Herramienta de captura/análisis | `tshark` / Wireshark | — |
| Herramienta de intercepción/modificación | — | `Scapy` + `NetfilterQueue` |
| Modificación de rutas de red | ❌ No requerido | ✅ Requerido (cliente y servidor) |
| Uso de `iptables` | ❌ No requerido | ✅ Requerido (`NFQUEUE`) |
| Compilación de dependencias nativas | ❌ No requerido | ✅ Requerido (headers, gcc, etc.) |
| Consultas SQL de prueba | ✅ (para generar tráfico observable) | ✅ (para probar la intercepción) |
| Nivel de intervención sobre el tráfico | Ninguna (solo lectura) | Activa (modificación de paquetes) |

---

## 5. 🗂️ Estructura completa del repositorio

```
.
├── Tarea-2/
│   ├── Readme.md              # Guía de instalación, despliegue y captura pasiva
│   └── docker-compose.yml     # Definición de db-server, db-client y network_analyzer
│
└── Tarea-3/
    ├── Readme.md              # Guía de despliegue y ataque MitM
    ├── docker-compose.yml     # Definición de psql_client, psql_server y psql_firewall
    └── MitM_psql.py           # Script de interceptación en Scapy
```

> ⚠️ **Nota general:** ambos laboratorios deben ejecutarse exclusivamente en los entornos Docker aislados definidos para el taller, con fines estrictamente educativos. No deben aplicarse las técnicas de la Tarea-3 sobre redes o sistemas ajenos al entorno del laboratorio.
