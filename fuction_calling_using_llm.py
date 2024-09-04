import json
import ollama
import asyncio
import requests
import time
import nest_asyncio

nest_asyncio.apply()

# In a real application, this would fetch data from a live database or API
def get_flight_times(departure: str, arrival: str) -> str:
    flights = {
        "NYC-LAX": {
            "departure": "08:00 AM",
            "arrival": "11:30 AM",
            "duration": "5h 30m",
        },
        "LAX-NYC": {
            "departure": "02:00 PM",
            "arrival": "10:30 PM",
            "duration": "5h 30m",
        },
        "LHR-JFK": {
            "departure": "10:00 AM",
            "arrival": "01:00 PM",
            "duration": "8h 00m",
        },
        "JFK-LHR": {
            "departure": "09:00 PM",
            "arrival": "09:00 AM",
            "duration": "7h 00m",
        },
        "CDG-DXB": {
            "departure": "11:00 AM",
            "arrival": "08:00 PM",
            "duration": "6h 00m",
        },
        "DXB-CDG": {
            "departure": "03:00 AM",
            "arrival": "07:30 AM",
            "duration": "7h 30m",
        },
    }

    key = f"{departure}-{arrival}".upper()
    return json.dumps(flights.get(key, {"error": "Flight not found"}))


async def run(model: str, user_input: str):
    client = ollama.AsyncClient()
    # Initialize conversation with a user query
    messages = [
        {
            "role": "user",
            "content": user_input,
            # "content": "What is the capital of India?",
        }
    ]

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_flight_times",
                    "description": "Get the flight times between two cities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "departure": {
                                "type": "string",
                                "description": "The departure city (airport code)",
                            },
                            "arrival": {
                                "type": "string",
                                "description": "The arrival city (airport code)",
                            },
                        },
                        "required": ["departure", "arrival"],
                    },
                },
            } ,
        ],
    )

    # print(f"Response: {response}")

    # Add the model's response to the conversation history
    messages.append(response["message"])

    # print(f"Conversation history:\n{messages}")

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        print("\nThe model didn't use the function. Its response was:")
        print(response["message"]["content"])
        return

    if response["message"].get("tool_calls"):
        # print(f"\nThe model used some tools")
        available_functions = {
            "get_flight_times": get_flight_times,
            "get_antonyms": get_antonyms,
            "weather_place": weather_place,
            "confirmed_cases": confirmed_cases,
        }
        # print(f"\navailable_function: {available_functions}")
        for tool in response["message"]["tool_calls"]:
            # print(f"available tools: {tool}")
            # tool: {'function': {'name': 'get_flight_times', 'arguments': {'arrival': 'LAX', 'departure': 'NYC'}}}
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"Function Invoked: {function_to_call}")

            if function_to_call == get_flight_times:
                function_response = function_to_call(
                    tool["function"]["arguments"]["departure"],
                    tool["function"]["arguments"]["arrival"],
                )

            print(f"function response: {function_response}")

            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )


while True:
    user_input = input("\n Please ask=> ")
    if not user_input:
        # user_input = "What is the flight time from NYC to LAX?"
        user_input = "Whats up with the weather in New York?"
    if user_input.lower() == "exit":
        break

    asyncio.run(run("llama3.1", user_input))
