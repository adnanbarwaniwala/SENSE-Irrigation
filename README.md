# 🌱 SENSE-Irrigation

**Sensor-driven, hourly irrigation advice for Indore (and anywhere else).**  
A tiny box of sensors + a few lines of Python that think like a weather station and water like a farmer’s best friend.

<p align="left">
  <a href="https://www.python.org/"><img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue.svg"></a>
  <a href="https://www.apache.org/licenses/LICENSE-2.0"><img alt="License" src="https://img.shields.io/badge/License-Apache--2.0-green.svg"></a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey">
</p>

---

## ✨ What it does

Every hour SENSE-Irrigation:

- Reads sensors from a Metro board: **air temperature** & **humidity** (DHT11) and **soil moisture** (YL-69 analog).  
- Fetches forecast for the same hour from **Open-Meteo** (solar radiation, wind, rain, pressure).  
- Computes **ET₀** (reference evapotranspiration) using **ASCE/FAO-56** (via the `refet` Python library).  
- Converts to **ETc** using a **crop coefficient (Kc)** for the crop + growth stage.  
- Updates **soil water balance (mm)** and recommends irrigation **only if** soil is predicted to drop below a safe band (default **60–80% of field capacity**).  
- Appends everything to `irrigation_data.txt`.

**TL;DR:** It measures, predicts, and only waters when needed—by the right amount. 💧

---

## 🧱 Repository layout
