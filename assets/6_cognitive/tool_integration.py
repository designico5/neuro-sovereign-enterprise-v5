#!/usr/bin/env python3
#===============================================================================
# TOOL INTEGRATION SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Integrate various tools for agent use
#===============================================================================

import os
import json
import subprocess
import requests
import sqlite3
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
import hashlib

class Tool(ABC):
    """Base Tool class"""
    
    def __init__(self, tool_id: str, config: Dict):
        self.tool_id = tool_id
        self.config = config
        self.enabled = config.get("enabled", True)
        self.privacy_level = config.get("privacy", "medium")
        self.execution_type = config.get("execution", "local")
        
    @abstractmethod
    async def execute(self, parameters: Dict) -> Dict:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate tool parameters"""
        pass
    
    def get_tool_info(self) -> Dict:
        """Get tool information"""
        return {
            "tool_id": self.tool_id,
            "enabled": self.enabled,
            "privacy_level": self.privacy_level,
            "execution_type": self.execution_type,
            "description": self.config.get("description", ""),
            "parameters": self.config.get("parameters", {})
        }

class WebSearchTool(Tool):
    """Web search tool using DuckDuckGo"""
    
    def __init__(self, tool_id: str, config: Dict):
        super().__init__(tool_id, config)
        self.api = config.get("api", "duckduckgo")
        
    async def execute(self, parameters: Dict) -> Dict:
        """Execute web search"""
        query = parameters.get("query", "")
        if not query:
            return {"success": False, "error": "Query parameter required"}
        
        try:
            # Use DuckDuckGo instant answer API
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "query": query,
                    "abstract": data.get("Abstract", ""),
                    "answer": data.get("Answer", ""),
                    "results": data.get("RelatedTopics", [])[:5],
                    "provider": "duckduckgo"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate parameters"""
        return "query" in parameters and isinstance(parameters["query"], str)

