import os
import json
import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv

# ── Load environment variables from .env ──
load_dotenv()

# ── Connect to Azure MySQL ──
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        ssl_disabled=False
    )

# ── Tool 1: List all tables ──
def list_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return json.dumps({"tables": tables})

# ── Tool 2: Describe a table's columns ──
def describe_table(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            "field": row[0],
            "type": row[1],
            "null": row[2],
            "key": row[3]
        })
    cursor.close()
    conn.close()
    return json.dumps({"table": table_name, "columns": columns})

# ── Tool 3: Run a SELECT query ──
def run_sql_query(query):
    if not query.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed."})

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        return json.dumps({"columns": columns, "rows": results}, default=str)
    except mysql.connector.Error as e:
        return json.dumps({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

# ── Define tools for OpenAI ──
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables in the connected MySQL database.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Get the schema (columns and types) of a specific table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Execute a read-only SQL SELECT query and return results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# ── Map names to functions ──
def call_tool(name, args):
    if name == "list_tables":
        return list_tables()
    elif name == "describe_table":
        return describe_table(args["table_name"])
    elif name == "run_sql_query":
        return run_sql_query(args["query"])
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})

# ── Main chat function ──
def chat(user_message, conversation_history):
    client = OpenAI()  # Reads OPENAI_API_KEY from environment

    conversation_history.append({"role": "user", "content": user_message})

    print(f"\n{'='*60}")
    print(f"🧑 You: {user_message}")
    print(f"{'='*60}")

    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # If the model wants to call tools
        if assistant_message.tool_calls:
            conversation_history.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"  🔧 Calling tool: {fn_name}({json.dumps(fn_args)})")

                result = call_tool(fn_name, fn_args)
                print(f"  ✅ Tool returned: {result[:200]}...")  # Show first 200 chars

                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # Final answer from the model
            final_answer = assistant_message.content
            conversation_history.append({"role": "assistant", "content": final_answer})
            print(f"\n🤖 Agent:\n{final_answer}")
            return conversation_history

# ── Run the agent ──
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🤖 MySQL AI Agent")
    print("  Powered by OpenAI + Azure Database for MySQL")
    print("  Type 'quit' to exit")
    print("=" * 60)

    system_message = {
        "role": "system",
        "content": (
            "You are a helpful data analyst agent connected to an Azure Database for MySQL. "
            "You have 3 tools: list_tables, describe_table, and run_sql_query. "
            "ALWAYS start by listing tables and describing their schema before writing queries. "
            "Only generate SELECT statements. Never write INSERT, UPDATE, DELETE, or DROP. "
            "Present query results in clean, readable tables. "
            "If the user asks a question, figure out the right SQL to answer it."
        )
    }

    conversation_history = [system_message]

    while True:
        user_input = input("\n🧑 You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Goodbye!")
            break
        if not user_input:
            continue
        conversation_history = chat(user_input, conversation_history)
