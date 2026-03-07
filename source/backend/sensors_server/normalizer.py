def normalize_rest_data(raw_data):
    """
    Transforms the raw JSON payload from the simulator into our Standard Event format
    strictly matching the defined JSON Schema.
    Handles both 'rest.scalar.v1' (single value) and 'rest.chemistry.v1' (array of measurements).
    """
    # Base structure matching the exact keys required by the Schema
    normalized_event = {
        "device_id": raw_data.get("sensor_id", "unknown_device"),
        "time": raw_data.get("captured_at", ""),  
        "status": raw_data.get("status", "ok"),   
        "metrics": [],                            
        "metadata": {}
    }

    # Handle 'rest.scalar.v1' schema (e.g., temperature, humidity)
    if "metric" in raw_data and "value" in raw_data:
        # Create the metric object as requested by the schema
        metric_obj = {
            "metric_name": raw_data["metric"],
            "value": raw_data["value"]
        }
        # Add the 'unit' field only if it exists in the raw data
        if "unit" in raw_data:
            metric_obj["unit"] = raw_data["unit"]
            
        normalized_event["metrics"].append(metric_obj)

    # Handle 'rest.chemistry.v1' schema (e.g., air quality with multiple measurements)
    elif "measurements" in raw_data:
        for item in raw_data["measurements"]:
            metric_name = item.get("metric")
            if metric_name and "value" in item:
                # Create the metric object for each measurement in the array
                metric_obj = {
                    "metric_name": metric_name,
                    "value": item["value"]
                }
                # Add the 'unit' field only if it exists in this specific measurement
                if "unit" in item:
                    metric_obj["unit"] = item["unit"]
                    
                normalized_event["metrics"].append(metric_obj)

    return normalized_event