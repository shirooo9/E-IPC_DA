import os
import time
import socket
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- KONFIGURASI ---
WATCH_DIR = r"C:\E-IPC_Line3\batch_records"
ARCHIVE_DIR = os.path.join(WATCH_DIR, "archive")
NODERED_IP = "10.126.15.4" # IP Mini PC
NODERED_PORT = 5000        # Port TCP In

# Fitur Logging Fisik 
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("C:\\E-IPC_Line3\\service_hardness.log"),
        logging.StreamHandler()
    ]
)

if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)

def send_to_nodered(content, filename):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((NODERED_IP, NODERED_PORT))
            s.sendall(content.encode('utf-8'))
            logging.info(f"[TERKIRIM] File {filename} ke {NODERED_IP}:{NODERED_PORT}")
            return True
    except Exception as e:
        logging.error(f"[GAGAL KIRIM] Target {NODERED_IP}:{NODERED_PORT} tidak merespons. Error: {e}")
        return False

class PTBHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            time.sleep(2)  # Tunggu PDFCreator selesai menulis file
            filename = os.path.basename(event.src_path)
            logging.info(f"[FILE BARU] Terdeteksi: {filename}")
            
            try:
                with open(event.src_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if content.strip():
                    success = send_to_nodered(content, filename)
                    
                    if success:
                        shutil.move(event.src_path, os.path.join(ARCHIVE_DIR, filename))
                        logging.info(f"[DIAMANKAN] {filename} dipindah ke Archive.\n")
                
            except Exception as e:
                logging.error(f"[ERROR] Gagal memproses file {filename}: {e}")

if __name__ == "__main__":
    logging.info(f"=== SERVICE HARDNESS WATCHER BERJALAN DI {WATCH_DIR} ===")
    observer = Observer()
    observer.schedule(PTBHandler(), WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()