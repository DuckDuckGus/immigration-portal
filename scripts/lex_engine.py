import os
import asyncio
import sys
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. SETUP & PATHING
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY in .env file!")

client = genai.Client(api_key=api_key)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class LexEngine:
    def __init__(self, user_id: int, role: str):
        self.user_id = user_id
        self.role = role
        
        # Permanent System Instruction for Lex
        self.chat = client.chats.create(
            model='gemini-3.1-flash-lite-preview',
            config=types.GenerateContentConfig(
                system_instruction=(
                    f"You are Lex, an expert legal-tech assistant for an immigration portal. "
                    f"Context: UserID {self.user_id}, Role {self.role}. "
                    "RULES: "
                    "1. Respond in the same language as the user (English/Spanish). "
                    "2. Use ONLY provided database data. If data is missing, say so politely. "
                    "3. Be concise and professional, like a helpful peer."
                )
            )
        )

    async def ask_mcp(self, user_prompt: str):
        """
        Connects to the MCP server, routes the intent, and returns a summary.
        """
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(BASE_DIR, "lex_mcp_server.py")],
            env=os.environ.copy()
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # --- STEP 1: SMART INTENT ROUTING ---
                # We use a separate prompt to decide WHICH tool to call.
                router_prompt = (
                    f"Identify the user intent for: '{user_prompt}'\n"
                    "- If they want stats, case counts, or 'who has most cases': return 'STATS'\n"
                    "- If they want an audit or missing documents: return 'AUDIT'\n"
                    "- If they are searching for a person/client: return 'SEARCH:[NAME]'\n"
                    "- Otherwise: return 'CHAT'"
                )
                
                intent_raw = client.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=router_prompt
                ).text.strip().upper()

                # --- STEP 2: TOOL EXECUTION ---
                db_data = "No data retrieved."
                
                if 'STATS' in intent_raw:
                    # Calls the new get_lawyer_stats tool
                    result = await session.call_tool("get_lawyer_stats", arguments={})
                    db_data = result.content
                    
                elif 'AUDIT' in intent_raw:
                    result = await session.call_tool("audit_documents", arguments={
                        "user_id": self.user_id, "role": self.role, "limit": 15
                    })
                    db_data = result.content
                    
                elif 'SEARCH:' in intent_raw:
                    # Extracts name from 'SEARCH:ELENA'
                    name_query = intent_raw.split(':')[-1]
                    result = await session.call_tool("search_clients", arguments={
                        "search_term": name_query, "user_id": self.user_id, "role": self.role
                    })
                    db_data = result.content
                
                # --- STEP 3: FINAL RESPONSE GENERATION ---
                # We feed the DB data back into the main chat history
                final_context = f"User: {user_prompt}\nDatabase Result: {db_data}\n\nPlease summarize this for the user."
                response = self.chat.send_message(final_context)
                
                return response.text

# --- LIVE CLI TERMINAL ---
async def main():
    # Simulated Login (Tomorrow we'll make this a real UI login)
    print("--- ⚖️ Lex Immigration Portal: CLI Mode ---")
    lex = LexEngine(user_id=1, role='Admin')
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']: break
            if not user_input: continue
            
            print("Lex is checking the vault...")
            answer = await lex.ask_mcp(user_input)
            print(f"\nLex: {answer}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    asyncio.run(main())