from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
from flask_redis import FlaskRedis

app = Flask(__name__)

# Initalize extensions
limiter = Limiter(get_remote_address, app=app, default_limits=["2 per minute"])
redis_client = FlaskRedis(app)

# Set Configuration
app.config["REDIS_URL"] = "redis://localhost:6379"

# Set variables
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
weather_api_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{pincode}?unitGroup=metric&key={WEATHER_API_KEY}&contentType=json"


@app.route("/")
@limiter.exempt
def index():
    return render_template("index.html")


@app.route("/weather", methods=["POST"])
@limiter.limit("4 per minute")
def weather():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        # Lookup in Redis
        cached_response = redis_client.get(pincode)
        if cached_response:
            print(f"Data found in Redis for pincode:{pincode}")
            return cached_response

        response = requests.get(
            weather_api_url.format(pincode=pincode, WEATHER_API_KEY=WEATHER_API_KEY)
        )
        if response.status_code == 200:
            weather_data = response.text
            # return render_template("weather.html", weather=weather_data)
            redis_client.setex(pincode, 1800, weather_data)
            print(f"Data fetched from origin for pincode:{pincode}")
            return weather_data
        else:
            return "Error: Unable to fetch weather data"


app.run(debug=True)
