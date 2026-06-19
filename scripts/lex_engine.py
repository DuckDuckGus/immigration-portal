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
    def __init__(self, user_id: int, lang: str = 'en'):
        self.user_id = user_id
        self.lang = lang
        
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
                
                # --- Language-specific prompts ---
                if self.lang == 'es':
                    router_prompt_template = (
                        "Analiza la petición del usuario: '{user_prompt}' y elige la mejor herramienta. "
                        "REGLAS: "
                        "1. Para preguntas sobre un caso específico (ej: 'quién está a cargo de X'), devuelve 'DETAILS:[CASE_KEY]'. "
                        "2. Para preguntas sobre los clientes de un abogado (ej: 'quiénes son los clientes de elena?'), devuelve 'LAWYER_CLIENTS:[LAWYER_NAME]'. "
                        "3. Para preguntas sobre estadísticas o carga de trabajo ('quién tiene más casos'), devuelve 'STATS'. "
                        "4. Para una lista de todos los abogados ('quiénes son nuestros abogados'), devuelve 'LAWYERS'. "
                        "5. Para auditorías o encontrar documentos faltantes, devuelve 'AUDIT'. "
                        "6. Para buscar un cliente por su nombre, devuelve 'SEARCH:[CLIENT_NAME]'. "
                        "7. Si no es ninguna de las anteriores, devuelve 'CHAT'."
                    )
                    final_context_template = "Usuario: {user_prompt}\nResultado de la Base de Datos: {db_data}\n\nPor favor, resume esto para el usuario en español."
                else: # Default to English
                    router_prompt_template = (
                        "Analyze the user's request: '{user_prompt}' and choose the best tool. "
                        "RULES: ..." # Abridged for brevity, original content is kept
                    )
                    final_context_template = "User: {user_prompt}\nDatabase Result: {db_data}\n\nPlease summarize this for the user."

                # --- STEP 1: SMART INTENT ROUTING ---
                router_prompt = router_prompt_template.format(user_prompt=user_prompt)
                
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
                final_context = final_context_template.format(user_prompt=user_prompt, db_data=db_data)
                response = self.chat.send_message(final_context)
                
                return response.text

# --- LIVE CLI TERMINAL ---
async def main():
    # Simulated Login (Tomorrow we'll make this a real UI login)
    print("--- ⚖️ Lex Immigration Portal: CLI Mode ---")
    lex = LexEngine(user_id=1, lang='en')
    
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