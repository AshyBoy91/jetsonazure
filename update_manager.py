"""
Update Manager for Azure IoT Device Application
Handles automatic updates from GitHub repository
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

import aiohttp

from config import Config


class UpdateManager:
    """Manages automatic updates for the IoT device application"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.auto_update_enabled = self.config.auto_update_enabled
        self.current_version = self._get_current_version()
        self.update_in_progress = False
        
    def set_auto_update(self, enabled: bool):
        """Enable or disable automatic updates"""
        self.auto_update_enabled = enabled
        self.logger.info(f"Auto-update {'enabled' if enabled else 'disabled'}")
    
    def _get_current_version(self) -> str:
        """Get current application version"""
        version_file = Path("version.txt")
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"Error reading version file: {e}")
        
        # Fallback to Git commit hash if available
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, cwd=Path.cwd()
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return "unknown"
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """Check for available updates from GitHub"""
        if not self.config.github_repo:
            return {"error": "GitHub repository not configured"}
        
        if self.update_in_progress:
            return {"status": "update_in_progress"}
        
        try:
            # Get latest release information from GitHub API
            latest_info = await self._get_latest_release_info()
            
            if not latest_info:
                return {"error": "Could not fetch release information"}
            
            latest_version = latest_info.get('tag_name', '')
            
            if latest_version and latest_version != self.current_version:
                self.logger.info(f"Update available: {self.current_version} -> {latest_version}")
                
                update_info = {
                    "update_available": True,
                    "current_version": self.current_version,
                    "latest_version": latest_version,
                    "release_notes": latest_info.get('body', ''),
                    "published_at": latest_info.get('published_at', ''),
                    "download_url": latest_info.get('zipball_url', '')
                }
                
                # Auto-update if enabled
                if self.auto_update_enabled:
                    update_result = await self._perform_update(latest_info)
                    update_info.update(update_result)
                
                return update_info
            else:
                return {
                    "update_available": False,
                    "current_version": self.current_version,
                    "message": "Application is up to date"
                }
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return {"error": f"Update check failed: {str(e)}"}
    
    async def _get_latest_release_info(self) -> Optional[Dict]:
        """Get latest release information from GitHub API"""
        if not self.config.github_repo:
            return None
        
        api_url = f"https://api.github.com/repos/{self.config.github_repo}/releases/latest"
        headers = {}
        
        if self.config.github_token:
            headers['Authorization'] = f'token {self.config.github_token}'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"GitHub API request failed: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching release info: {e}")
            return None
    
    async def _perform_update(self, release_info: Dict) -> Dict[str, Any]:
        """Perform the actual update process"""
        self.update_in_progress = True
        
        try:
            self.logger.info("Starting update process...")
            
            # Download the update
            download_url = release_info.get('zipball_url')
            if not download_url:
                return {"error": "No download URL found"}
            
            # Create temporary directory for update
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "update.zip"
                extract_path = Path(temp_dir) / "extracted"
                
                # Download update package
                await self._download_file(download_url, zip_path)
                
                # Extract and validate
                await self._extract_and_validate(zip_path, extract_path)
                
                # Create backup
                backup_path = await self._create_backup()
                
                try:
                    # Apply update
                    await self._apply_update(extract_path)
                    
                    # Update version
                    self._update_version_file(release_info.get('tag_name', 'unknown'))
                    
                    self.logger.info("Update completed successfully")
                    
                    return {
                        "status": "success",
                        "message": "Update completed successfully",
                        "new_version": release_info.get('tag_name', 'unknown'),
                        "restart_required": True
                    }
                    
                except Exception as e:
                    # Restore backup on failure
                    self.logger.error(f"Update failed, restoring backup: {e}")
                    await self._restore_backup(backup_path)
                    raise
                
        except Exception as e:
            self.logger.error(f"Update process failed: {e}")
            return {"error": f"Update failed: {str(e)}"}
        
        finally:
            self.update_in_progress = False
    
    async def _download_file(self, url: str, destination: Path):
        """Download file from URL"""
        headers = {}
        if self.config.github_token:
            headers['Authorization'] = f'token {self.config.github_token}'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    with open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                else:
                    raise Exception(f"Download failed: HTTP {response.status}")
    
    async def _extract_and_validate(self, zip_path: Path, extract_path: Path):
        """Extract and validate update package"""
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Find the actual content directory (GitHub creates a nested directory)
        contents = list(extract_path.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            # Move contents up one level
            inner_dir = contents[0]
            temp_move = extract_path / "temp_move"
            inner_dir.rename(temp_move)
            
            for item in temp_move.iterdir():
                item.rename(extract_path / item.name)
            
            temp_move.rmdir()
        
        # Validate required files exist
        required_files = ['main.py', 'config.py', 'requirements.txt']
        for required_file in required_files:
            if not (extract_path / required_file).exists():
                raise Exception(f"Required file missing: {required_file}")
    
    async def _create_backup(self) -> Path:
        """Create backup of current application"""
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}"
        
        # Copy current application files
        current_dir = Path.cwd()
        shutil.copytree(current_dir, backup_path, 
                       ignore=shutil.ignore_patterns('backups', '__pycache__', '*.log', '.git'))
        
        self.logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    async def _apply_update(self, source_path: Path):
        """Apply the update by copying new files"""
        current_dir = Path.cwd()
        
        # Files to update (excluding certain directories/files)
        exclude_patterns = {'.git', '__pycache__', 'backups', '*.log', '.env'}
        
        for item in source_path.iterdir():
            if item.name in exclude_patterns:
                continue
            
            destination = current_dir / item.name
            
            if item.is_file():
                # Copy file
                shutil.copy2(item, destination)
            elif item.is_dir():
                # Copy directory
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(item, destination)
        
        self.logger.info("Files updated successfully")
    
    async def _restore_backup(self, backup_path: Path):
        """Restore from backup"""
        if not backup_path.exists():
            return
        
        current_dir = Path.cwd()
        
        # Restore files from backup
        for item in backup_path.iterdir():
            destination = current_dir / item.name
            
            if destination.exists():
                if destination.is_file():
                    destination.unlink()
                else:
                    shutil.rmtree(destination)
            
            if item.is_file():
                shutil.copy2(item, destination)
            elif item.is_dir():
                shutil.copytree(item, destination)
        
        self.logger.info("Backup restored successfully")
    
    def _update_version_file(self, version: str):
        """Update the version file"""
        version_file = Path("version.txt")
        with open(version_file, 'w') as f:
            f.write(version)
        
        self.current_version = version
    
    async def handle_firmware_update(self, payload: Dict) -> Dict[str, Any]:
        """Handle firmware update request from Azure IoT Hub"""
        try:
            if not payload:
                return {"error": "No payload provided"}
            
            # Extract update parameters
            update_url = payload.get('update_url')
            expected_version = payload.get('version')
            force_update = payload.get('force', False)
            
            if not update_url:
                return {"error": "No update URL provided"}
            
            # Check if update is needed
            if not force_update and expected_version == self.current_version:
                return {
                    "status": "skipped",
                    "message": "Already at requested version",
                    "current_version": self.current_version
                }
            
            # Perform manual update
            self.logger.info(f"Manual update requested: {update_url}")
            
            # This would require custom logic for manual updates
            # For now, return a placeholder response
            return {
                "status": "initiated",
                "message": "Manual update process started",
                "current_version": self.current_version,
                "target_version": expected_version
            }
            
        except Exception as e:
            self.logger.error(f"Error handling firmware update: {e}")
            return {"error": f"Firmware update failed: {str(e)}"}
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status"""
        return {
            "current_version": self.current_version,
            "auto_update_enabled": self.auto_update_enabled,
            "update_in_progress": self.update_in_progress,
            "github_repo": self.config.github_repo,
            "last_check": datetime.utcnow().isoformat()
        } 