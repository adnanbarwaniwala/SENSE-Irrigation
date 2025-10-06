from datetime import datetime
import requests
import serial
import refet
import math
import time
import re

LAT = 22.7
LONG = 75.9
ELEV_M = 550           # station elevation [m]  (≈ Indore plateau)


def read_data_from_metro():

    """Reads the sensor values connected to the metro from the serial line.""" ## UNDERSTAND WHAT THE SERIAL LINE IS!!

    # --- configure your port and baudrate ---
    with serial.Serial(port='COM6', baudrate=115200, timeout=1) as ser:
        print("Listening on", ser.port)
        while True:
            if ser.in_waiting: # if there is data waiting
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    if re.match(r'^\s*[-+]?\d+(?:\.\d+)?,\s*[-+]?\d+(?:\.\d+)?,\s*\d+\s*$', line):
                        readings = line.split(', ')
                        break
                else:
                    continue

    print(line)
    temp, humidity, soil_moisture_raw =  float(readings[0]), float(readings[1]), int(readings[2])
    return temp, humidity, soil_moisture_raw


def calculate_water_capacity_of_soil(crop, soil_type):
    """Calculates the max mm of water the soil holds when fully wet / properly irrigated / at 100% capacity."""
    
    # --------------------------------------------------------------------
    # 1. ROOT‑ZONE DEPTH table (mm)
    # --------------------------------------------------------------------
    root_depths = {
        "vertisol": {
            "chickpea": 800, "maize": 1200, "soybean": 1000,
            "wheat": 1100, "dry onion": 400, "green onion": 350
        },
        "alluvial": {
            "chickpea": 600, "maize": 1000, "soybean": 800,
            "wheat": 900,  "dry onion": 300, "green onion": 250
        }
    }

    # Build an "unknown" table by averaging vertisol and alluvial
    root_depths["unknown"] = {
        crop: int((root_depths["vertisol"][crop] + root_depths["alluvial"][crop]) / 2)
        for crop in root_depths["vertisol"]
    }

    # --------------------------------------------------------------------
    # 2. FIELD CAPACITY percent lookup
    # --------------------------------------------------------------------
    field_capacity_percent = {
        "vertisol": 45,
        "alluvial": 35,
        "unknown":  40      # mid‑point default
    }

    # --------------------------------------------------------------------
    # 3. CALCULATIONS
    # --------------------------------------------------------------------
    root_zone_depth_mm = root_depths[soil_type][crop]
    fc_percent         = field_capacity_percent[soil_type]
    water_capacity_of_soil = root_zone_depth_mm * fc_percent / 100.0

    # --------------------------------------------------------------------
    # 4. OUTPUT (debug / user display)
    # --------------------------------------------------------------------
    # print(f"Crop                  : {crop.capitalize()}")
    # print(f"Assumed soil type     : {soil_type.capitalize()}")
    # print(f"Root‑zone depth (mm)  : {root_zone_depth_mm}")
    # print(f"Field capacity (%)    : {fc_percent}")
    # print(f"Water capacity (mm)   : {water_capacity_of_soil:.1f}")

    return water_capacity_of_soil


def calculate_soil_water_mm(soil_sensor_raw: int, water_capacity_of_soil):

    """Converts the raw soil sensor reading into the mm of water the soil currently has."""

    # --- calibration anchors -------------------------------------------------
    RAW_DRY = 65500          # soil sensor reading in dry soil
    RAW_WET = 22000          # soil sensor reading in saturated soil

    saturation_fraction = (RAW_DRY - soil_sensor_raw) / (RAW_DRY - RAW_WET)  # Represents how full the soil is with water, ranging from 0 (completely dry) to 1 (fully saturated based on calibration).
    saturation_fraction = max(0.0, min(1.0, saturation_fraction))  # Ensures the value doesn't go below 0.0 or above 1.0
    soil_water =  saturation_fraction * water_capacity_of_soil
    return soil_water


def get_weather_data_from_open_meteo():

    """
        Fetch Open‑Meteo weather data for the single hour containing target_dt.

        Returns a dict with:
          - 'radiation':  shortwave_radiation  (W/m2)
          - 'wind':       wind_speed_10m       (m/s)
          - 'precipitation':  rain             (mm)
    """

    when = datetime.now()
    timezone = "Asia/Kolkata"

    # 1) Build API request parameters
    date_str = when.date().isoformat()
    params = {
        "latitude": LAT,
        "longitude": LONG,
        "hourly": "shortwave_radiation,wind_speed_10m,precipitation",
        "start_date": date_str,
        "end_date": date_str,
        "timezone": timezone
    }

    # 2) Call the Open‑Meteo REST API
    resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()["hourly"]

    # 3) Figure out which index corresponds to our target hour
    #    The API returns arrays indexed 0 = 00:00–01:00, 1 = 01:00–02:00, etc.
    hour_index = when.hour

    # 4) Extract each value at that index
    radiation = data["shortwave_radiation"][hour_index]
    wind = data["wind_speed_10m"][hour_index]
    precipitation = data["precipitation"][hour_index]

    # 5) Return a clean dict
    return {
        "radiation": radiation,
        "wind_speed": wind,
        "precipitation": precipitation
    }


