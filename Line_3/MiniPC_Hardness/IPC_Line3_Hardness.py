import serial
import serial.tools.list_ports
import time
import socket
import logging

# Tambahkan handler untuk menyimpan log ke file fisik
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("C:\\E-IPC_Line3\\service_hardness.log"),
        logging.StreamHandler()
    ]
)

# Konfigurasi Mini PC Data Acquisition
NODERED_IP = "10.126.15.4"
NODERED_PORT = 5000  # Port TCP yang akan dibuka di Node-RED

def send_to_nodered(data_text):
    """Mengirim string data ke Node-RED melalui TCP Socket"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((NODERED_IP, NODERED_PORT))
            
            # Tambahkan \n di akhir agar Node-RED mudah memisahkan antar pesan
            pesan = f"{data_text}\n"
            s.sendall(pesan.encode('utf-8'))
            
            logging.info(f"[TERKIRIM] -> {NODERED_IP}:{NODERED_PORT}")
            
    except Exception as e:
        logging.error(f"[GAGAL KIRIM] Target {NODERED_IP}:{NODERED_PORT} tidak merespons. Error: {e}")

def find_serial_port():
    """Mencari port serial pertama yang tersedia"""
    ports = list(serial.tools.list_ports.comports())
    if ports:
        return ports[0].device
    return None

def main():
    logging.info("=== SERVICE PENGIRIM DATA RAW HARDNESS BERJALAN ===")
    
    while True:
        port_name = find_serial_port()
        
        # JIKA PORT TIDAK DITEMUKAN (KABEL DICABUT)
        if not port_name:
            logging.warning("Kabel instrumen tidak terdeteksi. Mencari port...")
            time.sleep(3)
            continue

        # JIKA PORT DITEMUKAN (KABEL TERSAMBUNG)
        try:
            ser = serial.Serial(
                port=port_name,
                baudrate=2400,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            logging.info(f"TERHUBUNG ke Instrumen di {port_name} (2400, 7E1)")
            
            while True:
                raw_bytes = ser.readline()
                
                if raw_bytes:
                    data_text = raw_bytes.decode('utf-8', errors='ignore').strip()
                    
                    # Abaikan baris kosong atau baris yang hanya berisi simbol aneh (seperti ♦)
                    if data_text and data_text != "♦":
                        logging.info(f"[RAW IN] {data_text}")
                        send_to_nodered(data_text)
                        
        except serial.SerialException as e:
            # Terpicu saat kabel tiba-tiba dicabut saat sedang membaca data
            logging.error(f"Koneksi instrumen terputus: {e}")
            if 'ser' in locals() and ser.is_open:
                ser.close()
            time.sleep(3) # Tunggu sejenak sebelum kembali ke loop pencarian port

if __name__ == "__main__":
    main()