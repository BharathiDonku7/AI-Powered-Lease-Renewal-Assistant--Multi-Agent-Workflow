"""
Tools available to the Renewal Decision Agent.

- lookup_market_rate: mocked market intelligence service (would be a real API
  like Zillow or RentCast in production)
- get_local_context: live external API call to Zippopotam.us for real-time
  geographic context based on zipcode
"""
import requests
from langchain_core.tools import tool


# Mocked market data — production would hit a real market intelligence API
MARKET_DATA = {
    "Maple Ridge Apartments": {
        "average_market_rate": 1875,
        "occupancy_rate": 0.94,
        "demand_trend": "high",
        "comparable_units_available": 3,
        "zipcode": "75080"
    },
    "Oak Hill Residences": {
        "average_market_rate": 1725,
        "occupancy_rate": 0.88,
        "demand_trend": "moderate",
        "comparable_units_available": 7,
        "zipcode": "75081"
    },
}


@tool
def lookup_market_rate(property_name: str) -> dict:
    """
    Look up current market intelligence for a specific property.
    Returns average market rent, occupancy rate, demand trend,
    and number of comparable units available.
    """
    if property_name in MARKET_DATA:
        return {
            "property": property_name,
            "data": MARKET_DATA[property_name],
            "source": "Market Intelligence API (mocked for demo)"
        }
    return {
        "property": property_name,
        "data": None,
        "note": "Property not found in market database"
    }


@tool
def get_local_context(zipcode: str) -> dict:
    """
    Fetch real-time local geographic context for a US zipcode using a live
    external API. Returns city, state, and place metadata. Useful for
    tailoring renewal communications to the resident's local market.
    """
    try:
        response = requests.get(
            f"https://api.zippopotam.us/us/{zipcode}",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "zipcode": zipcode,
                "city": data["places"][0]["place name"],
                "state": data["places"][0]["state"],
                "state_abbr": data["places"][0]["state abbreviation"],
                "source": "Zippopotam.us (live external API)"
            }
        return {
            "zipcode": zipcode,
            "error": f"API returned status {response.status_code}",
            "source": "Zippopotam.us (live external API)"
        }
    except Exception as e:
        return {
            "zipcode": zipcode,
            "error": str(e),
            "source": "Zippopotam.us (live external API)"
        }