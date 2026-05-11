# =========================================================
# DRIVER OLED SSD1306 UNTUK MICROPYTHON
# =========================================================
#
# Kompatibel:
# - ESP32
# - ESP8266
# - Raspberry Pi Pico
# - Board MicroPython lainnya
#
# Interface:
# - I2C
#
# Resolusi yang didukung:
# - 128x64
# - 128x32
# - 64x48
# - 64x32
#
# Fitur:
# - Stabil
# - Kompatibel lintas firmware
# - Ada fallback writevto()
# - Ada validasi parameter
# - Error handling
# - Siap production
#
# =========================================================

from micropython import const
import framebuf


# =========================================================
# KONSTANTA SSD1306
# =========================================================

SET_CONTRAST = const(0x81)

SET_ENTIRE_ON = const(0xA4)

SET_NORM_INV = const(0xA6)

SET_DISP = const(0xAE)

SET_MEM_ADDR = const(0x20)

SET_COL_ADDR = const(0x21)

SET_PAGE_ADDR = const(0x22)

SET_DISP_START_LINE = const(0x40)

SET_SEG_REMAP = const(0xA0)

SET_MUX_RATIO = const(0xA8)

SET_COM_OUT_DIR = const(0xC0)

SET_DISP_OFFSET = const(0xD3)

SET_COM_PIN_CFG = const(0xDA)

SET_DISP_CLK_DIV = const(0xD5)

SET_PRECHARGE = const(0xD9)

SET_VCOM_DESEL = const(0xDB)

SET_CHARGE_PUMP = const(0x8D)


# =========================================================
# CLASS UTAMA SSD1306
# =========================================================

class SSD1306(framebuf.FrameBuffer):

    def __init__(self, width, height):

        # =================================================
        # VALIDASI UKURAN DISPLAY
        # =================================================

        if width <= 0 or height <= 0:
            raise ValueError("Ukuran display tidak valid")

        # Tinggi wajib kelipatan 8
        # karena SSD1306 bekerja per page (8 pixel)
        if height % 8 != 0:
            raise ValueError(
                "Tinggi display harus kelipatan 8"
            )

        self.width = width
        self.height = height

        # Jumlah page
        self.pages = height // 8

        # Buffer framebuffer
        self.buffer = bytearray(
            self.pages * self.width
        )

        # Inisialisasi FrameBuffer
        super().__init__(
            self.buffer,
            self.width,
            self.height,
            framebuf.MONO_VLSB
        )

        # Inisialisasi display
        self.init_display()

    # =====================================================
    # INISIALISASI OLED
    # =====================================================

    def init_display(self):

        # Sequence inisialisasi SSD1306
        commands = (
            SET_DISP | 0x00,          # Display OFF

            SET_MEM_ADDR,
            0x00,                     # Horizontal addressing mode

            SET_DISP_START_LINE | 0x00,

            SET_SEG_REMAP | 0x01,

            SET_MUX_RATIO,
            self.height - 1,

            SET_COM_OUT_DIR | 0x08,

            SET_DISP_OFFSET,
            0x00,

            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,

            SET_DISP_CLK_DIV,
            0x80,

            SET_PRECHARGE,
            0x22,

            SET_VCOM_DESEL,
            0x30,

            # Contrast default aman
            SET_CONTRAST,
            0xCF,

            SET_ENTIRE_ON,

            SET_NORM_INV,

            # Enable internal charge pump
            SET_CHARGE_PUMP,
            0x14,

            # Display ON
            SET_DISP | 0x01,
        )

        # Kirim semua command
        for cmd in commands:
            self.write_cmd(cmd)

        # Bersihkan layar
        self.fill(0)

        # Tampilkan buffer kosong
        self.show()

    # =====================================================
    # MATIKAN DISPLAY
    # =====================================================

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    # =====================================================
    # HIDUPKAN DISPLAY
    # =====================================================

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    # =====================================================
    # ATUR KONTRAS
    # =====================================================

    def contrast(self, contrast):

        # Batasi nilai 0-255
        contrast = max(0, min(255, contrast))

        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    # =====================================================
    # MODE INVERT
    # =====================================================

    def invert(self, invert):
        self.write_cmd(
            SET_NORM_INV | (invert & 1)
        )

    # =====================================================
    # UPDATE BUFFER KE OLED
    # =====================================================

    def show(self):

        x0 = 0
        x1 = self.width - 1

        # Beberapa OLED 64 pixel
        # memiliki offset internal
        if self.width == 64:
            x0 += 32
            x1 += 32

        # Set column address
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)

        # Set page address
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)

        # Kirim framebuffer
        self.write_data(self.buffer)


# =========================================================
# IMPLEMENTASI I2C
# =========================================================

class SSD1306_I2C(SSD1306):

    def __init__(
        self,
        width,
        height,
        i2c,
        addr=0x3C
    ):

        self.i2c = i2c
        self.addr = addr

        # Buffer command kecil
        self.temp = bytearray(2)

        # Digunakan writevto()
        self.write_list = [b"\x40", None]

        # Test koneksi device
        self._check_device()

        # Jalankan parent constructor
        super().__init__(width, height)

    # =====================================================
    # CEK APAKAH OLED TERDETEKSI
    # =====================================================

    def _check_device(self):

        try:
            devices = self.i2c.scan()

        except Exception as e:
            raise OSError(
                "Gagal scan I2C: {}".format(e)
            )

        if self.addr not in devices:
            raise OSError(
                "OLED SSD1306 tidak ditemukan "
                "di alamat 0x{:02X}".format(self.addr)
            )

    # =====================================================
    # KIRIM COMMAND
    # =====================================================

    def write_cmd(self, cmd):

        try:
            self.temp[0] = 0x80
            self.temp[1] = cmd

            self.i2c.writeto(
                self.addr,
                self.temp
            )

        except OSError as e:
            raise OSError(
                "Gagal kirim command OLED: {}".format(e)
            )

    # =====================================================
    # KIRIM DATA FRAMEBUFFER
    # =====================================================

    def write_data(self, buf):

        # =================================================
        # PRIORITAS:
        # writevto() lebih cepat dan hemat RAM
        # =================================================

        try:

            self.write_list[1] = buf

            self.i2c.writevto(
                self.addr,
                self.write_list
            )

        # =================================================
        # FALLBACK:
        # Jika firmware tidak support writevto()
        # =================================================

        except AttributeError:

            try:
                self.i2c.writeto(
                    self.addr,
                    b"\x40" + buf
                )

            except OSError as e:
                raise OSError(
                    "Gagal kirim data OLED: {}".format(e)
                )

        except OSError as e:
            raise OSError(
                "Gagal kirim framebuffer: {}".format(e)
            )


# =========================================================
# CONTOH PENGGUNAAN
# =========================================================
#
# from machine import Pin, I2C
#
# from ssd1306 import SSD1306_I2C
#
# i2c = I2C(
#     0,
#     scl=Pin(22),
#     sda=Pin(21),
#     freq=400000
# )
#
# oled = SSD1306_I2C(
#     128,
#     64,
#     i2c
# )
#
# oled.fill(0)
#
# oled.text("HELLO WORLD", 0, 0)
#
# oled.rect(0, 15, 50, 20, 1)
#
# oled.show()
#
# =========================================================