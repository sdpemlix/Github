from groq import Groq
import json
import asyncio
import nest_asyncio
# Initialize Groq client
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

api_key = "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"
if not api_key:
    raise ValueError("API key for Groq is not set. Please set the GROQ_API_KEY environment variable.")
client = Groq(api_key=api_key)

def get_groq_response(text):
    messages = [
        {
            "role": "user",
            "content": text,
        },
        {
            "role": "system",
            "content": "Please provide a concise, one-line response."
        }
    ]
    try:
        tools = [
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
            }
        ]
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        if tool_calls:
            available_functions = {
                "get_flight_times": get_flight_times,
            }
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    departure=function_args.get("departure"),
                    arrival=function_args.get("arrival")
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            second_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages
            )
            return second_response.choices[0].message.content
        else:
            print(f"Gorq:{response.choices[0].message.content}")
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting response from Groq API: {e}")
        return "Sorry, I couldn't get a response from the server."
