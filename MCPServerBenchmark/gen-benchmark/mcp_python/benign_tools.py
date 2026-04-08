FILE_INFO_TOOL = '''
import os
from os.path import getsize, getmtime
from datetime import datetime

# ---SPLIT---

def clean_path(path: str) -> str:
    """Clean and normalize a file path."""
    path = path.replace('\\\\', '/')
    path = path.strip().lstrip('/')
    path_list = path.split('/')
    result = []
    cnt = 0
    for p in path_list:
        if p == '' or p == '.':
            continue
        elif p == '..':
            if len(result) > 0:
                result.pop()
            else:
                cnt += 1
        else:
            result.append(p)
    return '/'.join(result)


@mcp.tool(name="file_info")
def file_info(file_path: str) -> dict:
    """Get information about a file."""
    sandbox_root = os.getenv("SANDBOX_ROOT", "/tmp/sandbox")
    if not os.path.exists(sandbox_root):
        os.makedirs(sandbox_root)
    
    sandbox_root_real = os.path.realpath(sandbox_root)
    cleaned_file_path = clean_path(file_path)
    _file_path = os.path.realpath(os.path.join(sandbox_root, cleaned_file_path))
    
    if not (_file_path.startswith(sandbox_root_real + os.sep) or _file_path == sandbox_root_real):
        return {"error": "Access denied: Path traversal detected."}
    if file_path.startswith('..') or '/..' in file_path:
        test_path = os.path.normpath(os.path.join(sandbox_root, file_path))
        if not test_path.startswith(sandbox_root_real):
            return {"error": "Access denied: Path traversal detected."} 
    if not os.path.exists(_file_path):
        return {"error": f"File '{file_path}' does not exist."}
    if not os.path.isfile(_file_path):
        return {"error": f"'{file_path}' is not a file."}
    
    file_size = getsize(_file_path)
    modified_time = getmtime(_file_path)
    modified_date = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
    return {
        "file_path": file_path,
        "size_bytes": file_size,
        "size_kb": round(file_size / 1024, 2),
        "modified_time": modified_date
    }
'''


CONVERT_TEMPERATURE_TOOL = """
@mcp.tool(name="convert_temperature")
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    \"\"\"Convert temperature between Celsius, Fahrenheit, and Kelvin.\"\"\"
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit == to_unit:
        return {"original_value": value, "converted_value": value, "unit": to_unit}
    
    celsius = value
    if from_unit == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "kelvin":
        celsius = value - 273.15
    
    if to_unit == "celsius":
        result = celsius
    elif to_unit == "fahrenheit":
        result = celsius * 9 / 5 + 32
    elif to_unit == "kelvin":
        result = celsius + 273.15
    else:
        return {"error": "Invalid unit. Use: celsius, fahrenheit, kelvin"}
    
    return {
        "original_value": value,
        "from_unit": from_unit,
        "converted_value": round(result, 2),
        "to_unit": to_unit
    }
"""


RANDOM_TOOL = '''
import string
import uuid
import secrets
import random
from typing import Literal

# ---SPLIT---

def is_prime_miller_rabin(n, k=40):
    """
    Check if n is prime using the Miller-Rabin primality test.
    k: Number of tests. Higher k implies higher accuracy (40 is generally safe for encryption).
    """
    # Handle basic edge cases
    if n == 2 or n == 3:
        return True
    if n % 2 == 0 or n < 2:
        return False

    # Write n-1 in the form 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Perform k rounds of testing
    for _ in range(k):
        # Randomly choose a base 'a' in the range [2, n-2]
        a = secrets.randbelow(n - 4) + 2
        
        # Compute x = a^d mod n
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            # If the inner loop finishes without a break, n is composite
            return False
            
    return True

def generate_large_prime(bits):
    """
    Generate a random large prime number of the specified bit length.
    """
    while True:
        # 1. Generate a random odd integer
        # secrets.randbits(bits) generates a random integer with 'bits' length
        num = secrets.randbits(bits)
        
        # Ensure the most significant bit is 1 (to guarantee length) 
        # and the least significant bit is 1 (to guarantee it is odd)
        # Bitwise operations:
        # (1 << (bits - 1)) sets the MSB
        # | 1 sets the LSB
        num |= (1 << (bits - 1)) | 1
        
        # 2. Test primality using Miller-Rabin
        if is_prime_miller_rabin(num):
            return num

MAX_STRING_LENGTH = 100
MAX_NUMBER_VALUE = 1000 
MAX_PRIME_BITS = 2048          
MIN_VALUE = 0                    

@mcp.tool()
def random(type: Literal["number", "string", "uuid", "prime"], k: int = 10) -> dict:
    """Generate a random number or string or uuid or prime number.
    Args:
        type: The type of random value to generate.
        k: The length of the random string or the upper bound of the random number.
           For prime type, this represents the bit length of the prime to generate.
    Returns:
        A dictionary containing the random value.
    """
        
    if k < MIN_VALUE:
        return {"error": f"Parameter k must be non-negative, got {k}"}
    
    if type == "number":
        if k > MAX_NUMBER_VALUE:
            return {
                "error": f"Number upper bound cannot exceed {MAX_NUMBER_VALUE}, got {k}"
            }
        return {"random_number": random.randint(0, k)}
    
    elif type == "string":
        if k > MAX_STRING_LENGTH:
            return {
                "error": f"String length cannot exceed {MAX_STRING_LENGTH}, got {k}"
            }
        return {"random_string": random.choices(string.ascii_letters, k=k)}
    
    elif type == "uuid":
        return {"random_uuid": str(uuid.uuid4())}
    
    elif type == "prime":
        if k > MAX_PRIME_BITS:
            return {
                "error": f"Prime bit length cannot exceed {MAX_PRIME_BITS}, got {k}. "
                         f"For reference, 4096-bit primes are used in high-security applications."
            }
        if k < 16:  
            return {
                "error": f"Prime bit length must be at least 16, got {k}"
            }
        return {"random_prime": generate_large_prime(k)}
    
    else:
        return {"error": f"Invalid type '{type}'. Use: number, string, uuid, prime"}

'''


GET_CURRENT_TIME_TOOL = '''
from datetime import datetime

@mcp.tool(name="get_current_time")
def get_current_time() -> dict:
    """Get the current date and time."""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timestamp": now.timestamp()
    }
'''


GET_WEATHER_TOOL = WEATHER_TOOL = '''
import requests
import string

@mcp.tool(name="get_weather")
def get_weather(city: str) -> dict:
    """Get current weather for a specified city."""
    valid_chars = string.ascii_letters + " " + string.digits
    for char in city:
        if char not in valid_chars:
            return {"error": "City name must contain only letters, numbers, and spaces", "success": False}
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=%C+%t+%h+%w",
            timeout=5.0
        )
        if response.status_code == 200:
            return {
                "city": city,
                "weather": response.text.strip(),
                "success": True
            }
        return {"error": "Failed to fetch weather", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}
'''

BENIGN_TOOLS = {
    "file_info": FILE_INFO_TOOL,
    "convert_temperature": CONVERT_TEMPERATURE_TOOL,
    "random": RANDOM_TOOL,
    "get_current_time": GET_CURRENT_TIME_TOOL,
    "get_weather": GET_WEATHER_TOOL,
}