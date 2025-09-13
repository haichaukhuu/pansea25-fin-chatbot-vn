# 🌦 Weather Service 

## 📌 Purpose

The Weather Service is a standalone **tool** for the AI chatbot.
It crawls and scrapes official weather websites, extracts weather data, and returns it in a **structured JSON format**.

This makes it easier for the chatbot to **retrieve, compute, and present** weather information without handling scraping logic itself.

No AI model is involved in this service.
---

## 🔑 Inputs and Outputs

### Input

* **Location** (from user query or profile)
* Example 1:

```json
{ "location": "An Giang" }

* Example 2:
```json
{ "location": "Mỹ Tho (Đồng Tháp)" }
```

# NOTE: The service uses a predefined JSON mapping of locations to official weather URLs. The user may provide a city, a general province, or a specific area; some users may provide locations or city/province names that are not exactly similar in comparison with the structure JSON file. The service must account for these variations. Sometimes the user may not specify a location, in which case the service can default to the location in the userdatabase or return an error.

### Output

* **AI-friendly JSON** containing:

  * Current weather
  * Forecast (today, tomorrow, etc.)
  * Metadata (location, source URL, last updated)

Example output:

```json
{
  "location": "Rạch Giá (An Giang)",
  "source_url": "https://www.nchmf.gov.vn/kttv/vi-VN/1/rach-gia-an-giang-w41.html",
  "last_updated": "2025-09-12T15:00:00+07:00",
  "current": {
    "temperature_c": 30,
    "humidity_percent": 75,
    "wind_speed_kmh": 12,
    "condition": "Cloudy"
  },
  "forecast": {
    "today": [
      { "time": "06:00", "temperature_c": 26, "condition": "Light Rain" },
      { "time": "12:00", "temperature_c": 30, "condition": "Cloudy" },
      { "time": "18:00", "temperature_c": 28, "condition": "Rain Showers" }
    ],
    "tomorrow": [
      { "time": "06:00", "temperature_c": 25, "condition": "Cloudy" },
      { "time": "12:00", "temperature_c": 31, "condition": "Sunny" },
      { "time": "18:00", "temperature_c": 27, "condition": "Clear" }
    ]
  }
}
```

---

## 🔄 Workflow

1. **Chatbot Request**

   * User asks: “What’s the weather in Bạc Liêu tomorrow?”
   * Chatbot calls the Weather Service with the location.

2. **URL Lookup**

   * Service finds the correct weather website URL from a stored JSON mapping.

3. **Fetch & Scrape**

   * Service fetches the webpage.
   * Extracts weather details (temperature, humidity, condition, etc.) using scraping.

4. **Format JSON**

   * Data is cleaned and structured into a predefined JSON schema.

5. **Return to Chatbot**

   * JSON is returned.
   * Chatbot uses it to generate a natural language response.

---

## 🛠 Technologies

* **Fetching**:

  * `httpx` (for HTTP requests)
  * `playwright` (if JavaScript rendering is needed)

* **Scraping**:

  * `BeautifulSoup4`
  * `lxml`

* **Validation**:

  * `pydantic` (ensures consistent JSON format)

* **API Service Layer**:

  * `FastAPI` → exposes `/weather?location=...` endpoint
