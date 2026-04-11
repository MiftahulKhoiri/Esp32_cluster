import numpy as np
import tensorflow as tf
import os
from datetime import datetime

MODEL_FILE = "model.tflite"  # Nama default, bisa tetap dipakai untuk load prediksi
custom_X = None
custom_y = None

def get_training_data():
    """Mengembalikan data pelatihan (custom jika tersedia, else default)."""
    if custom_X is not None and custom_y is not None:
        return custom_X, custom_y
    else:
        X = np.array([20, 22, 24, 26, 28, 30, 32, 34], dtype=np.float32)
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1], dtype=np.float32)
        return X, y

def input_custom_data():
    """Meminta pengguna memasukkan data suhu dan label secara manual."""
    global custom_X, custom_y
    print("\n--- Input Data Custom ---")
    print("Masukkan data pelatihan. Label: 0 = AC mati, 1 = AC menyala.")
    
    while True:
        try:
            n = int(input("Berapa jumlah data yang ingin dimasukkan? "))
            if n <= 0:
                print("Jumlah data harus lebih dari 0.")
                continue
            break
        except ValueError:
            print("Harap masukkan angka bulat.")
    
    X_list = []
    y_list = []
    for i in range(n):
        print(f"\nData ke-{i+1}:")
        while True:
            try:
                suhu = float(input("  Suhu (Celcius): "))
                break
            except ValueError:
                print("  Harap masukkan angka (desimal diperbolehkan).")
        while True:
            label_input = input("  Label (0 atau 1): ").strip()
            if label_input in ['0', '1']:
                label = int(label_input)
                break
            else:
                print("  Label harus 0 atau 1.")
        X_list.append(suhu)
        y_list.append(label)
    
    custom_X = np.array(X_list, dtype=np.float32)
    custom_y = np.array(y_list, dtype=np.float32)
    print(f"\nData custom berhasil disimpan: {n} sampel.")

def train_model():
    """Melatih model AI sederhana menggunakan data yang tersedia."""
    print("\n--- Melatih Model ---")
    X, y = get_training_data()
    
    print("Data pelatihan yang digunakan:")
    for suhu, label in zip(X, y):
        print(f"  Suhu: {suhu:5.1f}°C -> Label: {int(label)}")
    
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(1, input_shape=(1,), activation="sigmoid")
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy")
    
    print("Mulai pelatihan...")
    model.fit(X, y, epochs=200, verbose=0)
    print("Pelatihan selesai!")
    return model

def save_tflite_auto(model):
    """
    Menyimpan model TensorFlow Lite dengan nama otomatis berbasis timestamp.
    Format: model_YYYYMMDD_HHMMSS.tflite
    Tidak akan menimpa file yang sudah ada.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"model_{timestamp}.tflite"
    
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(filename, "wb") as f:
        f.write(tflite_model)
    print(f"Model berhasil disimpan sebagai '{filename}'")
    return filename

def save_tflite_manual(model):
    """Menyimpan model dengan nama file dari input pengguna."""
    filename = input("Masukkan nama file (tanpa ekstensi, contoh: ac_model_v2): ").strip()
    if not filename:
        print("Nama file tidak boleh kosong. Menggunakan nama otomatis.")
        return save_tflite_auto(model)
    if not filename.endswith('.tflite'):
        filename += '.tflite'
    
    # Konfirmasi jika file sudah ada
    if os.path.exists(filename):
        konfirmasi = input(f"File '{filename}' sudah ada. Timpa? (y/n): ").strip().lower()
        if konfirmasi != 'y':
            print("Penyimpanan dibatalkan.")
            return None
    
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(filename, "wb") as f:
        f.write(tflite_model)
    print(f"Model berhasil disimpan sebagai '{filename}'")
    return filename

def load_tflite(filename=None):
    """Memuat model TensorFlow Lite dari file."""
    if filename is None:
        # Cari file .tflite terbaru di direktori saat ini
        tflite_files = [f for f in os.listdir('.') if f.endswith('.tflite')]
        if not tflite_files:
            print("Tidak ada file .tflite ditemukan.")
            return None
        # Pilih file terbaru berdasarkan waktu modifikasi
        filename = max(tflite_files, key=os.path.getmtime)
        print(f"Menggunakan file terbaru: '{filename}'")
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None
    
    interpreter = tf.lite.Interpreter(model_path=filename)
    interpreter.allocate_tensors()
    return interpreter

def predict_with_tflite(interpreter, suhu):
    """Melakukan prediksi menggunakan model TFLite."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    input_data = np.array([[suhu]], dtype=np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    return output[0][0]

