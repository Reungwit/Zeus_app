import pandas as pd
import glob
import os

# 1. กำหนดโฟลเดอร์ที่เก็บไฟล์ (ใส่ '.' ถ้าวางไฟล์ py นี้ไว้ที่เดียวกับข้อมูล)
folder_path = '.' 
all_files = glob.glob(os.path.join(folder_path, "*")) # อ่านทุกไฟล์

# ชื่อ Column ตามลำดับใน Dataset (Mapping ตามที่คุณให้มา)
# ตัดส่วน Log ขยะออก แล้วเริ่มนับที่ Unix Time
column_names = [
    'unix_time', 'timezone', 'datetime', 'station_id', 
    'unk1', 'unk2', 'unk3', 'lat', 'long', 
    'rain', 'temp', 'humidity', 'pressure', 
    'wind_speed', 'wind_dir', 'uv', 
    'co2', 'pm1', 'pm25', 'pm4', 'pm10', 
    'light_r', 'light_g', 'light_b', 'light_ir', 'light_vis'
]

data_list = []

print(f"กำลังค้นหาไฟล์... เจอทั้งหมด {len(all_files)} ไฟล์")

for filename in all_files:
    # ข้ามไฟล์ script ของเราเอง หรือไฟล์ csv ที่อาจจะเคยสร้างไว้
    if filename.endswith('.py') or filename.endswith('.csv'):
        continue
        
    try:
        # เปิดไฟล์มาอ่านทีละบรรทัด เพื่อตัดส่วน Header ขยะทิ้ง
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        cleaned_data = []
        for line in lines:
            # คีย์เวิร์ดคือแยกด้วย '] ' (วงเล็บปิดและเว้นวรรค)
            if '] ' in line:
                # เอาเฉพาะส่วนหลัง ]  คือข้อมูล CSV จริงๆ
                clean_line = line.split('] ')[1].strip()
                cleaned_data.append(clean_line.split(','))
        
        # แปลงเป็น DataFrame
        df = pd.DataFrame(cleaned_data, columns=column_names)
        data_list.append(df)
        print(f"อ่านไฟล์ {filename} สำเร็จ!")
        
    except Exception as e:
        print(f"อ่านไฟล์ {filename} ไม่ได้: {e}")

# รวมทุกไฟล์เป็นก้อนเดียว
if data_list:
    final_df = pd.concat(data_list, ignore_index=True)
    
    # แปลงเวลาให้เป็นมาตรฐาน
    final_df['datetime'] = pd.to_datetime(final_df['datetime'])
    final_df = final_df.sort_values('datetime') # เรียงตามเวลา
    
    # Save เป็น CSV ไฟล์เดียวจบ
    final_df.to_csv("zeus_dataset_combined.csv", index=False)
    print("-----------------------------------")
    print("✅ รวมร่างเสร็จสมบูรณ์! ได้ไฟล์ชื่อ zeus_dataset_combined.csv")
    print(f"ข้อมูลทั้งหมด {len(final_df)} แถว")
else:
    print("❌ ไม่พบข้อมูลที่อ่านได้")