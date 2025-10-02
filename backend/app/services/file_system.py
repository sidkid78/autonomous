# file_system_service.py
import os
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileSystemService:
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)
        self.permissions: Dict[str, Dict[str, bool]] = {}
        
        # Create the base directory if it doesn't existethod that rigorously checks if the requested file path resolves to a location wi
        try:
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"Initialized FileSystemService with base path: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create base directory {self.base_path}: {e}")
            raise
    
    def grant_permission(self, agent_id: str, permissions: Dict[str, bool]):
        """Grants specified permissions to an agent."""
        if not isinstance(permissions, dict):
            raise ValueError("Permissions must be a dictionary.")
        self.permissions[agent_id] = permissions
        logger.info(f"Granted permissions to agent {agent_id}: {permissions}")
    
    def _validate_path_and_permission(self, agent_id: str, operation: str, relative_path: str) -> str:
        """
        Validates the agent's permission and ensures the path is within the base directory.

        Args:
            agent_id: The ID of the agent performing the operation.
            operation: The operation being attempted (e.g., 'read', 'write', 'delete').
            relative_path: The file or directory path relative to the base path.

        Returns:
            The validated absolute path.

        Raises:
            HTTPException: If permission is denied or the path is invalid/outside the base directory.
        """
        agent_permissions = self.permissions.get(agent_id, {})
        if not agent_permissions.get(operation, False):
            logger.warning(f"Permission denied for agent {agent_id}, operation '{operation}', path '{relative_path}'")
            raise HTTPException(status_code=403, detail=f"Agent does not have '{operation}' permission.")

        # Prevent access to the base path itself if relative_path is empty or '.'
        if not relative_path or relative_path == '.':
             logger.warning(f"Attempt by agent {agent_id} to access base path directly for operation '{operation}'.")
             raise HTTPException(status_code=403, detail="Direct access to the base directory is not permitted.")

        absolute_path = os.path.abspath(os.path.join(self.base_path, relative_path))

        # Critical Path Traversal Check: Ensure the resolved path is truly within the base path
        if not absolute_path.startswith(self.base_path + os.sep) and absolute_path != self.base_path:
             logger.error(f"Path traversal attempt detected: Agent {agent_id}, operation '{operation}', requested path '{relative_path}', resolved to '{absolute_path}', outside base '{self.base_path}'")
             raise HTTPException(status_code=403, detail="Access denied: Path is outside the allowed base directory.")

        return absolute_path

    def read_file(self, agent_id: str, file_path: str) -> str:
        """Reads the content of a file."""
        absolute_path = self._validate_path_and_permission(agent_id, 'read', file_path)

        if not os.path.isfile(absolute_path):
            logger.warning(f"Read attempt failed: Agent {agent_id}, path '{file_path}' is not a file or does not exist.")
            raise HTTPException(status_code=404, detail="File not found.")

        try:
            with open(absolute_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"Agent {agent_id} successfully read file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error reading file.")
    
    def write_file(self, agent_id: str, file_path: str, content: str):
        """Writes content to a file, creating directories if necessary."""
        absolute_path = self._validate_path_and_permission(agent_id, 'write', file_path)
        parent_dir = os.path.dirname(absolute_path)

        try:
            # Ensure parent directory exists (safe due to base path validation)
            os.makedirs(parent_dir, exist_ok=True)
            with open(absolute_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logger.info(f"Agent {agent_id} successfully wrote to file: {file_path}")
        except Exception as e:
            logger.error(f"Error writing file '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error writing file.")
    
    def list_files(self, agent_id: str, directory_path: str) -> List[str]:
        """Lists files and directories within a given directory."""
        absolute_path = self._validate_path_and_permission(agent_id, 'read', directory_path) # Listing requires read permission on the dir

        if not os.path.isdir(absolute_path):
            logger.warning(f"List files attempt failed: Agent {agent_id}, path '{directory_path}' is not a directory or does not exist.")
            raise HTTPException(status_code=404, detail="Directory not found.")

        try:
            entries = os.listdir(absolute_path)
            logger.info(f"Agent {agent_id} successfully listed directory: {directory_path}")
            return entries
        except Exception as e:
            logger.error(f"Error listing directory '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error listing directory content.")
    
    def delete_file(self, agent_id: str, file_path: str):
        """Deletes a file."""
        absolute_path = self._validate_path_and_permission(agent_id, 'delete', file_path)

        if not os.path.isfile(absolute_path):
            logger.warning(f"Delete attempt failed: Agent {agent_id}, path '{file_path}' is not a file or does not exist.")
            raise HTTPException(status_code=404, detail="File not found.")

        try:
            os.remove(absolute_path)
            logger.info(f"Agent {agent_id} successfully deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error deleting file.")
    
    def create_directory(self, agent_id: str, directory_path: str):
        """Creates a directory, including parent directories if necessary."""
        # Typically, creating a directory requires 'write' permission in the parent
        # We validate the *target* path to ensure it's within bounds.
        absolute_path = self._validate_path_and_permission(agent_id, 'write', directory_path)

        # Check if parent directory exists and is writable (optional, os.makedirs handles some cases)
        parent_dir = os.path.dirname(absolute_path)
        if not os.path.isdir(parent_dir):
             # This case should ideally be caught by _validate_path_and_permission if base_path doesn't exist
             # but could happen if an intermediate dir within base_path was deleted.
             logger.warning(f"Create directory attempt failed: Agent {agent_id}, parent directory '{parent_dir}' does not exist for path '{directory_path}'.")
             raise HTTPException(status_code=404, detail="Parent directory does not exist.")

        try:
            # exist_ok=True prevents error if directory already exists
            os.makedirs(absolute_path, exist_ok=True)
            logger.info(f"Agent {agent_id} successfully created directory (or it already existed): {directory_path}")
        except Exception as e:
            logger.error(f"Error creating directory '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error creating directory.")
    
    def move_file(self, agent_id: str, old_path: str, new_path: str):
        """Moves or renames a file or directory."""
        # Requires delete permission on the old path and write permission on the new path's *directory*
        # We validate both paths are within the base directory.
        abs_old_path = self._validate_path_and_permission(agent_id, 'delete', old_path) # Need delete perm for source
        abs_new_path = self._validate_path_and_permission(agent_id, 'write', new_path)  # Need write perm for destination

        if not os.path.exists(abs_old_path):
             logger.warning(f"Move attempt failed: Agent {agent_id}, source path '{old_path}' does not exist.")
             raise HTTPException(status_code=404, detail="Source path does not exist.")

        # Ensure parent directory of the new path exists
        new_parent_dir = os.path.dirname(abs_new_path)
        try:
            os.makedirs(new_parent_dir, exist_ok=True)
            shutil.move(abs_old_path, abs_new_path)
            logger.info(f"Agent {agent_id} successfully moved '{old_path}' to '{new_path}'")
        except Exception as e:
            logger.error(f"Error moving '{abs_old_path}' to '{abs_new_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error moving file or directory.")
    
    def copy_file(self, agent_id: str, source_path: str, destination_path: str):
        """Copies a file."""
        abs_source_path = self._validate_path_and_permission(agent_id, 'read', source_path)
        abs_destination_path = self._validate_path_and_permission(agent_id, 'write', destination_path)

        if not os.path.isfile(abs_source_path):
            logger.warning(f"Copy attempt failed: Agent {agent_id}, source path '{source_path}' is not a file or does not exist.")
            raise HTTPException(status_code=404, detail="Source file not found.")

        # Ensure parent directory of the destination path exists
        destination_parent_dir = os.path.dirname(abs_destination_path)
        try:
            os.makedirs(destination_parent_dir, exist_ok=True)
            shutil.copy2(abs_source_path, abs_destination_path) # copy2 preserves metadata
            logger.info(f"Agent {agent_id} successfully copied '{source_path}' to '{destination_path}'")
        except Exception as e:
            logger.error(f"Error copying '{abs_source_path}' to '{abs_destination_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error copying file.")
    
    def get_file_metadata(self, agent_id: str, file_path: str) -> Dict[str, Any]:
        """Gets metadata for a file or directory."""
        absolute_path = self._validate_path_and_permission(agent_id, 'read', file_path) # Requires read permission

        if not os.path.exists(absolute_path):
            logger.warning(f"Get metadata attempt failed: Agent {agent_id}, path '{file_path}' does not exist.")
            raise HTTPException(status_code=404, detail="File or directory not found.")

        try:
            stats = os.stat(absolute_path)
            is_dir = os.path.isdir(absolute_path)
            metadata = {
                'path': file_path, # Return relative path for consistency
                'absolute_path': absolute_path, # Maybe useful internally, but consider if agent should see it
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'is_directory': is_dir,
                'is_file': not is_dir,
            }
            logger.info(f"Agent {agent_id} successfully retrieved metadata for: {file_path}")
            return metadata
        except Exception as e:
            logger.error(f"Error getting metadata for '{absolute_path}' for agent {agent_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error getting file metadata.")