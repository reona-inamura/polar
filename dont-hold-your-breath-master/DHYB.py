from bleak import BleakScanner
import asyncio
import numpy as np
from tqdm import tqdm
import argparse
import plotly.express as px
from PolarH10 import PolarH10
from BreathingAnalyser import BreathingAnalyser

""" DHYB.py
Scan and connect to Polar H10 device
Retrieve basic sensor information including battery level and serial number
- Stream accelerometer data simultaneously with heart rate data
- Alternatively read sample data from a file
"""

async def main(record_len):
    
    devices = await BleakScanner.discover()
    polar_device_found = False
    acc_data = None
    ibi_data = None
    ecg_data = None

    for device in devices:
        if device.name is not None and "Polar" in device.name:
            polar_device_found = True
            polar_device = PolarH10(device)
            await polar_device.connect()
            await polar_device.get_device_info()
            await polar_device.print_device_info()

            #  #にしたところはpmd_streamでまとめてやるため要らなくなった
            #await polar_device.start_acc_stream()
            await polar_device.start_hr_stream()
            #await polar_device.start_ecg_stream()
            await polar_device.start_pmd_stream()

            await asyncio.sleep(polar_device.warmup_time)  # Wait for the stream to start
            polar_device.ibi_stream_values.clear()
            polar_device.ibi_stream_times.clear()        
            polar_device.ecg_stream_times.clear()
            polar_device.ecg_stream_values.clear()
            polar_device.acc_stream_times.clear()
            polar_device.acc_stream_values.clear()            

            for i in tqdm(range(record_len), desc='Recording...'):
                await asyncio.sleep(1)

            #await polar_device.stop_acc_stream()
            await polar_device.stop_hr_stream()
            #await polar_device.stop_ecg_stream()
            await polar_device.stop_pmd_stream()

            acc_data = polar_device.get_acc_data()
            ibi_data = polar_device.get_ibi_data()
            ecg_data = polar_device.get_ecg_data()

            await polar_device.disconnect()
    
    if not polar_device_found:
        print("No Polar device found")

    return [acc_data, ibi_data, ecg_data]

def save_sample_data(acc_data, ibi_data, ecg_data):
    # このまあだとdataフォルダを作成しておく必要がある

    np.savetxt("data/"+paticipant_id+"_data_acc.csv", np.column_stack((acc_data['times'], acc_data['values'], acc_data['timestamp'])), delimiter=",")
    np.savetxt("data/"+paticipant_id+"_data_ibi.csv", np.column_stack((ibi_data['times'], ibi_data['values'], ibi_data['timestamp'])), delimiter=",")
    np.savetxt("data/"+paticipant_id+"_data_ecg.csv", np.column_stack((ecg_data['times'], ecg_data['values'], ecg_data['timestamp'])), delimiter=",")

def load_sample_data():
    sample_acc_data = np.loadtxt("data/sample_data_acc.csv", delimiter=",")
    acc_data = {'times': sample_acc_data[:, 0], 'values': sample_acc_data[:, 1:]}
    sample_ibi_data = np.loadtxt("data/sample_data_ibi.csv", delimiter=",")
    ibi_data = {'times': sample_ibi_data[:, 0], 'values': sample_ibi_data[:, 1]}
    sample_ecg_data = np.loadtxt("data/sample_data_ecg.csv", delimiter=",")
    ecg_data = {'times': sample_ecg_data[:, 0], 'values': sample_ecg_data[:, 1]}
    return acc_data, ibi_data, ecg_data

def get_arguments():
    parser = argparse.ArgumentParser(description="Polar H10 Heart Rate Variability and Breathing Rate Monitor")
    parser.add_argument("--use-sample-data", action="store_true", help="Use sample data loaded from a file")
    parser.add_argument("--record-len", type=int, default=20, help="Length of recording in seconds")
    return parser.parse_args()

if __name__ == "__main__":

    # 参加者IDを指定してデータを保存--------------------------------------------------------------------
    paticipant_id = "timestamp"
    # testは呼吸の影響をみたやつを作ってしまったため、しばらく使わない
    imgfilepass = "img/" + paticipant_id

    args = get_arguments()
    use_sample_data = args.use_sample_data
    record_len = args.record_len

    if use_sample_data:
        acc_data, ibi_data, ecg_data = load_sample_data()


    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        acc_data, ibi_data, ecg_data = loop.run_until_complete(main(record_len))
    
    if acc_data is not None or ibi_data is not None: 
        breathing_analyser = BreathingAnalyser(acc_data, ibi_data, paticipant_id)
        breathing_analyser.show_breathing_signal()
        breathing_analyser.show_heart_rate_variability()
        breathing_analyser.save_breathing_rate()

        if ecg_data is not None:
            # たとえば Plotly でECG可視化

            fig = px.line(x=ecg_data['times'], y=ecg_data['values'],
                        labels={'x':'Time (s)', 'y':'ECG (µV)'},
                        title="ECG Signal")
            fig.write_html(imgfilepass+"ecg.html")
            #fig.show()
        if not use_sample_data:
            response = input("Do you want to save the data? (y/n): ")
            if response.lower() == "y":
                save_sample_data(acc_data, ibi_data, ecg_data)
                print("Data saved")
            else:
                print("Data not saved")
