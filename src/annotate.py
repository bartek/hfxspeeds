def extract_cars(annotations_response, frame_rate, distance, min_speed, min_distance):
    ar = annotations_response["response"]["annotationResults"][0]["objectAnnotations"]
    print(ar)
    cars = list(filter(is_car, ar))
    print(cars)

def is_car(oa):
    return oa["entity"]["description"] == "car"

