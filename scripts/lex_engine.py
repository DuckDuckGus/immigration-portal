import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing API Key!")

client = genai.Client(api_key=api_key)

class LexEngine:
    def __init__(self, current_user_id: int, role: str):
        self.user_id = current_user_id
        self.role = role
        
        # This chat object ONLY sees the clean conversation now
        self.chat = client.chats.create(
            model='gemini-3.1-flash-lite-preview',
            config=types.GenerateContentConfig(
                system_instruction=(
                    f"You are Lex, a bilingual legal assistant. "
                    f"Logged in user ID: {self.user_id} | Role: {self.role}. "
                    "CRITICAL RULES: "
                    "1. Always respond in the EXACT language the user used. "
                    "2. NEVER invent or guess information. If the database returns 'SYSTEM MESSAGE: No client found', you MUST tell the user the client could not be found. Do not guess their nationality."
                )
            )
        )

    async def ask_mcp(self, user_prompt: str):
        server_params = StdioServerParameters(
            command="python",
            args=["scripts/lex_mcp_server.py"], 
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("Lex is thinking (and connecting to MCP)...")
                
                # ---------------------------------------------------------
                # 1. THE STATELESS ROUTER (Does not poison chat history)
                # ---------------------------------------------------------
                router_prompt = (
                    f"The user just said: '{user_prompt}'.\n"
                    f"If they are asking to find, search, or look up a specific client, reply with JUST their name (no punctuation).\n"
                    f"If they are asking for missing documents or an audit, reply with exactly 'AUDIT'.\n"
                    f"If it's just normal conversation, a greeting, or a correction, reply with 'CONVERSATION'."
                )
                
                intent_response = client.models.generate_content(
                    model='gemini-3.1-flash-lite-preview',
                    contents=router_prompt
                )
                ai_intent = intent_response.text.strip().replace(".", "").replace("?", "")
                
                # ---------------------------------------------------------
                # 2. EXECUTE AND RESPOND (Using clean chat history)
                # ---------------------------------------------------------
                if ai_intent == 'AUDIT':
                    result = await session.call_tool("audit_documents", arguments={
                        "user_id": self.user_id, "role": self.role, "limit": 20
                    })
                    final_answer = self.chat.send_message(f"User asked: '{user_prompt}'. Database data: {result.content}. Summarize this.")
                    return final_answer.text
                    
                elif ai_intent not in ['CONVERSATION', 'AUDIT']:
                    # It extracted a name!
                    result = await session.call_tool("search_clients", arguments={
                        "search_term": ai_intent, "user_id": self.user_id, "role": self.role
                    })
                    final_answer = self.chat.send_message(f"User asked: '{user_prompt}'. Database data for {ai_intent}: {result.content}. Answer the user accurately based ONLY on this data.")
                    return final_answer.text
                
                else:
                    # Normal conversation (like "No, he's from Mali")
                    final_answer = self.chat.send_message(user_prompt)
                    return final_answer.text

# --- LIVE TEST ---
if __name__ == "__main__":
    async def main():
        print("--- Lex Live MCP Session ---")
        lex = LexEngine(current_user_id=1, role='Admin')
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            response = await lex.ask_mcp(user_input)
            print(f"\nLex: {response}")

    asyncio.run(main())