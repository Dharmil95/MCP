#!/usr/bin/env python3
"""
MCP Client Manager
Handles initialization and management of MCP clients (FastMCP and LangGraph).
"""

import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional

# FastMCP imports
from fastmcp import Client
from fastmcp.exceptions import McpError, ClientError

# LangGraph imports
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from .config import MCPConfig


class MCPClientManager:
    """Manages MCP clients for document and math operations."""
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.fastmcp_client = None
        self.langgraph_client = None
        self.available_tools = {}
        
    async def initialize_fastmcp(self) -> bool:
        """Initialize FastMCP client for document operations."""
        try:
            config = MCPConfig.get_fastmcp_config()
            self.fastmcp_client = Client(config)
            
            async with self.fastmcp_client:
                await self.fastmcp_client.ping()
                tools = await self.fastmcp_client.list_tools()
                
                for tool in tools:
                    self.available_tools[f"document_{tool.name}"] = {
                        "name": tool.name,
                        "description": tool.description,
                        "type": "document",
                        "schema": tool.inputSchema
                    }
                
                print(f"✓ Document Client: Connected with {len(tools)} tools")
                return True
                
        except Exception as e:
            print(f"⚠️  FastMCP initialization failed: {e}")
            return False
    
    async def initialize_langgraph(self) -> bool:
        """Initialize LangGraph client for math operations."""
        if not LANGGRAPH_AVAILABLE:
            print("⚠️  LangGraph not available")
            return False
            
        try:
            config = MCPConfig.get_langgraph_config()
            self.langgraph_client = MultiServerMCPClient(config)
            tools = await self.langgraph_client.get_tools()
            
            for tool in tools:
                self.available_tools[f"math_{tool.name}"] = {
                    "name": tool.name,
                    "description": tool.description,
                    "type": "math",
                    "tool": tool
                }
            
            print(f"✓ Math Client: Connected with {len(tools)} tools")
            return True
            
        except Exception as e:
            print(f"⚠️  LangGraph initialization failed: {e}")
            return False
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all MCP clients."""
        results = {}
        results["fastmcp"] = await self.initialize_fastmcp()
        results["langgraph"] = await self.initialize_langgraph()
        return results
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools across clients."""
        return self.available_tools.copy()
    
    async def get_fastmcp_tools(self):
        """Get FastMCP tools for agent creation."""
        if not self.fastmcp_client:
            return []
            
        from langchain_core.tools import tool
        import asyncio
        
        # Create a reference to the client for closure
        client = self.fastmcp_client
        
        @tool
        def list_documents() -> str:
            """List all available documents in the system."""
            print("🔍 DEBUG: list_documents tool invoked")
            try:
                # Run async operation in sync context
                async def _async_list():
                    async with client:
                        result = await client.call_tool("list_documents")
                        
                        if isinstance(result, dict):
                            documents = result.get("documents", [])
                        elif isinstance(result, list):
                            documents = result
                        else:
                            documents = []
                        
                        if documents:
                            # Format each document to show ID and filename
                            doc_list = []
                            for doc in documents:
                                if isinstance(doc, dict):
                                    # Format with document_id and filename if available
                                    doc_id = doc.get("document_id", "Unknown ID")
                                    filename = doc.get("filename", "Unknown filename")
                                    doc_list.append(f"- {filename} (ID: {doc_id})")
                                else:
                                    # Fallback if not a dictionary
                                    doc_list.append(f"- {doc}")
                            
                            # Join the formatted documents
                            formatted_list = "\n".join(doc_list)
                            return f"Available documents:\n{formatted_list}"
                        else:
                            return "No documents found in the system."
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to run in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, _async_list())
                            return future.result()
                    else:
                        return loop.run_until_complete(_async_list())
                except RuntimeError:
                    # No event loop, create new one
                    return asyncio.run(_async_list())
                    
            except Exception as e:
                print(f"🔍 DEBUG: list_documents error: {e}")
                return f"Error listing documents: {str(e)}"
        
        @tool
        def search_documents(query: str, limit: int = 5) -> str:
            """Search documents using semantic search."""
            print(f"🔍 DEBUG: search_documents tool invoked with query='{query}', limit={limit}")
            try:
                # Run async operation in sync context
                async def _async_search():
                    async with client:
                        result = await client.call_tool("search_documents", {
                            "query": query,
                            "limit": limit
                        })
                        
                        if isinstance(result, dict):
                            results = result.get("results", [])
                        elif isinstance(result, list):
                            results = result
                        else:
                            results = []
                        
                        if results:
                            search_results = []
                            for r in results:
                                if isinstance(r, dict):
                                    doc_name = r.get('document', 'Unknown')
                                    content = r.get('content', '')[:100]
                                    search_results.append(f"- {doc_name}: {content}...")
                                else:
                                    search_results.append(f"- {str(r)}")
                            
                            return f"Found {len(results)} results for '{query}':\n" + "\n".join(search_results)
                        else:
                            return f"No results found for '{query}'"
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to run in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, _async_search())
                            return future.result()
                    else:
                        return loop.run_until_complete(_async_search())
                except RuntimeError:
                    # No event loop, create new one
                    return asyncio.run(_async_search())
                    
            except Exception as e:
                print(f"🔍 DEBUG: search_documents error: {e}")
                return f"Error searching documents: {str(e)}"
        
        @tool
        def upload_folder(folder_path: str) -> str:
            """Upload all PDF documents from a folder to Milvus for semantic search."""
            print(f"📁 DEBUG: upload_folder tool invoked with folder_path='{folder_path}'")
            try:
                # Run async operation in sync context
                async def _async_upload_folder():
                    async with client:
                        result = await client.call_tool("upload_folder", {
                            "folder_path": folder_path
                        })
                        
                        # Handle different result formats
                        if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                            # Handle list of TextContent objects
                            for item in result:
                                if hasattr(item, 'text'):
                                    try:
                                        import json
                                        result_dict = json.loads(item.text)
                                        if isinstance(result_dict, dict):
                                            result = result_dict
                                            break
                                    except:
                                        continue
                        
                        if isinstance(result, dict):
                            status = result.get("status", "unknown")
                            message = result.get("message", "No message")
                            details = result.get("details", {})
                            
                            if status == "completed":
                                total_files = details.get("total_files", 0)
                                successful = details.get("successful", 0)
                                failed = details.get("failed", 0)
                                
                                return f"Folder upload completed!\n" \
                                       f"Folder: {folder_path}\n" \
                                       f"Total files processed: {total_files}\n" \
                                       f"Successfully uploaded: {successful}\n" \
                                       f"Failed: {failed}\n" \
                                       f"Message: {message}"
                            else:
                                return f"Folder upload failed: {message}"
                        else:
                            return f"Folder upload completed for: {folder_path}"
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to run in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, _async_upload_folder())
                            return future.result()
                    else:
                        return loop.run_until_complete(_async_upload_folder())
                except RuntimeError:
                    # No event loop, create new one
                    return asyncio.run(_async_upload_folder())
                    
            except Exception as e:
                print(f"📁 DEBUG: upload_folder error: {e}")
                return f"Error uploading folder: {str(e)}"
                
        @tool
        def delete_document(document_id: str) -> str:
            """Delete a document from the system by its document ID."""
            print(f"🗑️ DEBUG: delete_document tool invoked with document_id='{document_id}'")
            try:
                # Run async operation in sync context
                async def _async_delete():
                    async with client:
                        try:
                            # First try the delete_document_mcp POST endpoint
                            try:
                                print(f"🗑️ DEBUG: Calling delete_document_mcp tool")
                                result = await client.call_tool("delete_document_mcp", {
                                    "document_id": document_id
                                })
                            except Exception as tool_error:
                                # If the mcp tool fails, try the standard delete_document tool
                                print(f"🗑️ DEBUG: delete_document_mcp failed ({tool_error}), trying direct deletion")
                                
                                # For direct deletion, we need to make a direct HTTP request
                                import aiohttp
                                
                                # Construct the DELETE URL 
                                api_url = "http://localhost:8000"
                                delete_url = f"{api_url}/api/documents/{document_id}"
                                
                                print(f"🗑️ DEBUG: Sending DELETE request to {delete_url}")
                                
                                # Make DELETE request
                                async with aiohttp.ClientSession() as session:
                                    async with session.delete(delete_url) as response:
                                        if response.status == 200:
                                            result = await response.json()
                                        else:
                                            error_text = await response.text()
                                            return f"Failed to delete document: HTTP {response.status} - {error_text}"
                            
                            print(f"🗑️ DEBUG: Delete document result: {result}")
                            
                            # Handle different response formats from FastMCP
                            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                                # Handle list of TextContent objects from FastMCP
                                for item in result:
                                    if hasattr(item, 'text'):
                                        try:
                                            import json
                                            result_dict = json.loads(item.text)
                                            if isinstance(result_dict, dict):
                                                status = result_dict.get("status", "")
                                                if status == "success":
                                                    return f"Successfully deleted document with ID: {document_id}"
                                        except Exception as json_error:
                                            print(f"🗑️ DEBUG: Error parsing result JSON: {json_error}")
                            
                            # Continue with standard response format handling
                            if isinstance(result, dict):
                                status = result.get("status", "")
                                message = result.get("message", "")
                                
                                if status == "success":
                                    return f"Successfully deleted document with ID: {document_id}"
                                else:
                                    return message or f"Failed to delete document with ID: {document_id}"
                            else:
                                # Boolean or string response
                                if result is True or (isinstance(result, str) and "success" in str(result).lower()):
                                    return f"Successfully deleted document with ID: {document_id}"
                                else:
                                    # Check for success in the string representation
                                    if "success" in str(result).lower():
                                        return f"Successfully deleted document with ID: {document_id}"
                                    else:
                                        return f"Result of delete operation: {result}"
                        except Exception as inner_e:
                            print(f"🗑️ DEBUG: Inner delete error: {inner_e}")
                            return f"Error deleting document: {str(inner_e)}"
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to run in thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, _async_delete())
                            return future.result()
                    else:
                        return loop.run_until_complete(_async_delete())
                except RuntimeError:
                    # No event loop, create new one
                    return asyncio.run(_async_delete())
                    
            except Exception as e:
                print(f"🗑️ DEBUG: delete_document error: {e}")
                return f"Error deleting document: {str(e)}"

        return [list_documents, search_documents, upload_folder, delete_document]
    
    async def get_langgraph_tools(self):
        """Get LangGraph tools for agent creation with sync wrappers."""
        if not self.langgraph_client:
            return []
        
        try:
            original_tools = await self.langgraph_client.get_tools()
            print(f"🧮 DEBUG: Retrieved {len(original_tools)} LangGraph tools: {[t.name for t in original_tools]}")
            
            # Create sync-wrapped versions of the tools
            from langchain_core.tools import tool
            import concurrent.futures
            
            wrapped_tools = []
            
            for original_tool in original_tools:
                # Create a closure to capture the original tool
                def create_wrapper(orig_tool):
                    @tool
                    def wrapped_tool(*args, **kwargs) -> str:
                        """Sync wrapper for LangGraph MCP tool."""
                        print(f"🧮 DEBUG: {orig_tool.name} tool invoked with args={args}, kwargs={kwargs}")
                        try:
                            # Handle tool invocation in sync context
                            async def _async_invoke():
                                if hasattr(orig_tool, 'ainvoke'):
                                    if args:
                                        # If positional args, convert to dict if needed
                                        if len(args) == 1 and isinstance(args[0], (int, float)):
                                            # Single numeric argument - use as input
                                            result = await orig_tool.ainvoke(args[0])
                                        elif len(args) == 2 and all(isinstance(arg, (int, float)) for arg in args):
                                            # Two numeric arguments - create dict
                                            result = await orig_tool.ainvoke({"a": args[0], "b": args[1]})
                                        else:
                                            result = await orig_tool.ainvoke(args[0] if len(args) == 1 else args)
                                    elif kwargs:
                                        # Handle special case where args are passed in kwargs
                                        if 'args' in kwargs and isinstance(kwargs['args'], (list, tuple)):
                                            args_list = kwargs['args']
                                            if len(args_list) == 2:
                                                result = await orig_tool.ainvoke({"a": args_list[0], "b": args_list[1]})
                                            elif len(args_list) == 1:
                                                result = await orig_tool.ainvoke(args_list[0])
                                            else:
                                                result = await orig_tool.ainvoke(kwargs)
                                        else:
                                            result = await orig_tool.ainvoke(kwargs)
                                    else:
                                        result = await orig_tool.ainvoke({})
                                else:
                                    # Fall back to invoke if ainvoke not available
                                    if args:
                                        if len(args) == 1 and isinstance(args[0], (int, float)):
                                            result = orig_tool.invoke(args[0])
                                        elif len(args) == 2 and all(isinstance(arg, (int, float)) for arg in args):
                                            result = orig_tool.invoke({"a": args[0], "b": args[1]})
                                        else:
                                            result = orig_tool.invoke(args[0] if len(args) == 1 else args)
                                    elif kwargs:
                                        # Handle special case where args are passed in kwargs
                                        if 'args' in kwargs and isinstance(kwargs['args'], (list, tuple)):
                                            args_list = kwargs['args']
                                            if len(args_list) == 2:
                                                result = orig_tool.invoke({"a": args_list[0], "b": args_list[1]})
                                            elif len(args_list) == 1:
                                                result = orig_tool.invoke(args_list[0])
                                            else:
                                                result = orig_tool.invoke(kwargs)
                                        else:
                                            result = orig_tool.invoke(kwargs)
                                    else:
                                        result = orig_tool.invoke({})
                                return result
                            
                            # Run async operation in sync context
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # If loop is running, we need to run in thread
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(asyncio.run, _async_invoke())
                                        result = future.result()
                                else:
                                    result = loop.run_until_complete(_async_invoke())
                            except RuntimeError:
                                # No event loop, create new one
                                result = asyncio.run(_async_invoke())
                            
                            print(f"🧮 DEBUG: {orig_tool.name} result: {result}")
                            return str(result)
                            
                        except Exception as e:
                            print(f"🧮 DEBUG: {orig_tool.name} error: {e}")
                            return f"Error in {orig_tool.name}: {str(e)}"
                    
                    # Set the function name to match the original tool name
                    wrapped_tool.__name__ = orig_tool.name
                    wrapped_tool.name = orig_tool.name
                    return wrapped_tool
                
                wrapped_tools.append(create_wrapper(original_tool))
            
            print(f"🧮 DEBUG: Created {len(wrapped_tools)} sync-wrapped LangGraph tools")
            return wrapped_tools
            
        except Exception as e:
            print(f"Error getting LangGraph tools: {e}")
            return []
    
    async def check_fastmcp_health(self) -> bool:
        """Check FastMCP client health."""
        if not self.fastmcp_client:
            return False
        
        try:
            async with self.fastmcp_client:
                await self.fastmcp_client.ping()
            return True
        except:
            return False
    
    async def check_langgraph_health(self) -> bool:
        """Check LangGraph client health."""
        if not self.langgraph_client:
            return False
        
        try:
            tools = await self.langgraph_client.get_tools()
            return len(tools) > 0
        except:
            return False