def predict_menu(model=None):
    """Menu untuk melakukan prediksi berdasarkan input pengguna."""
    print("\n--- Prediksi AC Menyala/Mati ---")
    
    # Cari file .tflite yang tersedia
    tflite_files = [f for f in os.listdir('.') if f.endswith('.tflite')]
    use_tflite = False
    interpreter = None
    
    if tflite_files:
        print("File model TFLite ditemukan:")
        for i, f in enumerate(tflite_files, 1):
            print(f"  {i}. {f}")
        pilih = input("Pilih nomor file (Enter untuk gunakan terbaru, 'keras' untuk model di memori): ").strip()
        
        if pilih.lower() == 'keras':
            use_tflite = False
        else:
            use_tflite = True
            if pilih.isdigit() and 1 <= int(pilih) <= len(tflite_files):
                filename = tflite_files[int(pilih)-1]
            else:
                filename = max(tflite_files, key=os.path.getmtime)
                print(f"Menggunakan file terbaru: '{filename}'")
            interpreter = load_tflite(filename)
            if interpreter is None:
                return
    else:
        print("Tidak ada file .tflite. Menggunakan model Keras di memori (jika tersedia).")
        use_tflite = False
    
    if not use_tflite and model is None:
        print("Model belum dilatih. Silakan latih model terlebih dahulu (pilih opsi 1).")
        return
    
    while True:
        try:
            suhu_input = input("Masukkan suhu (dalam Celcius) atau ketik 'menu' untuk kembali: ")
            if suhu_input.lower() == 'menu':
                break
            suhu = float(suhu_input)
            
            if use_tflite:
                prob = predict_with_tflite(interpreter, suhu)
            else:
                prob = model.predict(np.array([[suhu]], dtype=np.float32), verbose=0)[0][0]
            
            prediksi = 1 if prob >= 0.5 else 0
            status = "MENYALA" if prediksi == 1 else "MATI"
            print(f"Suhu: {suhu}°C → Probabilitas AC menyala: {prob:.4f} → AC {status}")
        except ValueError:
            print("Input tidak valid. Harap masukkan angka.")

def show_data_status():
    """Menampilkan status data pelatihan saat ini."""
    if custom_X is not None:
        print("Data pelatihan saat ini: CUSTOM")
    else:
        print("Data pelatihan saat ini: DEFAULT")

def main():
    global custom_X, custom_y
    model = None
    print("=" * 50)
    print("SISTEM PREDIKSI AC BERDASARKAN SUHU (TinyML)")
    print("=" * 50)
    
    while True:
        print("\n--- Menu Utama ---")
        show_data_status()
        print("1. Latih model")
        print("2. Input data custom (ganti data default)")
        print("3. Kembalikan ke data default")
        print("4. Prediksi (berdasarkan input suhu)")
        print("5. Simpan model ke file TensorFlow Lite")
        print("6. Keluar")
        
        pilihan = input("Pilih opsi (1-6): ").strip()
        
        if pilihan == "1":
            model = train_model()
        elif pilihan == "2":
            input_custom_data()
        elif pilihan == "3":
            custom_X = None
            custom_y = None
            print("Data dikembalikan ke default.")
        elif pilihan == "4":
            predict_menu(model)
        elif pilihan == "5":
            if model is None:
                print("Model belum dilatih. Latih model terlebih dahulu (opsi 1).")
            else:
                print("\nPilih mode penyimpanan:")
                print("  1. Otomatis (nama dengan timestamp)")
                print("  2. Manual (masukkan nama sendiri)")
                sub_pilihan = input("Pilih (1/2): ").strip()
                if sub_pilihan == "1":
                    save_tflite_auto(model)
                elif sub_pilihan == "2":
                    save_tflite_manual(model)
                else:
                    print("Pilihan tidak valid. Menggunakan mode otomatis.")
                    save_tflite_auto(model)
        elif pilihan == "6":
            print("Keluar dari program. Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")

if __name__ == "__main__":
    main()