def calculate_actual_vapor_pressure(temp, humidity):
    """Calculate actual vapour pressure (ea, kPa) from T (°C) & RH (%)"""
    es = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
    return es * humidity / 100.0


def calculate_hourly_eto(temp, humidity, dt, open_meteo_weather_data):
    """
    Return hourly ETo (mm) at datetime `dt`
    using T and RH from your sensor + Open‑Meteo extras.
    """
    # 1) Open‑Meteo radiation and wind speed
    weather = open_meteo_weather_data

    # 2) Convert units for refet.Hourly
    rs_MJ = weather["radiation"] * 0.0036               # W m‑2 → MJ m‑2 h‑1
    u2    = weather["wind_speed"] * 0.748                # 10 m → 2 m (FAO height corr.)
    ea    = calculate_actual_vapor_pressure(temp, humidity)   # kPa

    # 3) ASCE/FAO‑56 hourly ET0
    et0 = refet.Hourly(
        tmean      = temp,
        ea         = ea,
        rs         = rs_MJ,
        uz         = u2,
        zw         = 2,              # we gave wind already at 2 m
        elev       = ELEV_M,
        lat        = LAT,
        lon        = LONG,
        doy        = dt.timetuple().tm_yday,
        time       = dt.hour,        # UTC hour at **start** of period
        method     = 'asce',         # ASCE Penman–Monteith (grass ≈ FAO‑56)
    ).eto()                          # .eto()  for short‑crop ET₀ (grass)

    return float(et0[0])


def returns_kc(crop: str, stage: str) -> float:
    """
    Returns crop-coefficient Kc for a given crop and growth stage.

    Parameters
    ----------
    crop  : str   – chickpea, maize, soybean, wheat, dry onion, green onion
    stage : str   – 'initial', 'development', 'mid', or 'late'
    """

    # --------------------------------------------------------------------
    # Kc look-up table  (values cross-checked against FAO-56 ranges)
    # --------------------------------------------------------------------
    kc_stage = {
        "chickpea": {"initial": 0.54, "development": 0.80, "mid": 0.97, "late": 0.30},
        "maize": {"initial": 0.40, "development": 0.70, "mid": 1.20, "late": 0.50},
        "soybean": {"initial": 0.40, "development": 0.65, "mid": 1.15, "late": 0.70},
        "wheat": {"initial": 0.30, "development": 0.60, "mid": 1.10, "late": 0.80},
        "dry onion": {"initial": 0.50, "development": 0.70, "mid": 1.05, "late": 0.70},
        "green onion": {"initial": 0.50, "development": 0.70, "mid": 1.00, "late": 0.85},
    }
    valid_stages = ("initial", "development", "mid", "late")

    crop = crop.lower().strip()
    stage = stage.lower().strip()

    if crop not in kc_stage:
        raise ValueError(f"Unknown crop '{crop}'. Choose from: {list(kc_stage.keys())}")
    if stage not in valid_stages:
        raise ValueError(f"Stage must be one of {valid_stages}")

    return kc_stage[crop][stage]


def calculate_ETc(ETo, Kc):
    """Returns ETc, which is the evapotranspiration amount adjusted for a specific crop."""
    return ETo * Kc


def hourly_soil_water_update(
        soil_mm_now: float,
        ETc: float,
        rain_mm: float,
        root_zone_capacity_mm: float,
        lower_band: float = 0.60,        # 60 % FC
        upper_band: float = 0.80         # 80 % FC
    ) -> dict:

    """
    Computes the predicted soil-water level at the end of the coming hour
    and decides if irrigation is needed.

    Parameters
    ----------
    soil_mm_now : float
        Current soil water in mm (converted from your probe reading).
    ETc : float
        Crop evapotranspiration for the coming hour (mm).
    rain_mm : float
        Forecast rain for the coming hour (mm).
    root_zone_capacity_mm : float
        Max water the root zone can hold at field capacity (mm).
    lower_band, upper_band : float, optional
        FC thresholds (fractions of capacity) for “too dry” and “refill to”.

    Returns
    -------
    dict  with keys:
        'soil_mm_pred' : predicted soil water for the next hour (mm)
        'soil_pct_pred': same value as a % of the FC (field capacity)
        'irrigation_mm': mm to irrigate (0 if none)
    """

    # 1. Predict new soil level without irrigation
    soil_mm_pred = soil_mm_now + rain_mm - ETc

    # 2. Check against thresholds
    lower_thresh = lower_band * root_zone_capacity_mm
    upper_target = upper_band * root_zone_capacity_mm

    irrigation_mm = 0.0

    if soil_mm_pred < lower_thresh:
        # Need to top-up to the upper band
        irrigation_mm = upper_target - soil_mm_pred
        soil_mm_pred  = upper_target   # what the level will be after irrigation

    # 4. Convert to predicted soil water for the next hour to % of FC.
    soil_pct_pred = (soil_mm_pred / root_zone_capacity_mm) * 100.0

    return {
        "soil_mm_pred" : soil_mm_pred,
        "soil_pct_pred": soil_pct_pred,
        "irrigation_mm": irrigation_mm,
    }



start = time.time()



