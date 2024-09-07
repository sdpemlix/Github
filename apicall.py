from groq import Groq
import json
import asyncio
import nest_asyncio
import requests
import time


def weather_place(place_name: str) -> str:

    url = "https://weatherapi-com.p.rapidapi.com/forecast.json"

    querystring = {"q": place_name, "days": "3"}

    headers = {
        "x-rapidapi-key": "b6dc2081ccmsh282bec1ffdb6254p10b966jsn0c43c4330ada",
        "x-rapidapi-host": "weatherapi-com.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    return json.dumps(
        f"The weather in {response.json()['location']['name']} is {response.json()['current']}"
    )


# rapidapi.com
def confirmed_cases(country_name: str) -> str:
    url = "https://covid-19-data.p.rapidapi.com/country/code"

    querystring = {"format": "json", "code": country_name[:2].upper()}

    headers = {
        "x-rapidapi-key": "b6dc2081ccmsh282bec1ffdb6254p10b966jsn0c43c4330ada",
        "x-rapidapi-host": "covid-19-data.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    return json.dumps(response.json()[0]["confirmed"])


# for key in ["India", "USA", "Italy", "Australia", "Germany"]:
#     a = confirmed_cases(key)
#     print(a)
#     print(type(a))
#     time.sleep(2)


def get_antonyms(word: str) -> str:
    "Get the antonyms of the any given word"

    words = {
        "hot": "cold",
        "small": "big",
        "weak": "strong",
        "light": "dark",
        "lighten": "darken",
        "dark": "bright",
    }

    return json.dumps(words.get(word, "Not available in database"))
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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_antonyms",
                    "description": "Get the antonyms of any given words",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "word": {
                                "type": "string",
                                "description": "The word for which the opposite is required.",
                            },
                        },
                        "required": ["word"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "weather_place",
                    "description": "Get the weather condition of any particular place",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "place_name": {
                                "type": "string",
                                "description": "The place for which the weather data is required",
                            },
                        },
                        "required": ["country_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "confirmed_cases",
                    "description": "Get the number of confirmed COVID cases for this particular country",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "country_name": {
                                "type": "string",
                                "description": "The country for which the number of confirmed COVID cases is required.",
                            },
                        },
                        "required": ["country_name"],
                    },
                },
            },
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
                "get_antonyms": get_antonyms,
                "weather_place": weather_place,
                "confirmed_cases": confirmed_cases,
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
