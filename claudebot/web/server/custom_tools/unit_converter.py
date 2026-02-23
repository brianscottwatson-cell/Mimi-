"""
Unit Converter Tool for Mimi
Converts between common units: distance, weight, temperature, volume
"""


def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert between various units.
    
    Supported conversions:
    - Distance: miles, km, feet, meters, inches, cm
    - Weight: lbs, kg, oz, grams
    - Temperature: fahrenheit, celsius, kelvin
    - Volume: gallons, liters, cups, ml, oz_fluid
    """
    
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    # Distance conversions (base: meters)
    distance_to_meters = {
        'miles': 1609.34,
        'mi': 1609.34,
        'km': 1000,
        'kilometers': 1000,
        'feet': 0.3048,
        'ft': 0.3048,
        'meters': 1,
        'm': 1,
        'inches': 0.0254,
        'in': 0.0254,
        'cm': 0.01,
        'centimeters': 0.01,
    }
    
    # Weight conversions (base: kg)
    weight_to_kg = {
        'lbs': 0.453592,
        'lb': 0.453592,
        'pounds': 0.453592,
        'kg': 1,
        'kilograms': 1,
        'oz': 0.0283495,
        'ounces': 0.0283495,
        'grams': 0.001,
        'g': 0.001,
    }
    
    # Volume conversions (base: liters)
    volume_to_liters = {
        'gallons': 3.78541,
        'gal': 3.78541,
        'liters': 1,
        'l': 1,
        'cups': 0.236588,
        'ml': 0.001,
        'milliliters': 0.001,
        'oz_fluid': 0.0295735,
        'fl_oz': 0.0295735,
    }
    
    result = None
    conversion_type = None
    
    # Try distance conversion
    if from_unit in distance_to_meters and to_unit in distance_to_meters:
        meters = value * distance_to_meters[from_unit]
        result = meters / distance_to_meters[to_unit]
        conversion_type = "distance"
    
    # Try weight conversion
    elif from_unit in weight_to_kg and to_unit in weight_to_kg:
        kg = value * weight_to_kg[from_unit]
        result = kg / weight_to_kg[to_unit]
        conversion_type = "weight"
    
    # Try volume conversion
    elif from_unit in volume_to_liters and to_unit in volume_to_liters:
        liters = value * volume_to_liters[from_unit]
        result = liters / volume_to_liters[to_unit]
        conversion_type = "volume"
    
    # Temperature conversions (special case - not base unit system)
    elif from_unit in ['fahrenheit', 'f', 'celsius', 'c', 'kelvin', 'k'] and \
         to_unit in ['fahrenheit', 'f', 'celsius', 'c', 'kelvin', 'k']:
        
        # Normalize unit names
        temp_map = {'f': 'fahrenheit', 'c': 'celsius', 'k': 'kelvin'}
        from_unit = temp_map.get(from_unit, from_unit)
        to_unit = temp_map.get(to_unit, to_unit)
        
        # Convert to celsius first
        if from_unit == 'fahrenheit':
            celsius = (value - 32) * 5/9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:
            celsius = value
        
        # Convert from celsius to target
        if to_unit == 'fahrenheit':
            result = celsius * 9/5 + 32
        elif to_unit == 'kelvin':
            result = celsius + 273.15
        else:
            result = celsius
        
        conversion_type = "temperature"
    
    else:
        return {
            "status": "error",
            "message": f"Cannot convert from '{from_unit}' to '{to_unit}'. Unsupported units or incompatible types.",
            "supported_distance": list(set(distance_to_meters.keys())),
            "supported_weight": list(set(weight_to_kg.keys())),
            "supported_volume": list(set(volume_to_liters.keys())),
            "supported_temperature": ["fahrenheit", "f", "celsius", "c", "kelvin", "k"],
        }
    
    return {
        "status": "success",
        "original_value": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
        "result": round(result, 4),
        "conversion_type": conversion_type,
        "formatted": f"{value} {from_unit} = {round(result, 2)} {to_unit}",
    }


# --- Required exports ---

TOOLS = [
    {
        "name": "convert_units",
        "description": "Convert between common units (distance, weight, temperature, volume). Supports: miles/km/feet/meters/inches/cm, lbs/kg/oz/grams, fahrenheit/celsius/kelvin, gallons/liters/cups/ml.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "The numeric value to convert",
                },
                "from_unit": {
                    "type": "string",
                    "description": "The source unit (e.g. 'miles', 'lbs', 'fahrenheit')",
                },
                "to_unit": {
                    "type": "string",
                    "description": "The target unit (e.g. 'km', 'kg', 'celsius')",
                },
            },
            "required": ["value", "from_unit", "to_unit"],
        },
    },
]

HANDLERS = {
    "convert_units": convert_units,
}
