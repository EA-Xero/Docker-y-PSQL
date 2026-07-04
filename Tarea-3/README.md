# Laboratorio: Ataque MitM sobre tráfico PostgreSQL con Docker

## Descripción del proyecto

Este proyecto implementa un laboratorio de red controlado, usando **Docker Compose**, para demostrar de forma práctica un ataque **Man in the Middle (MitM)** sobre una conexión **PostgreSQL**.

La topología simula tres roles de red separados en distintas subredes:

- **`psql_client`**: equipo cliente que se conecta a la base de datos usando `pgcli`.
- **`psql_server`**: contenedor que aloja el servidor de PostgreSQL (`taller_redes`).
- **`psql_firewall`**: contenedor intermedio que actúa como **router/firewall** entre el cliente y el servidor, y que además ejecuta el script de interceptación con **Scapy**.

Al forzar a que el tráfico del cliente y del servidor pase obligatoriamente por `psql_firewall` (modificando las rutas por defecto), este contenedor queda en posición de interceptar, inspeccionar y modificar los paquetes TCP que viajan hacia el puerto **5432** (PostgreSQL), usando **NFQUEUE** e **iptables** para desviar el tráfico hacia el script en Python.

El objetivo académico es entender:
- Cómo funciona el enrutamiento y el reenvío de paquetes en una red.
- Cómo un atacante en una posición de "hombre en el medio" puede interceptar tráfico no cifrado.
- Cómo herramientas como Scapy y NetfilterQueue permiten capturar, reconstruir y reinyectar paquetes modificados.
- La importancia de cifrar las conexiones a bases de datos (SSL/TLS) para evitar este tipo de ataques.

> ⚠️ **Nota importante:** este laboratorio debe ejecutarse únicamente en un entorno aislado y controlado (contenedores Docker propios), con fines educativos dentro de un taller de redes. No debe aplicarse sobre redes o sistemas que no sean de tu propiedad o sin autorización explícita.

---

## Requisitos previos

- Docker y Docker Compose instalados.
- Archivo `docker-compose.yml` con la definición de los tres contenedores (`psql_client`, `psql_server`, `psql_firewall`) y sus respectivas subredes.
- Permisos de administrador (sudo) en el host para algunos comandos de `iptables`.
- Conexión a internet para instalar paquetes dentro de los contenedores.

---

## Paso a paso

### 1. Levantar el entorno
Se inicializan todos los contenedores definidos en el `docker-compose.yml`:
```bash
docker compose up -d
```

### 2. Preparar herramientas de red en el cliente
Se instala `iproute2` dentro de `psql_client` para poder manipular las tablas de rutas:
```bash
docker exec -it -u root psql_client sh -c "apt-get update && apt-get install -y iproute2"
```

### 3. Reconfigurar la ruta por defecto del cliente
Se elimina la ruta por defecto y se apunta hacia el firewall (`192.168.10.254`), forzando que todo el tráfico saliente pase por `psql_firewall`:
```bash
docker exec -it psql_client bash -c "ip route del default && ip route add default via 192.168.10.254"
```

### 4. Preparar herramientas de red en el servidor
Igual que en el paso 2, pero en `psql_server`:
```bash
docker exec -it -u root psql_server sh -c "apt-get update && apt-get install -y iproute2"
```

### 5. Reconfigurar la ruta por defecto del servidor
Se apunta la ruta por defecto del servidor hacia el firewall en su propia subred (`192.168.20.254`), de modo que las respuestas también pasen por el MitM:
```bash
docker exec -it psql_server bash -c "ip route del default && ip route add default via 192.168.20.254"
```

### 6. Preparar el sistema del firewall (Alpine)
Se actualiza el gestor de paquetes `apk` y se instala Python 3:
```bash
sudo docker exec -it -u root psql_firewall apk update
sudo docker exec -it -u root psql_firewall apk add python3 py3-pip
```

### 7. Instalar Scapy
Librería principal para la manipulación de paquetes de red:
```bash
sudo docker exec -it -u root psql_firewall pip install scapy --break-system-packages
```

---

## Inicio del ataque MitM

### 8. Crear el script de intercepción
Se crea (o edita) el script `MitM_psql.py` dentro del contenedor `psql_firewall`, encargado de capturar el tráfico PostgreSQL y modificarlo:
```bash
sudo docker exec -it psql_firewall vi MitM_psql.py
```
> El contenido del script se encuentra adjunto en el repositorio del proyecto.

### 9. Bloquear temporalmente el reenvío automático de paquetes
Se redirige el tráfico destinado al puerto **5432** hacia la cola `NFQUEUE`, dando tiempo a Scapy para recibir, reconstruir y reenviar el paquete modificado (en lugar de que el kernel lo reenvíe automáticamente):
```bash
iptables -A FORWARD -p tcp --dport 5432 -j NFQUEUE --queue-num 1
```

### 10. Instalar dependencias para NetfilterQueue
Se instalan las librerías del sistema necesarias para compilar e instalar el binding de Python `NetfilterQueue`:
```bash
sudo docker exec -it -u root psql_firewall apk add libnfnetlink-dev libnetfilter_queue-dev gcc musl-dev python3-dev
sudo docker exec -it -u root psql_firewall apk add linux-headers
sudo docker exec -it -u root psql_firewall pip install NetfilterQueue --break-system-packages
```

### 11. Ejecutar el script de intercepción
Se deja el script corriendo en una terminal, a la espera de paquetes en la cola configurada:
```bash
docker exec -it psql_firewall python3 MitM_psql.py
```

### 12. Generar tráfico de prueba
Desde otra terminal, se realiza una consulta real a la base de datos a través de `pgcli`, generando el tráfico que será interceptado:
```bash
sudo docker exec -it psql_client pgcli -h 192.168.20.10 -U taller_user -d taller_redes
```

### 13. Análisis de resultados
Se analiza el comportamiento observado:
- ¿Qué paquetes fueron interceptados por `psql_firewall`?
- ¿Qué modificación se realizó sobre ellos (datos, credenciales, respuestas del servidor, etc.)?
- ¿Cómo reaccionó el cliente o el servidor ante el paquete alterado?
- ¿Qué evidencia queda de que el ataque fue exitoso (o de por qué falló)?
- ¿Qué medidas de mitigación (por ejemplo, `sslmode=require` en PostgreSQL) hubieran evitado este ataque?

---

## Conclusiones esperadas

Al finalizar el laboratorio, se espera poder explicar:
1. Por qué el control del enrutamiento (rutas por defecto) es clave para posicionarse como intermediario en una red.
2. Cómo `iptables` + `NFQUEUE` permiten desviar tráfico específico hacia una aplicación en espacio de usuario.
3. Cómo Scapy permite reconstruir e inyectar paquetes TCP modificados.
4. Por qué los protocolos sin cifrado (como PostgreSQL sin SSL) son vulnerables a este tipo de ataques.

## Estructura sugerida del repositorio
```
.
├── docker-compose.yml
├── MitM_psql.py
└── README.md
```
