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
    def __init__(self, user_id: int):
        self.user_id = user_id
        
        # Permanent System Instruction for Lex
        self.chat = client.chats.create(
            model='gemini-3.1-flash-lite-preview',
            config=types.GenerateContentConfig(
                system_instruction=(
                    f"You are Lex the Robot, an expert legal-tech assistant for an immigration portal. "
                    f"Context: UserID {self.user_id}. "
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
                    f"Analyze the user's request: '{user_prompt}' and choose the best tool. "
                    "RULES: "
                    "1. For questions about a specific case file (e.g., 'who is in charge of X', 'is Y complete'), return 'DETAILS:[CASE_KEY]'. "
                    "2. For questions about a lawyer's clients (e.g., 'who are elena's clients?'), return 'LAWYER_CLIENTS:[LAWYER_NAME]'. "
                    "3. For questions about case counts or lawyer workload ('who has most cases'), return 'STATS'. "
                    "4. For a list of all lawyers ('who are our lawyers'), return 'LAWYERS'. "
                    "5. For audits or finding missing documents in general, return 'AUDIT'. "
                    "6. For searching for a client by their own name, return 'SEARCH:[CLIENT_NAME]'. "
                    "7. If none of the above, return 'CHAT'."
                )
                
                intent_raw = client.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=router_prompt
                ).text.strip().upper()

                # --- STEP 2: TOOL EXECUTION ---
                db_data = "No data retrieved."
                
                if 'STATS' in intent_raw:
                    result = await session.call_tool("get_lawyer_stats", arguments={})
                    db_data = result.content
                
                elif 'LAWYERS' in intent_raw:
                    # Calls the new list_all_lawyers tool
                    result = await session.call_tool("list_all_lawyers", arguments={})
                    db_data = result.content
                    
                elif 'AUDIT' in intent_raw:
                    result = await session.call_tool("audit_documents", arguments={
                        "user_id": self.user_id, "limit": 15
                    })
                    db_data = result.content
                    
                elif 'SEARCH:' in intent_raw:
                    # Extracts name from 'SEARCH:ELENA'
                    name_query = intent_raw.split(':')[-1]
                    result = await session.call_tool("search_clients", arguments={
                        "search_term": name_query, "user_id": self.user_id
                    })
                    db_data = result.content

                elif 'LAWYER_CLIENTS:' in intent_raw:
                    # Extracts lawyer name from 'LAWYER_CLIENTS:ELENA'
                    lawyer_name_query = intent_raw.split(':')[-1]
                    result = await session.call_tool("get_clients_for_lawyer", arguments={
                        "lawyer_name": lawyer_name_query
                    })
                    db_data = result.content

                elif 'DETAILS:' in intent_raw:
                    # Extracts case key from 'DETAILS:GARCIA_2026_101'
                    case_key_query = intent_raw.split(':')[-1]
                    result = await session.call_tool("get_case_details", arguments={
                        "case_key": case_key_query
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
    lex = LexEngine(user_id=1)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']: break
            if not user_input: continue
            
            print("Lex the Robot is checking the vault...")
            answer = await lex.ask_mcp(user_input)
            print(f"\nLex the Robot: {answer}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[Error]: {e}")

if __name__ == "__main__":
    asyncio.run(main())