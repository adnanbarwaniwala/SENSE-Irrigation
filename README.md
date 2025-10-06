# 🌿 SENSE-Irrigation  
*Smart, Sensor-Driven Hourly Irrigation Management System*  

---

### 💧 Overview  

**SENSE-Irrigation** (**S**ensor **EN**abled **S**mart **E**vapotranspiration) is a Python-powered system that decides *when* and *how much* to irrigate crops — automatically, precisely, and intelligently.  
It combines **real-time sensor readings** with **live weather data** to make hour-by-hour irrigation decisions, conserving water while keeping the soil perfectly balanced.  

> Think of it as your crop’s personal water manager — always watching, thinking, and acting on time.  

---

### ⚙️ How It Works  

1. 🌡️ The **Metro M0 Express board** reads temperature and humidity using a **DHT11** sensor.  
2. 🌱 The **YL-69 soil moisture probe** measures how much water is left in the soil.  
3. 🌤️ The system pulls **hourly weather data** (solar radiation, wind speed, pressure, rainfall) from the **Open-Meteo API**.  
4. 💻 Using the **RefET** library, it calculates **Reference Evapotranspiration (ETo)** via the **FAO-56 Penman-Monteith** equation — the gold standard in irrigation science.  
5. 🌾 A crop coefficient (**Kc**) adjusts ETo → **ETc**, representing actual crop water use.  
6. 📉 The program predicts soil water changes by subtracting ETc and adding rainfall.  
7. 🚰 If the soil moisture is predicted to fall below **60%**, the system calculates how much irrigation is needed to bring it back to the **60–80% safe zone**.  
8. 📜 All results — soil readings, forecasts, and irrigation recommendations — are logged in `irrigation_data.txt`.

---

## Repo Structure
- `main.py`: Main script that runs the full hourly irrigation logic.
- `functions.py`: Contains all modular functions: sensor reading, ETo, ETc, soil water, irrigation calculation, etc.
- `irrigation_data.txt`: Stores hourly soil water and irrigation data logs.
- `LICENSE`: Project license (Apache 2.0).
- `README.md`: Project overview, setup instructions, and usage details.


### 🧠 Tech Stack  

| Component | Purpose |
|------------|----------|
| 🐍 **Python** | Main language for logic, control, and data analysis |
| ⚡ **CircuitPython** | Reads DHT11 and soil sensor data on Metro M0 |
| 🔌 **PySerial** | Enables communication between Metro and PC |
| 🌤️ **Open-Meteo API** | Provides real-time weather data |
| 🌿 **RefET Library** | Calculates FAO-56 hourly evapotranspiration |
| 💾 **AnalogIO + Adafruit DHT** | Reads sensor values |
| 📈 *(Future)* **Matplotlib / Streamlit** | For data visualization and UI |

---

### 🧩 Project Logic (In Simple Words)

Imagine it’s **10 AM**.  
- The soil has **50 mm** of available water.  
- Sensors send readings to your laptop.  
- Weather data says it’s hot and windy — high ETc expected.  
- The system predicts that by **11 AM**, soil moisture will drop below 60%.  
- It automatically recommends (or triggers) irrigation to restore the soil to around **75%**.  

By the end of the day — water saved, plants happy, and zero guesswork. 🌾  

---

### 🔬 Features  

- Real-time sensor integration (DHT11 + YL-69)  
- Hourly ETo and ETc calculations  
- Rainfall forecast integration  
- Automatic irrigation scheduling logic  
- Text-based data logging  

---

### 🚀 Future Plans  

- Add **wireless connectivity** (Wi-Fi or LoRa)  
- Create a **Streamlit dashboard** for live data visualization  
- Connecting the code to pumps and pipes to automate the irrigation process.

---

### 🪪 License  
This project is licensed under the **Apache-2.0 License**.  
See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or suggestions, feel free to open an issue or reach out:

- **Email**: [adnanbarwaniwala7@gmail.com](mailto:adnanbarwaniwala7@gmail.com)

## 🙏 Thank You

Thank you for exploring SENSE Irrigation! I hope you find it useful.
