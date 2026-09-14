#!/usr/bin/env python3
#===============================================================================
# NEURO-SOVEREIGN DESKTOP APPLICATION BUILDER
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Build signed desktop applications for Mac, Windows, and Linux
#===============================================================================

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class NeuroSovereignAppBuilder:
    """Cross-platform desktop application builder with code signing"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.system = platform.system().lower()
        self.load_configurations()
        
    def load_configurations(self):
        """Load build configurations"""
        try:
            with open(self.config_dir / "electron_builder_config.yml") as f:
                self.builder_config = f.read()
            
            with open(self.config_dir / "code_signing_infrastructure.json") as f:
                self.signing_config = json.load(f)
                
        except FileNotFoundError as e:
            print(f"Configuration file not found: {e}")
            sys.exit(1)
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required build tools are installed"""
        dependencies = {
            "node": False,
            "npm": False,
            "electron": False,
            "electron-builder": False
        }
        
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
            dependencies["node"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            dependencies["npm"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            # Check if electron is installed
            result = subprocess.run(["npm", "list", "electron"], capture_output=True, text=True)
            dependencies["electron"] = "electron" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            # Check if electron-builder is installed
            result = subprocess.run(["npm", "list", "electron-builder"], capture_output=True, text=True)
            dependencies["electron-builder"] = "electron-builder" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return dependencies
    
    def install_dependencies(self):
        """Install required build dependencies"""
        print("Installing build dependencies...")
        
        # Install Node.js if not present
        if not self.check_dependencies()["node"]:
            print("Node.js not found. Please install from https://nodejs.org/")
            return False
        
        # Initialize npm project if package.json doesn't exist
        if not (self.config_dir / "package.json").exists():
            subprocess.run(["npm", "init", "-y"], cwd=self.config_dir)
        
        # Install electron and electron-builder
        try:
            subprocess.run(["npm", "install", "electron", "--save-dev"], cwd=self.config_dir)
            subprocess.run(["npm", "install", "electron-builder", "--save-dev"], cwd=self.config_dir)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def prepare_source_code(self):
        """Prepare source code for packaging"""
        print("Preparing source code...")
        
        # Create basic Electron app structure
        src_dir = self.config_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create main.js
        main_js = src_dir / "main.js"
        if not main_js.exists():
            main_js.write_text("""
const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })
  
  win.loadFile('index.html')
}

app.whenReady().then(() => {
  createWindow()
  
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit()
    }
  })
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})
""")
        
        # Create index.html
        index_html = src_dir / "index.html"
        if not index_html.exists():
            index_html.write_text("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Neuro-Sovereign Enterprise</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0;
      padding: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      text-align: center;
    }
    h1 {
      font-size: 2.5em;
      margin-bottom: 0.5em;
    }
    .status {
      background: rgba(255,255,255,0.1);
      padding: 20px;
      border-radius: 10px;
      margin: 20px 0;
    }
    .metric {
      display: inline-block;
      margin: 10px;
      padding: 15px;
      background: rgba(255,255,255,0.2);
      border-radius: 5px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🧠 Neuro-Sovereign Enterprise</h1>
    <p>Secure, Symbiotic AI Operations Platform</p>
    
    <div class="status">
      <h2>System Status</h2>
      <div class="metric">
        <h3>Security</h3>
        <p>95/100</p>
      </div>
      <div class="metric">
        <h3>Symbiosis</h3>
        <p>95/100</p>
      </div>
      <div class="metric">
        <h3>Compliance</h3>
        <p>97/100</p>
      </div>
    </div>
    
    <p>Version 5.0-SYMBIOSIS | Production Ready</p>
  </div>
</body>
</html>
""")
        
        print("✅ Source code prepared")
    
    def build_application(self, platform: str = None) -> Dict:
        """Build application for specified platform"""
        if platform is None:
            platform = self.system
        
        print(f"Building application for {platform}...")
        
        # Prepare source code
        self.prepare_source_code()
        
        # Check dependencies
        deps = self.check_dependencies()
        if not all(deps.values()):
            print("Installing missing dependencies...")
            if not self.install_dependencies():
                return {"success": False, "error": "Failed to install dependencies"}
        
        # Build based on platform
        build_cmd = ["npx", "electron-builder"]
        
        if platform == "macos":
            build_cmd.extend(["--mac"])
        elif platform == "windows":
            build_cmd.extend(["--win"])
        elif platform == "linux":
            build_cmd.extend(["--linux"])
        else:
            build_cmd.extend(["--" + platform])
        
        try:
            result = subprocess.run(build_cmd, cwd=self.config_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Build successful for {platform}")
                return {
                    "success": True,
                    "platform": platform,
                    "output_dir": "dist"
                }
            else:
                print(f"❌ Build failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
    
    def sign_built_application(self, platform: str) -> Dict:
        """Sign the built application"""
        print(f"Signing application for {platform}...")
        
        # Import the signing script
        signing_script = self.config_dir / "cross_platform_signing.py"
        
        if not signing_script.exists():
            return {"success": False, "error": "Signing script not found"}
        
        # Find the built application
        dist_dir = self.config_dir / "dist"
        
        if platform == "macos":
            app_files = list(dist_dir.glob("*.app"))
            if not app_files:
                return {"success": False, "error": "No .app file found in dist/"}
            app_path = str(app_files[0])
        elif platform == "windows":
            exe_files = list(dist_dir.glob("*.exe"))
            if not exe_files:
                return {"success": False, "error": "No .exe file found in dist/"}
            app_path = str(exe_files[0])
        else:
            # Linux - look for AppImage or deb
            app_files = list(dist_dir.glob("*.AppImage")) or list(dist_dir.glob("*.deb"))
            if not app_files:
                return {"success": False, "error": "No Linux package found in dist/"}
            app_path = str(app_files[0])
        
        # Run signing
        sign_cmd = [
            "python", str(signing_script),
            "sign", app_path, "NeuroSovereignEnterprise", "5.0.0"
        ]
        
        try:
            result = subprocess.run(sign_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Application signed successfully")
                return {
                    "success": True,
                    "platform": platform,
                    "signed_file": app_path
                }
            else:
                print(f"❌ Signing failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
    
    def build_and_sign(self, platform: str = None) -> Dict:
        """Complete build and sign process"""
        print(f"Building and signing for {platform or 'current platform'}...")
        
        # Build application
        build_result = self.build_application(platform)
        if not build_result["success"]:
            return build_result
        
        # Sign application
        sign_result = self.sign_built_application(platform or self.system)
        if not sign_result["success"]:
            return sign_result
        
        return {
            "success": True,
            "platform": platform or self.system,
            "build_result": build_result,
            "sign_result": sign_result
        }

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python build_desktop_app.py <build|sign|build-and-sign> [platform]")
        print("Platforms: macos, windows, linux")
        sys.exit(1)
    
    action = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    
    builder = NeuroSovereignAppBuilder()
    
    if action == "build":
        result = builder.build_application(platform)
    elif action == "sign":
        result = builder.sign_built_application(platform)
    elif action == "build-and-sign":
        result = builder.build_and_sign(platform)
    else:
        print("Unknown action. Use 'build', 'sign', or 'build-and-sign'")
        sys.exit(1)
    
    if result["success"]:
        print(f"✅ {action} completed successfully for {result.get('platform', 'current platform')}")
        sys.exit(0)
    else:
        print(f"❌ {action} failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()