class CodeExecutionTool(Tool):
    """Code execution tool in sandboxed environment"""
    
    def __init__(self, tool_id: str, config: Dict):
        super().__init__(tool_id, config)
        self.allowed_languages = config.get("languages", ["python", "javascript", "bash"])
        self.sandboxed = config.get("execution", "sandboxed") == "sandboxed"
        
    async def execute(self, parameters: Dict) -> Dict:
        """Execute code in sandboxed environment"""
        code = parameters.get("code", "")
        language = parameters.get("language", "python")
        
        if not code:
            return {"success": False, "error": "Code parameter required"}
        
        if language not in self.allowed_languages:
            return {"success": False, "error": f"Language {language} not allowed"}
        
        try:
            if language == "python":
                result = self._execute_python(code)
            elif language == "javascript":
                result = self._execute_javascript(code)
            elif language == "bash":
                result = self._execute_bash(code)
            else:
                return {"success": False, "error": "Unsupported language"}
            
            return {
                "success": True,
                "language": language,
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "execution_time": result.get("execution_time", 0)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_python(self, code: str) -> Dict:
        """Execute Python code"""
        # This would use a proper sandbox like RestrictedPython
        # For demonstration, we'll use exec with restrictions
        start_time = datetime.now()
        
        try:
            # Create restricted environment
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "set": set,
                }
            }
            
            # Capture output
            output = []
            def capture_print(*args, **kwargs):
                output.append(" ".join(str(arg) for arg in args))
            
            safe_globals["print"] = capture_print
            
            # Execute code
            exec(code, safe_globals)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "output": "\n".join(output),
                "error": "",
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {
                "output": "",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _execute_javascript(self, code: str) -> Dict:
        """Execute JavaScript code"""
        # This would use Node.js or similar
        return {"output": "JavaScript execution not implemented", "error": "", "execution_time": 0}
    
    def _execute_bash(self, code: str) -> Dict:
        """Execute bash commands with restrictions"""
        # This would use a proper sandbox like Firejail
        # For safety, we'll only allow very basic commands
        dangerous_commands = ["rm", "dd", "mkfs", "format", "del", "erase"]
        
        for cmd in dangerous_commands:
            if cmd in code.lower():
                return {"output": "", "error": "Dangerous command blocked", "execution_time": 0}
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "output": result.stdout,
                "error": result.stderr,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {"output": "", "error": "Command timeout", "execution_time": 10}
        except Exception as e:
            return {"output": "", "error": str(e), "execution_time": 0}
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate parameters"""
        return "code" in parameters and "language" in parameters

class FileOperationsTool(Tool):
    """File operations tool with security restrictions"""
    
    def __init__(self, tool_id: str, config: Dict):
        super().__init__(tool_id, config)
        self.permissions = config.get("permissions", ["read", "write", "list"])
        self.allowed_directories = config.get("allowed_directories", ["./", "./temp/"])
        
    async def execute(self, parameters: Dict) -> Dict:
        """Execute file operations"""
        operation = parameters.get("operation", "")
        path = parameters.get("path", "")
        
        if not operation or not path:
            return {"success": False, "error": "Operation and path parameters required"}
        
        # Check if operation is allowed
        if operation not in self.permissions:
            return {"success": False, "error": f"Operation {operation} not allowed"}
        
        # Check if path is in allowed directories
        if not self._is_path_allowed(path):
            return {"success": False, "error": "Path not in allowed directories"}
        
        try:
            if operation == "read":
                result = self._read_file(path)
            elif operation == "write":
                content = parameters.get("content", "")
                result = self._write_file(path, content)
            elif operation == "list":
                result = self._list_directory(path)
            elif operation == "delete":
                result = self._delete_file(path)
            else:
                return {"success": False, "error": "Unsupported operation"}
            
            return {"success": True, "operation": operation, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is in allowed directories"""
        # Basic path validation
        path = os.path.abspath(path)
        for allowed_dir in self.allowed_directories:
            allowed_path = os.path.abspath(allowed_dir)
            if path.startswith(allowed_path):
                return True
        return False
    
    def _read_file(self, path: str) -> Dict:
        """Read file contents"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
            return {"content": content, "size": len(content)}
        else:
            return {"error": "File not found"}
    
    def _write_file(self, path: str, content: str) -> Dict:
        """Write content to file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(content)
        
        return {"path": path, "size": len(content)}
    
    def _list_directory(self, path: str) -> Dict:
        """List directory contents"""
        if os.path.isdir(path):
            files = os.listdir(path)
            return {"files": files, "count": len(files)}
        else:
            return {"error": "Not a directory"}
    
    def _delete_file(self, path: str) -> Dict:
        """Delete file"""
        if os.path.exists(path):
            os.remove(path)
            return {"path": path, "deleted": True}
        else:
            return {"error": "File not found"}
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate parameters"""
        return "operation" in parameters and "path" in parameters

class DatabaseQueryTool(Tool):
    """Database query tool"""
    
    def __init__(self, tool_id: str, config: Dict):
        super().__init__(tool_id, config)
        self.supported_databases = config.get("supported_databases", ["sqlite"])
        
    async def execute(self, parameters: Dict) -> Dict:
        """Execute database query"""
        query = parameters.get("query", "")
        database = parameters.get("database", "")
        
        if not query or not database:
            return {"success": False, "error": "Query and database parameters required"}
        
        # Check if database type is supported
        db_type = database.split(":")[0] if ":" in database else "sqlite"
        if db_type not in self.supported_databases:
            return {"success": False, "error": f"Database type {db_type} not supported"}
        
        try:
            if db_type == "sqlite":
                result = self._execute_sqlite(query, database)
            else:
                return {"success": False, "error": "Database type not implemented"}
            
            return {"success": True, "query": query, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_sqlite(self, query: str, database: str) -> Dict:
        """Execute SQLite query"""
        # Extract database path
        db_path = database.split(":")[1] if ":" in database else database
        
        if not os.path.exists(db_path):
            return {"error": "Database file not found"}
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                return {"error": f"Dangerous operation {keyword} not allowed"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            result = {
                "columns": columns,
                "rows": [dict(zip(columns, row)) for row in rows],
                "count": len(rows)
            }
        else:
            conn.commit()
            result = {"affected_rows": cursor.rowcount}
        
        conn.close()
        return result
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate parameters"""
        return "query" in parameters and "database" in parameters

class ToolIntegrationSystem:
    """Tool Integration System for agent use"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.tools: Dict[str, Tool] = {}
        self.load_tools()
        
    def load_config(self, config_path: str) -> Dict:
        """Load tool integration configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "tool_integration": {
                "tools": {}
            }
        }
    
    def load_tools(self):
        """Load tools from configuration"""
        tools_config = self.config.get("tool_integration", {}).get("tools", {})
        
        tool_classes = {
            "web_search": WebSearchTool,
            "code_execution": CodeExecutionTool,
            "file_operations": FileOperationsTool,
            "database_query": DatabaseQueryTool
        }
        
        for tool_id, tool_config in tools_config.items():
            if tool_config.get("enabled", True):
                tool_type = tool_config.get("type", "unknown")
                
                if tool_type in tool_classes:
                    tool = tool_classes[tool_type](tool_id, tool_config)
                    self.tools[tool_id] = tool
                    print(f"Loaded tool: {tool_id}")
    
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.tool_id] = tool
        print(f"Registered tool: {tool.tool_id}")
    
    async def execute_tool(self, tool_id: str, parameters: Dict) -> Dict:
        """Execute a tool with given parameters"""
        if tool_id not in self.tools:
            return {"success": False, "error": f"Tool {tool_id} not found"}
        
        tool = self.tools[tool_id]
        
        if not tool.enabled:
            return {"success": False, "error": f"Tool {tool_id} is disabled"}
        
        # Validate parameters
        if not tool.validate_parameters(parameters):
            return {"success": False, "error": "Invalid parameters"}
        
        # Execute tool
        return await tool.execute(parameters)
    
    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools"""
        return [tool.get_tool_info() for tool in self.tools.values()]
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict]:
        """Get information about a specific tool"""
        if tool_id in self.tools:
            return self.tools[tool_id].get_tool_info()
        return None
    
    def select_tool_for_task(self, task_description: str, task_capabilities: List[str]) -> Optional[str]:
        """Select appropriate tool for a task"""
        # Simple keyword matching for tool selection
        tool_keywords = {
            "web_search": ["search", "find", "lookup", "web", "internet"],
            "code_execution": ["code", "execute", "run", "program", "script"],
            "file_operations": ["file", "read", "write", "save", "load"],
            "database_query": ["database", "query", "sql", "data"]
        }
        
        for tool_id, keywords in tool_keywords.items():
            if tool_id in self.tools:
                for keyword in keywords:
                    if keyword in task_description.lower():
                        return tool_id
        
        return None

async def main():
    """Main entry point for testing"""
    tool_system = ToolIntegrationSystem()
    
    print("Tool Integration System Status:")
    tools = tool_system.get_available_tools()
    print(json.dumps(tools, indent=2))
    
    # Test web search
    print("\nTesting web search tool...")
    result = await tool_system.execute_tool("web_search", {
        "query": "artificial intelligence"
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test code execution
    print("\nTesting code execution tool...")
    result = await tool_system.execute_tool("code_execution", {
        "code": "print('Hello from Python!')",
        "language": "python"
    })
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())