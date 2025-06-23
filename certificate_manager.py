"""
Certificate Manager for VoIP Quality Monitor
Handles TLS certificate generation, management and download for SIP clients
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import ipaddress
import socket

class CertificateManager:
    def __init__(self, cert_dir="certificates"):
        self.cert_dir = cert_dir
        self.ensure_cert_directory()
        
    def ensure_cert_directory(self):
        """Ensure certificate directory exists"""
        if not os.path.exists(self.cert_dir):
            os.makedirs(self.cert_dir)
            
    def generate_ca_certificate(self, common_name="VoIP Monitor CA", 
                               organization="VoIP Monitor", 
                               validity_days=3650):
        """Generate Certificate Authority (CA) certificate"""
        
        # Generate private key for CA
        ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "VoIP Security"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            ca_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=False,
                key_encipherment=False,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).sign(ca_private_key, hashes.SHA256())
        
        # Save CA certificate and key
        ca_cert_path = os.path.join(self.cert_dir, "ca-cert.pem")
        ca_key_path = os.path.join(self.cert_dir, "ca-private-key.pem")
        
        with open(ca_cert_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
        with open(ca_key_path, "wb") as f:
            f.write(ca_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        return ca_cert_path, ca_key_path, ca_cert, ca_private_key
    
    def generate_server_certificate(self, server_name="sip-server.local",
                                   server_ip=None, 
                                   validity_days=365,
                                   ca_cert=None, 
                                   ca_private_key=None):
        """Generate server certificate signed by CA"""
        
        # If no CA provided, load existing or create new
        if ca_cert is None or ca_private_key is None:
            ca_cert_path = os.path.join(self.cert_dir, "ca-cert.pem")
            ca_key_path = os.path.join(self.cert_dir, "ca-private-key.pem")
            
            if os.path.exists(ca_cert_path) and os.path.exists(ca_key_path):
                # Load existing CA
                with open(ca_cert_path, "rb") as f:
                    ca_cert = x509.load_pem_x509_certificate(f.read())
                    
                with open(ca_key_path, "rb") as f:
                    ca_private_key = serialization.load_pem_private_key(
                        f.read(), password=None
                    )
            else:
                # Generate new CA
                _, _, ca_cert, ca_private_key = self.generate_ca_certificate()
        
        # Generate server private key
        server_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Get server IP if not provided
        if server_ip is None:
            try:
                server_ip = self.get_local_ip()
            except:
                server_ip = "127.0.0.1"
        
        # Create server certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, server_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VoIP Monitor"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "SIP Server"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        ])
        
        # Subject Alternative Names for SIP clients compatibility
        san_list = [
            x509.DNSName(server_name),
            x509.DNSName("localhost"),
            x509.DNSName(socket.gethostname()),
        ]
        
        # Add IP addresses
        try:
            san_list.append(x509.IPAddress(ipaddress.ip_address(server_ip)))
            san_list.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
        except:
            pass
        
        server_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            server_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=False,
                crl_sign=False,
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        ).sign(ca_private_key, hashes.SHA256())
        
        # Save server certificate and key
        server_cert_path = os.path.join(self.cert_dir, f"{server_name}-cert.pem")
        server_key_path = os.path.join(self.cert_dir, f"{server_name}-private-key.pem")
        server_bundle_path = os.path.join(self.cert_dir, f"{server_name}-bundle.pem")
        
        with open(server_cert_path, "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))
            
        with open(server_key_path, "wb") as f:
            f.write(server_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # Create bundle file (cert + CA for client installation)
        with open(server_bundle_path, "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
        return server_cert_path, server_key_path, server_bundle_path
    
    def generate_client_certificate(self, client_name="sip-client",
                                   extension="201",
                                   validity_days=365,
                                   ca_cert=None,
                                   ca_private_key=None):
        """Generate client certificate for SIP phone/softphone"""
        
        # Load CA if not provided
        if ca_cert is None or ca_private_key is None:
            ca_cert_path = os.path.join(self.cert_dir, "ca-cert.pem")
            ca_key_path = os.path.join(self.cert_dir, "ca-private-key.pem")
            
            with open(ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read())
                
            with open(ca_key_path, "rb") as f:
                ca_private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )
        
        # Generate client private key
        client_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create client certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"{client_name}-{extension}"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VoIP Monitor"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, f"Extension {extension}"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        ])
        
        client_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            client_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=False,
                crl_sign=False,
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=True,
        ).sign(ca_private_key, hashes.SHA256())
        
        # Save client certificate and key
        client_cert_path = os.path.join(self.cert_dir, f"{client_name}-{extension}-cert.pem")
        client_key_path = os.path.join(self.cert_dir, f"{client_name}-{extension}-private-key.pem")
        client_p12_path = os.path.join(self.cert_dir, f"{client_name}-{extension}.p12")
        
        with open(client_cert_path, "wb") as f:
            f.write(client_cert.public_bytes(serialization.Encoding.PEM))
            
        with open(client_key_path, "wb") as f:
            f.write(client_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Create PKCS12 for easy client installation
        try:
            from cryptography.hazmat.primitives import serialization
            p12 = serialization.pkcs12.serialize_key_and_certificates(
                name=f"{client_name}-{extension}".encode(),
                key=client_private_key,
                cert=client_cert,
                cas=[ca_cert],
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(client_p12_path, "wb") as f:
                f.write(p12)
        except:
            client_p12_path = None
            
        return client_cert_path, client_key_path, client_p12_path
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def get_certificate_info(self, cert_path):
        """Get certificate information"""
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
                
            return {
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "not_valid_before": cert.not_valid_before,
                "not_valid_after": cert.not_valid_after,
                "serial_number": str(cert.serial_number),
                "is_expired": cert.not_valid_after < datetime.datetime.utcnow(),
                "days_until_expiry": (cert.not_valid_after - datetime.datetime.utcnow()).days
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_certificates(self):
        """List all certificates in certificate directory"""
        certificates = []
        
        if not os.path.exists(self.cert_dir):
            return certificates
            
        for filename in os.listdir(self.cert_dir):
            if filename.endswith('.pem') and 'cert' in filename:
                cert_path = os.path.join(self.cert_dir, filename)
                cert_info = self.get_certificate_info(cert_path)
                cert_info['filename'] = filename
                cert_info['path'] = cert_path
                certificates.append(cert_info)
                
        return certificates
    
    def delete_certificate_files(self, base_name):
        """Delete all files related to a certificate"""
        patterns = [
            f"{base_name}-cert.pem",
            f"{base_name}-private-key.pem", 
            f"{base_name}-bundle.pem",
            f"{base_name}.p12"
        ]
        
        deleted = []
        for pattern in patterns:
            file_path = os.path.join(self.cert_dir, pattern)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted.append(pattern)
                
        return deleted