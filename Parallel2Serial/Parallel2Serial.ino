/*
 * CONVERTER PARALLEL TO SERIAL (PTZ AUTO 4)
 * Berdasarkan arsitektur firmware Centronics Receiver
 */
 
#include <avr/io.h>
#include <util/delay.h>
 
// --- MAPPING PIN ARDUINO SESUAI DENGAN KABEL DB25 ---
// Jalur Data 8-bit: Pin A0-A5 dan Pin D6-D7 (Port C dan Port D)
#define PAR_STROBE_BIT 3  // Disambung ke Pin D3 (Pin 1 di DB25)
#define PAR_SEL_BIT    1  // Disambung ke Pin D9 (Pin 13 di DB25)
#define PAR_BUSY_BIT   4  // Disambung ke Pin D4 (Pin 11 di DB25)
#define PAR_ACK_BIT    0  // Disambung ke Pin D8 (Pin 10 di DB25)
 
// Fungsi untuk Inisialisasi Serial (Baud Rate)
void uart_init(uint32_t baudrate) {
    const uint32_t divisorFP1024 = (((uint32_t) (1024 / 8) * F_CPU) / baudrate);
    const uint16_t divisor = (divisorFP1024 + 512) / 1024;
    const uint16_t ubrr = divisor - 1;
 
    UBRR0H = ubrr >> 8;
    UBRR0L = ubrr & 0xff;
 
    UCSR0A |= (1 << U2X0); // Double-speed mode
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00); // 8-bit data
    UCSR0B = (1 << RXEN0) | (1 << TXEN0); // Aktifkan RX dan TX
}
 
// Fungsi untuk melempar data per-byte ke Serial Monitor (PC)
void uart_putbyte(uint8_t byte) {
    loop_until_bit_is_set(UCSR0A, UDRE0);
    UDR0 = byte;
}
 
// Fungsi untuk Inisialisasi Pin Paralel
void parport_init(void) {
    // 1. Set pin SEL (Select) sebagai OUTPUT dan set ke LOW
    DDRB |= (1 << PAR_SEL_BIT);
    PORTB &= ~(1 << PAR_SEL_BIT);
   
    // 2. Set pin BUSY sebagai OUTPUT dan set ke LOW
    DDRD |= (1 << PAR_BUSY_BIT);
    PORTD &= ~(1 << PAR_BUSY_BIT);
 
    // 3. Aktifkan resistor Pull-Up di pin STROBE agar sinyal stabil
    PORTD |= (1 << PAR_STROBE_BIT);
 
    // 4. Set pin ACK (Acknowledge) sebagai OUTPUT dan set ke HIGH (Standby)
    DDRB |= (1 << PAR_ACK_BIT);
    PORTB |= (1 << PAR_ACK_BIT);
 
    // 5. Set pin SEL (Select) ke HIGH untuk lapor ke PTZ bahwa alat siap
    PORTB |= (1 << PAR_SEL_BIT);
}
 
void setup() {
    // Set Baud Rate ke 57600 bps untuk ditarik oleh script Python
    uart_init(57600);
   
    // Konfigurasi pin paralel
    parport_init();
}
 
void loop() {
    // 1. Turunkan status BUSY (Tanda Arduino siap menerima data)
    PORTD &= ~(1 << PAR_BUSY_BIT);
   
    // 2. Tahan program di sini sampai PTZ mengirim sinyal STROBE (LOW)
    loop_until_bit_is_clear(PIND, PAR_STROBE_BIT);
   
    // 3. Begitu STROBE masuk, langsung set BUSY ke HIGH agar PTZ tidak menimpa data
    PORTD |= (1 << PAR_BUSY_BIT);
   
    // 4. Tarik data 8-bit paralel dari Pin A0-A5 dan Pin D6-D7
    const uint8_t byte = (PINC & 0x3f) | (PIND & 0xc0);
   
    // 5. Kirim data yang didapat ke Mini PC lewat jalur Serial (USB)
    uart_putbyte(byte);
   
    // 6. Tunggu sampai sinyal STROBE dari PTZ selesai (kembali HIGH)
    loop_until_bit_is_set(PIND, PAR_STROBE_BIT);
 
    // 7. Berikan sinyal ACK (Acknowledge LOW) ke PTZ tanda data sudah sukses diproses
    PORTB &= ~(1 << PAR_ACK_BIT);
    _delay_us(5);  // Standar industri delay ACK selama 5 microsecond
    PORTB |= (1 << PAR_ACK_BIT);
}