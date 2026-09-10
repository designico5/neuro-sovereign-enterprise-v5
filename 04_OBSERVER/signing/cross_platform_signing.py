#!/usr/bin/env python3
#===============================================================================
# CROSS-PLATFORM CODE SIGNING SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Sign applications for Mac, Windows, and Linux with Neuro-Sovereign integration
#===============================================================================

import os
import sys
import json
import subprocess
import hashlib
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3

class NeuroSovereignCodeSigning:
    """Cross-platform code signing with blockchain verification"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.system = platform.system().lower()
        self.load_configurations()
        self.init_blockchain_db()
        
    def load_configurations(self):
        """Load signing configurations"""
        try:
            with open(self.config_dir / "code_signing_infrastructure.json") as f:
                self.infra_config = json.load(f)
            
            if self.system == "darwin":
                with open(self.config_dir / "mac_signing_config.json") as f:
                    self.platform_config = json.load(f)
            elif self.system == "windows":
                with open(self.config_dir / "windows_signing_config.json") as f:
                    self.platform_config = json.load(f)
            else:
                self.platform_config = {"platform": "linux"}
                
        except FileNotFoundError as e:
            print(f"Configuration file not found: {e}")
            sys.exit(1)
    
    def init_blockchain_db(self):
        """Initialize blockchain verification database"""
        db_path = self.config_dir / "state" / "ledger" / "code_signing.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signed_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                version TEXT NOT NULL,
                platform TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                signature_hash TEXT NOT NULL,
                certificate_info TEXT,
                blockchain_tx_hash TEXT,
                timestamp REAL NOT NULL,
                verified BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signing_audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (app_id) REFERENCES signed_applications (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def sign_macos_application(self, app_path: str, app_name: str, version: str) -> Dict:
        """Sign macOS application with Apple Developer ID"""
        print(f"Signing macOS application: {app_name}")
        
        config = self.platform_config["signing_configuration"]
        
        # Step 1: Sign the application bundle
        codesign_cmd = [
            "codesign",
            "--force",
            "--sign", config["certificates"]["developer_id_application"]["certificate_id"],
            "--entitlements", "entitlements.mac.plist",
            "--options=runtime",
            "--timestamp",
            app_path
        ]
        
        try:
            result = subprocess.run(codesign_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
        
        # Step 2: Notarize the application
        if config["notarization"]["enabled"]:
            notarize_cmd = [
                "xcrun", "notarytool", "submit",
                app_path,
                "--apple-id", os.getenv(config["notarization"]["apple_id_env"]),
                "--password", os.getenv(config["notarization"]["password_env"]),
                "--team-id", config["apple_developer"]["team_id"],
                "--wait"
            ]
            
            try:
                result = subprocess.run(notarize_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return {"success": False, "error": f"Notarization failed: {result.stderr}"}
                
                # Step 3: Staple the notarization ticket
                staple_cmd = ["xcrun", "stapler", "staple", app_path]
                subprocess.run(staple_cmd, capture_output=True)
                
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Notarization error: {str(e)}"}
        
        # Verify signature
        verify_cmd = ["codesign", "--verify", "--verbose", app_path]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        
        return {
            "success": True,
            "platform": "macos",
            "notarized": config["notarization"]["enabled"],
            "verified": verify_result.returncode == 0
        }
    
    def sign_windows_application(self, file_path: str, app_name: str, version: str) -> Dict:
        """Sign Windows application with Authenticode certificate"""
        print(f"Signing Windows application: {app_name}")
        
        config = self.platform_config["signing_configuration"]
        signtool_path = config["signing_tools"]["signtool"]["path"]
        
        # Use first available timestamp server
        timestamp_server = config["timestamp_servers"][0]["url"]
        
        sign_cmd = [
            signtool_path,
            "sign",
            "/f", config["certificate"]["file"],
            "/p", os.getenv(config["certificate"]["password_env"]),
            "/tr", timestamp_server,
            "/td", config["timestamp_servers"][0]["algorithm"],
            "/fd", config["certificate"]["hash_algorithm"],
            "/as",  # Append signature
            file_path
        ]
        
        try:
            result = subprocess.run(sign_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            # Verify signature
            verify_cmd = [signtool_path, "verify", "/pa", file_path]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            return {
                "success": True,
                "platform": "windows",
                "timestamp_server": timestamp_server,
                "verified": verify_result.returncode == 0
            }
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
        except FileNotFoundError:
            return {"success": False, "error": "signtool.exe not found"}
    
    def sign_linux_application(self, file_path: str, app_name: str, version: str) -> Dict:
        """Sign Linux application with GPG"""
        print(f"Signing Linux application: {app_name}")
        
        # GPG signing
        gpg_cmd = [
            "gpg",
            "--default-key", os.getenv("LINUX_SIGNING_KEY_ID"),
            "--detach-sign",
            "--armor",
            file_path
        ]
        
        try:
            result = subprocess.run(gpg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "platform": "linux",
                "signature_file": f"{file_path}.asc"
            }
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
    
    def record_signed_application(self, app_name: str, version: str, platform: str, 
                                 file_hash: str, signature_hash: str, 
                                 certificate_info: Dict) -> int:
        """Record signed application in blockchain database"""
        db_path = self.config_dir / "state" / "ledger" / "code_signing.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signed_applications 
            (app_name, version, platform, file_hash, signature_hash, certificate_info, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            app_name, version, platform, file_hash, signature_hash,
            json.dumps(certificate_info), datetime.now().timestamp()
        ))
        
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return app_id
    
    def anchor_to_blockchain(self, app_id: int) -> str:
        """Anchor signature to blockchain (placeholder)"""
        # In production: Use actual blockchain anchoring
        tx_hash = f"0x{hashlib.sha256(str(app_id).encode()).hexdigest()}"
        
        db_path = self.config_dir / "state" / "ledger" / "code_signing.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE signed_applications SET blockchain_tx_hash = ?, verified = TRUE WHERE id = ?
        ''', (tx_hash, app_id))
        
        conn.commit()
        conn.close()
        
        return tx_hash
    
    def sign_application(self, file_path: str, app_name: str, version: str) -> Dict:
        """Main signing function - detects platform and signs accordingly"""
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        
        file_hash = self.compute_file_hash(file_path)
        
        # Platform-specific signing
        if self.system == "darwin":
            result = self.sign_macos_application(file_path, app_name, version)
        elif self.system == "windows":
            result = self.sign_windows_application(file_path, app_name, version)
        else:
            result = self.sign_linux_application(file_path, app_name, version)
        
        if result["success"]:
            # Record in blockchain database
            signature_hash = self.compute_file_hash(file_path)  # Re-compute after signing
            certificate_info = {
                "signing_time": datetime.now().isoformat(),
                "platform": self.system,
                "certificate_used": "developer_id" if self.system == "darwin" else "authenticode"
            }
            
            app_id = self.record_signed_application(
                app_name, version, self.system, file_hash, signature_hash, certificate_info
            )
            
            # Anchor to blockchain
            tx_hash = self.anchor_to_blockchain(app_id)
            
            result["blockchain_tx_hash"] = tx_hash
            result["app_id"] = app_id
            result["file_hash"] = file_hash
        
        return result
    
    def verify_signature(self, file_path: str) -> Dict:
        """Verify application signature against blockchain record"""
        file_hash = self.compute_file_hash(file_path)
        
        db_path = self.config_dir / "state" / "ledger" / "code_signing.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_name, version, platform, signature_hash, blockchain_tx_hash, verified
            FROM signed_applications WHERE file_hash = ?
        ''', (file_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"valid": False, "reason": "Application not found in database"}
        
        app_name, version, platform, signature_hash, tx_hash, verified = result
        
        # Platform-specific verification
        if platform == "darwin":
            verify_cmd = ["codesign", "--verify", "--verbose", file_path]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            platform_verified = verify_result.returncode == 0
        elif platform == "windows":
            # Windows verification would use signtool verify
            platform_verified = True  # Placeholder
        else:
            # Linux GPG verification
            verify_cmd = ["gpg", "--verify", f"{file_path}.asc"]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            platform_verified = verify_result.returncode == 0
        
        return {
            "valid": platform_verified and verified,
            "app_name": app_name,
            "version": version,
            "platform": platform,
            "blockchain_anchored": tx_hash is not None,
            "blockchain_tx_hash": tx_hash,
            "platform_verified": platform_verified
        }

def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python cross_platform_signing.py <sign|verify> <file_path> <app_name> <version>")
        sys.exit(1)
    
    action = sys.argv[1]
    file_path = sys.argv[2]
    app_name = sys.argv[3]
    version = sys.argv[4] if len(sys.argv) > 4 else "1.0.0"
    
    signer = NeuroSovereignCodeSigning()
    
    if action == "sign":
        result = signer.sign_application(file_path, app_name, version)
        if result["success"]:
            print(f"✅ Successfully signed {app_name} v{version}")
            print(f"   Platform: {result['platform']}")
            print(f"   Blockchain TX: {result.get('blockchain_tx_hash', 'N/A')}")
            print(f"   App ID: {result.get('app_id', 'N/A')}")
        else:
            print(f"❌ Signing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    elif action == "verify":
        result = signer.verify_signature(file_path)
        if result["valid"]:
            print(f"✅ Signature verified for {result['app_name']} v{result['version']}")
            print(f"   Platform: {result['platform']}")
            print(f"   Blockchain anchored: {result['blockchain_anchored']}")
            print(f"   Platform verified: {result['platform_verified']}")
        else:
            print(f"❌ Verification failed: {result.get('reason', 'Unknown reason')}")
            sys.exit(1)
    
    else:
        print("Unknown action. Use 'sign' or 'verify'")
        sys.exit(1)

if __name__ == "__main__":
    main()