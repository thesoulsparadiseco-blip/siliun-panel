"""Genera un certificado TLS autofirmado para correr el servidor por HTTPS
en la red local, sin depender de ningun servicio externo (Render, ngrok,
etc). Necesario porque los navegadores de celular solo dan permiso de
camara/microfono en un sitio servido por HTTPS (o en localhost).

Uso:
    python3 generate_cert.py            # detecta la IP local automaticamente
    python3 generate_cert.py 192.168.1.5  # o la indicas a mano

Genera cert.pem y key.pem en esta misma carpeta, validos por 5 anios.
No se conecta a internet en ningun momento (la deteccion de IP usa un
truco de socket UDP que no llega a enviar ningun paquete).
"""

import ipaddress
import socket
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

BASE_DIR = Path(__file__).parent
CERT_PATH = BASE_DIR / "cert.pem"
KEY_PATH = BASE_DIR / "key.pem"


def detect_local_ip() -> str:
    """Devuelve la IP de la red local sin salir a internet: un socket UDP
    'conectado' a una IP publica solo hace que el SO elija la interfaz de
    salida, no llega a mandar ningun paquete."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def build_san(host: str):
    entries = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    try:
        entries.append(x509.IPAddress(ipaddress.ip_address(host)))
    except ValueError:
        entries.append(x509.DNSName(host))
    return x509.SubjectAlternativeName(entries)


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else detect_local_ip()

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, host),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Sistema de Llamadas (local)"),
    ])

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=5 * 365))
        .add_extension(build_san(host), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    KEY_PATH.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    CERT_PATH.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Certificado generado para: {host} (y localhost / 127.0.0.1)")
    print(f"  {CERT_PATH}")
    print(f"  {KEY_PATH}")
    print()
    print("Arrancá el servidor con:")
    print(
        f"  uvicorn server:app --host 0.0.0.0 --port 8443 "
        f"--ssl-keyfile key.pem --ssl-certfile cert.pem"
    )
    print()
    print(f"Y desde el celular (misma wifi) entrá a: https://{host}:8443")


if __name__ == "__main__":
    main()
