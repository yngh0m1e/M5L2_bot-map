import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import requests
from datetime import datetime
import pytz

class DB_Map():
    def __init__(self, database):
        self.database = database
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_graph(self, path, cities, color=None):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, lng = coordinates
                ax.plot(lng, lat, 'o', color=color or 'blue', markersize=10)  # Используйте цвет по умолчанию, если не указан
                ax.text(lng + 1, lat + 1, city, horizontalalignment='right', transform=ccrs.Geodetic())

        plt.savefig(path)
        plt.close()

    def get_cities_by_country(self, country_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city
                              FROM cities
                              WHERE country = ?''', (country_name,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_cities_by_population_density(self, density):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city
                              FROM cities
                              WHERE population / (SELECT COUNT(*) FROM cities WHERE city=city) > ?''', (density,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_cities_by_country_and_density(self, country_name, density):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city
                              FROM cities
                              WHERE country = ? AND population / (SELECT COUNT(*) FROM cities WHERE city=city) > ?''', 
                           (country_name, density))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_weather(self, city_name):
        api_key = "b497e8e178c80e432b579b542a6d1289"
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        try:
            response = requests.get(base_url, params={"q": city_name, "appid": api_key, "units": "metric"})
            weather_data = response.json()
            if weather_data.get("cod") != 200:
                return None
            description = weather_data["weather"][0]["description"]
            temperature = weather_data["main"]["temp"]
            return f"{description}, {temperature}°C"
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

    def get_time(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                              FROM cities
                              WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            if coordinates:
                lat, lng = coordinates
                timezone = self.get_timezone(lat, lng)
                if timezone:
                    city_time = datetime.now(pytz.timezone(timezone))
                    return city_time.strftime("%Y-%m-%d %H:%M:%S")
            return None

    def get_timezone(self, lat, lng):
        api_key = "YOUR_GOOGLE_TIMEZONE_API_KEY"
        base_url = "https://maps.googleapis.com/maps/api/timezone/json"
        try:
            response = requests.get(base_url, params={"location": f"{lat},{lng}", "timestamp": datetime.now().timestamp(), "key": api_key})
            timezone_data = response.json()
            if timezone_data.get("status") == "OK":
                return timezone_data["timeZoneId"]
            else:
                return None
        except Exception as e:
            print(f"Error fetching timezone: {e}")
            return None

if __name__=="__main__":
    manager = DB_Map(DATABASE)
    manager.create_user_table()
