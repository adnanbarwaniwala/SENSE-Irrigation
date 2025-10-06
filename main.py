from functions import *

while True:
    T_sensor, RH_sensor, soil_sensor_raw = read_data_from_metro()

    crop = 'maize'
    soil_type = 'vertisol'
    growth_stage = 'mid'

    water_capacity_of_soil = calculate_water_capacity_of_soil(crop, soil_type)
    soil_water_mm = calculate_soil_water_mm(soil_sensor_raw, water_capacity_of_soil)

    weather_data = get_weather_data_from_open_meteo()
    now = datetime.now()
    eto_mm = calculate_hourly_eto(T_sensor, RH_sensor, now, weather_data)

    kc = returns_kc(crop, growth_stage)
    ETc = calculate_ETc(eto_mm, kc)

    irrigation_dict = hourly_soil_water_update(soil_water_mm, ETc,
                                               weather_data["precipitation"], water_capacity_of_soil)

    print(f"Predicted Soil Water Level: {irrigation_dict['soil_mm_pred']} mm")
    print(f"Predicted Soil Water Level as a % of FC: {irrigation_dict['soil_pct_pred']} %")
    print(f"Irrigation amount: {irrigation_dict['irrigation_mm']} mm")

    with open('irrigation_data.txt', 'a') as f:
        f. write(f"{datetime.now()}, {soil_water_mm}, {irrigation_dict['soil_mm_pred']}, "
                 f"{irrigation_dict['soil_pct_pred']}, {irrigation_dict['irrigation_mm']}\n")

    time.sleep(3600)

