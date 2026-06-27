import requests

from errors import RoutingError


def get_route_info(start_lat, start_lon, end_lat, end_lon): #LON, LAT (not LAT, LON)
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )
    
    try:
        response = requests.get(url, params={"overview": "false"})
        data = response.json()

    except requests.RequestException as error:
        raise RoutingError(f"Routing request fail: {error}")
    except ValueError as error:
        raise RoutingError(f"Response is not valid format: {error}")

    if "routes" not in data:
        raise RoutingError(f"Routing API (value) error: {error}")
    route = data["routes"][0]
    #print(url)
    return {"distance_km": route["distance"]/1000, "duration_h": route["duration"]/3600}



# info = get_route_info(
#     42.6977, 23.3219,
#     43.2141, 27.9147
# )

# print(info)