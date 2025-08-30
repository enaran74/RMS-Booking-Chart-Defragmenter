"""
ChatGPT service for generating move explanations
Uses OpenAI API to analyze booking charts and explain defragmentation rationale
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatGPTService:
    """Service for integrating with OpenAI ChatGPT API to explain defragmentation moves"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Using the latest efficient model
        
    def _is_configured(self) -> bool:
        """Check if ChatGPT API is properly configured"""
        return bool(self.api_key and self.api_key.startswith('sk-'))
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the ChatGPT API connection"""
        if not self._is_configured():
            return {
                "success": False,
                "message": "OpenAI API key not configured or invalid",
                "details": {"error": "API key missing or doesn't start with 'sk-'"}
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": "Hello, this is a test connection. Please respond with 'Connection successful'."}
                        ],
                        "max_tokens": 10
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "ChatGPT API connection successful",
                        "details": {
                            "model": self.model,
                            "response": result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "success": False,
                        "message": f"ChatGPT API error: {response.status_code}",
                        "details": {"error": error_data.get("error", {}).get("message", "Unknown error")}
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "ChatGPT API connection timeout",
                "details": {"error": "Request timed out after 30 seconds"}
            }
        except Exception as e:
            logger.error(f"ChatGPT API test error: {e}")
            return {
                "success": False,
                "message": "ChatGPT API connection failed",
                "details": {"error": str(e)}
            }
    
    def _format_move_data_for_analysis(self, moves_data: List[Dict], chart_data: Dict, property_code: str) -> str:
        """Format move suggestions and chart data for ChatGPT analysis"""
        
        # Extract key information from moves
        move_summaries = []
        for move in moves_data[:10]:  # Limit to first 10 moves to avoid token limits
            move_summary = {
                "guest_name": move.get("guest_name", "Unknown"),
                "from_unit": move.get("from_unit_name", "Unknown"),
                "to_unit": move.get("to_unit_name", "Unknown"),
                "check_in": move.get("check_in", ""),
                "check_out": move.get("check_out", ""),
                "nights": move.get("nights", 0),
                "nights_freed": move.get("nights_freed", 0),
                "strategic_importance": move.get("strategic_importance_level", "Unknown"),
                "reason": move.get("reason", "")
            }
            move_summaries.append(move_summary)
        
        # Extract chart information
        chart_summary = {
            "property_code": property_code,
            "total_categories": len(chart_data.get("categories", [])) if chart_data else 0,
            "analysis_period": "Next 31 nights",
        }
        
        # Format for ChatGPT
        formatted_data = f"""
PROPERTY: {property_code}
ANALYSIS PERIOD: Next 31 nights from {datetime.now().strftime('%Y-%m-%d')}

SUGGESTED MOVES:
"""
        
        for i, move in enumerate(move_summaries, 1):
            formatted_data += f"""
{i}. {move['guest_name']} 
   - FROM: {move['from_unit']} 
   - TO: {move['to_unit']}
   - DATES: {move['check_in']} to {move['check_out']} ({move['nights']} nights)
   - NIGHTS FREED: {move['nights_freed']}
   - IMPORTANCE: {move['strategic_importance']}
   - REASON: {move['reason']}
"""
        
        if chart_data and chart_data.get("categories"):
            formatted_data += f"\nBOOKING CHART CONTEXT:\n"
            formatted_data += f"- Total accommodation categories: {chart_summary['total_categories']}\n"
            formatted_data += f"- Analysis covers booking patterns and gaps across all units\n"
            formatted_data += f"- Moves are designed to create longer contiguous availability blocks\n"
        
        return formatted_data
    
    async def explain_moves(self, moves_data: List[Dict], chart_data: Dict, property_code: str) -> Dict[str, Any]:
        """Generate explanation for defragmentation moves using ChatGPT"""
        
        if not self._is_configured():
            return {
                "success": False,
                "message": "ChatGPT API not configured. Please add your OpenAI API key in the Setup page.",
                "explanation": ""
            }
        
        if not moves_data:
            return {
                "success": False,
                "message": "No move suggestions available to explain",
                "explanation": ""
            }
        
        try:
            # Format the data for analysis
            formatted_data = self._format_move_data_for_analysis(moves_data, chart_data, property_code)
            
            # Create the prompt
            prompt = f"""You are an expert in hotel revenue management and booking optimization. Analyze the following defragmentation move suggestions and provide a clear, professional explanation of the rationale behind each suggested move.

{formatted_data}

Please provide your analysis in the following format:

1. Move Analysis Explanation:
   • For each move, explain WHY it makes sense from a revenue management perspective
   • Focus on how each move creates better booking continuity, reduces fragmentation, or improves availability blocks
   • Mention specific benefits like freeing up contiguous nights, reducing gaps, or optimizing unit utilization

2. Assessment of the Suggested Moves:
   • Provide an overall assessment of whether these moves are beneficial
   • Use checkmarks (✅) for good moves and explain why
   • If any moves seem questionable, explain the concerns

Keep the explanation concise but informative, using bullet points and clear language that a property manager would understand. Focus on the business benefits and booking optimization aspects."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    
                    return {
                        "success": True,
                        "message": "Move explanation generated successfully",
                        "explanation": explanation,
                        "moves_analyzed": len(moves_data),
                        "property_code": property_code
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    
                    return {
                        "success": False,
                        "message": f"ChatGPT API error: {error_message}",
                        "explanation": ""
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "ChatGPT API request timed out. Please try again.",
                "explanation": ""
            }
        except Exception as e:
            logger.error(f"ChatGPT explanation error: {e}")
            return {
                "success": False,
                "message": f"Error generating explanation: {str(e)}",
                "explanation": ""
            }

# Global instance
chatgpt_service = ChatGPTService()
