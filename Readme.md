# 🌐 Taller de Redes — Guía de Procedimiento

> **Objetivo del proyecto:** Desplegar una infraestructura virtualizada con contenedores Docker que simule una arquitectura cliente-servidor de base de datos, con captura y análisis de tráfico de red en tiempo real.

---

## 📋 Tabla de Contenidos

1. [Instalación de Herramientas](#1--instalación-de-herramientas)
2. [Configuración con Docker Compose](#2--configuración-con-docker-compose)
3. [Despliegue y Conexión](#3--despliegue-y-conexión)
4. [Captura de Tráfico de Red](#4--captura-de-tráfico-de-red)
5. [Consultas SQL de Prueba](#5--consultas-sql-de-prueba)
6. [Análisis con Wireshark](#6--análisis-con-wireshark)

---

## 1. 🛠 Instalación de Herramientas

> **Contexto:** El proyecto se desarrolla sobre **Windows**, por lo que se requieren herramientas de compatibilidad con Linux y contenedores.

### Herramientas necesarias

| Herramienta | Propósito |
|---|---|
| **Windows Subsystem for Linux (WSL)** | Permite ejecutar un entorno Linux dentro de Windows |
| **Docker Desktop + Docker CLI** | Motor de contenedores y su interfaz gráfica |
| **Git Bash** | Terminal compatible con comandos Unix en Windows |

### ⚠️ Nota importante de instalación

- Al instalar **Docker Desktop**, se incluye automáticamente el **Docker CLI** y el **WSL**.
- **Git Bash** debe instalarse **por separado** (no viene incluido con Docker).

---

## 2. ⚙️ Configuración con Docker Compose

La infraestructura completa se define y levanta usando un único archivo `docker-compose.yml`. Esto crea todos los servicios, sus configuraciones y la red virtual de forma automática.

> 📁 Los archivos de configuración y evidencias fotográficas se encuentran en:
> `Tarea 2 Taller de Redes/Evidencias/Fotos`

### 🐳 Contenedores definidos

#### `db-server` — Servidor de Base de Datos
- Usa la imagen oficial de **PostgreSQL**
- Configura automáticamente usuario, contraseña y base de datos de prueba

#### `db-client` — Cliente de Base de Datos
- Basado en una imagen ligera de **Python**
- Instala `pgcli` y bibliotecas necesarias al iniciarse
- Queda en espera para interacción manual desde terminal

#### `red-taller` — Red Virtual
- Red de tipo **bridge** que interconecta todos los contenedores
- El cliente se conecta al servidor usando el nombre del servicio (`db-server`) como hostname

#### `network_analyzer` — Analizador de Tráfico
- Contenedor separado que escucha y registra el tráfico de red del `db-server`

---

### 🔑 Parámetros principales de configuración

```env
POSTGRES_USER=taller_user
POSTGRES_PASSWORD=taller_password
POSTGRES_DB=taller_redes
```

---

## 3. 🚀 Despliegue y Conexión

Ejecuta los siguientes comandos **en orden** desde Git Bash o una terminal compatible:

### Paso 1 — Levantar todos los servicios

```bash
docker-compose up -d
```

> El flag `-d` ejecuta los contenedores en segundo plano (*detached mode*).

### Paso 2 — Acceder a la terminal del cliente

```bash
docker exec -it psql_client bash
```

### Paso 3 — Conectarse a la base de datos con pgcli

```bash
pgcli -h db-server -U taller_user -d taller_redes
```

Cuando se solicite, ingresar la contraseña:

```
taller_password
```

---

## 4. 📡 Captura de Tráfico de Red

> **⚠️ Abrir una nueva terminal** para este paso, sin cerrar la conexión a pgcli del paso anterior.

### Comando de captura

```bash
MSYS_NO_PATHCONV=1 docker exec -it psql_analyzer tshark -i any -f "tcp port 5432" -w /capturas/trafico_taller.pcapng
```

### ¿Qué hace este comando?

| Parte del comando | Descripción |
|---|---|
| `MSYS_NO_PATHCONV=1` | Evita que Git Bash traduzca la ruta; la pasa directamente a Docker (compatibilidad Windows) |
| `tshark` | Versión CLI de Wireshark para captura en línea de comandos |
| `-i any` | Escucha en **todas** las interfaces de red del contenedor |
| `-f "tcp port 5432"` | Filtra solo el tráfico del puerto de PostgreSQL |
| `-w /capturas/trafico_taller.pcapng` | Guarda los paquetes capturados en un archivo `.pcapng` |

La terminal quedará **en escucha activa**, mostrando un contador de paquetes capturados en tiempo real.

---

## 5. 🗄️ Consultas SQL de Prueba

Con la captura activa, volver a la terminal de `pgcli` y ejecutar las siguientes operaciones:

### Crear tabla

```sql
CREATE TABLE estudiantes (
  id     SERIAL PRIMARY KEY,
  nombre VARCHAR(50),
  correo VARCHAR(50),
  nota   INT
);
```

### Insertar registros

```sql
-- Primera inserción
INSERT INTO estudiantes (nombre, correo, nota)
VALUES ('Eduardo', 'eduardo@correo.cl', 7);

-- Segunda inserción
INSERT INTO estudiantes (nombre, correo, nota)
VALUES ('Oscar', 'Oscar@correo.cl', 6);
```

### Modificar un registro

```sql
UPDATE estudiantes SET nota = 5 WHERE nombre = 'Oscar';
```

### Consultar registros

```sql
-- Todos los registros
SELECT * FROM estudiantes;

-- Solo estudiantes con nota 7
SELECT nombre, nota FROM estudiantes WHERE nota = 7;
```

### Limpiar (opcional — para repetir el experimento)

```sql
DROP TABLE estudiantes;
```

---

## 6. 🔬 Análisis con Wireshark

Una vez terminadas las pruebas SQL, seguir estos pasos:

### 1. Detener la captura
En la terminal del analizador, presionar:
```
Ctrl + C
```
La terminal volverá a su estado normal. Puedes cerrar todas las terminales escribiendo `exit`.

### 2. Localizar el archivo de captura

Navegar a la ruta:
```
Tarea 2 Taller de Redes\capturas
```
Allí encontrarás el archivo `trafico_taller.pcapng`.

### 3. Abrir el archivo en Wireshark

- **Si tienes Wireshark instalado:** haz doble clic en el archivo `.pcapng`, se abrirá automáticamente.
- **Si no se abre solo:** abre Wireshark manualmente → `Archivo` → `Abrir` → selecciona el archivo en la ruta indicada.

### 4. Analizar el tráfico

Con el archivo abierto puedes:
- 🔍 Detectar **patrones de comunicación** entre cliente y servidor
- 📊 Revisar **estadísticas de red** (menú `Estadísticas`)
- 🚨 Identificar **anomalías o comportamientos inesperados** en el protocolo

---

## 💡 Resumen del flujo completo

```
Instalar herramientas
        ↓
Configurar docker-compose.yml
        ↓
docker-compose up -d   →   Levanta db-server, db-client, network_analyzer
        ↓
Terminal 1: Conectarse a pgcli (db-client → db-server)
Terminal 2: Iniciar captura con tshark (network_analyzer)
        ↓
Ejecutar consultas SQL en Terminal 1
        ↓
Detener captura con Ctrl+C en Terminal 2
        ↓
Abrir .pcapng en Wireshark y analizar
```

---

> **Tecnologías usadas:** Docker · PostgreSQL · pgcli · tshark/Wireshark · WSL · Git Bash
