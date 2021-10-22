#include <iostream>
#include <fstream>
#include <thread>
#include <vector>
#include <string>
#include <bitset>
#include "CRC.h"

struct load_params {
    int value;
    float load_ratio;
};

/**
 * BFSK default parameters
 */
#define HIGH_FREQ 400000
#define LOW_FREQ 200000
#define BFSK_FREQ 1
#define LOAD_FACTOR 0.5

/**
 * Returns the current time since epoch time in microseconds.
 * @return microseconds since UNIX epoch
 */
int get_time() {
    return std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
}

/**
 * Occupies the current CPU core it is running on with an infinite loop.
 * @param Duration for which the core is loaded
 */
void busy_wait(double duration_micros) {
    auto current_time = get_time();
    while (current_time + duration_micros > get_time()) {}
}

/**
 * Occupies the specified CPU core so that it switches between load and idle at a certain frequency.
 * @param params: the frequency at which the core shall be switched + the desired load ratio
 */
void *generate_frequency_on_core(void *params) {
    busy_wait(1000000 / (((struct load_params *) params)->load_ratio * ((struct load_params *) params)->value));
    std::this_thread::sleep_for(std::chrono::microseconds(
            (int) (1000000 / (((struct load_params *) params)->load_ratio * ((struct load_params *) params)->value))));
    return nullptr;
}

/**
 * Creates a number of worker threads equal to the number of logical cores, and binds each worker to exactly one of them. Each worker executes generate_frequency_on_core().
 * @param p_load_params: the frequency at which the CPU shall be switched
 */
void generate_frequency_on_all_cores(void *p_load_params) {
    const auto processor_count = std::thread::hardware_concurrency();
    pthread_t threads[processor_count];
    pthread_attr_t attr;
    cpu_set_t cpus;
    pthread_attr_init(&attr);

    for (auto i = 0; i < processor_count; i++) {
        CPU_ZERO(&cpus);
        CPU_SET(i, &cpus);
        pthread_attr_setaffinity_np(&attr, sizeof(cpu_set_t), &cpus);
        pthread_create(&threads[i], &attr, generate_frequency_on_core, p_load_params);
    }

    for (auto i = 0; i < processor_count; i++) {
        pthread_join(threads[i], nullptr);
    }
}

/**
 * Generates a signal using generate_frequency_on_all_cores().
 * @param duration_micros: Desired duration of the signal in microseconds
 * @param freq: CPU swtiching frequency
 * @param load_ratio: Ratio between loading time and idle time while loading CPU
 */
void generate_signal(long long duration_micros, int freq, float load_ratio = 0.5) {
    auto *p_load_params = (struct load_params *) malloc(sizeof(struct load_params));
    p_load_params->value = freq;
    p_load_params->load_ratio = load_ratio;
    auto start = get_time();
    while (start + duration_micros > get_time())
        generate_frequency_on_all_cores((void *) p_load_params);
    free(p_load_params);
}

/**
 * Generates a sweep signal, which can then be analyzed to determine the spectrum in which data can be transmitted.
 * @param duration_micros: Duration of each generated frequency
 * @param max_freq: Maximum switching frequency which shall be reached at the end of the sweep signal
 * @param inc: Increase in Hz from frequency(n) to frequency(n+1)
 * @param load_ratio: Ratio between loading time and idle time while loading CPU
 */
void generate_sweep_signal(int duration_micros = 5000, int max_freq = 500000, int inc = 100, float load_ratio = 0.5) {
    auto frequency_amount = (max_freq / inc);
    std::cout << "Generating sweep signal." << std::endl << "Approximate duration: "
              << duration_micros * frequency_amount / 1000000
              << " seconds" << std::endl << "Distinct frequencies: " << frequency_amount << std::endl;
    auto start = (int) get_time() / 1000;
    for (auto i = 1; i < max_freq; i += inc) {
        generate_signal(duration_micros, i, load_ratio);
    }
    // show elapsed time
    std::cout << "Sweep signal lasted " << (get_time() / 1000 - start) / 1000.0 << " seconds." << std::endl;
}

/**
 * Generates a BFSK signal.
 * @param data_string: The data to be transferred, in binary format
 * @param high_freq: The switching frequency used to encode 1s
 * @param low_freq: The switching frequency used to encode 0s
 * @param bfsk_freq: Frequency at which symbols shall be transmitted
 * @param load_ratio: Ratio between loading time and idle time while loading CPU
 */
void generate_bfsk_signal(const std::string &data_string, int high_freq = 200000, int low_freq = 100000, float bfsk_freq = 1,
                          float load_ratio = 0.5) {
    std::cout << "Generating BFSK signal for data: " << data_string << std::endl;
    std::cout << "Estimated duration: " << data_string.length() * (1.0 / bfsk_freq) << " seconds" << std::endl;
    for (char c : data_string) {
        if (c == '1')
            generate_signal(1000000.0 / bfsk_freq, high_freq, load_ratio);
        if (c == '0')
            generate_signal(1000000.0 / bfsk_freq, low_freq, load_ratio);
    }
}

/**
 * Generates a CRC (CRC-8/SMBUS).
 * @param content: payload which we should CRC
 */
void generate_crc(const std::string &content){
    std::cout << "\n---CRC START---" << std::endl;
    std::uint32_t crc = CRC::Calculate(content.c_str(), sizeof(content.c_str()), CRC::CRC_8());
    generate_bfsk_signal(std::bitset<8>(crc).to_string(), HIGH_FREQ, LOW_FREQ, BFSK_FREQ, LOAD_FACTOR);
    std::cout << "---CRC END---" << std::endl;
}

/**
 * Reads a file, transforms the contents into ASCII bytes.
 * @param file_name: Name / location of the file which is to be transmitted
 */
void generate_signal_from_file(const std::string &file_name) {
    std::cout << "\n---PAYLOAD TRANSMISSION START---" << std::endl;
    std::cout << "Transmitting bytes from file: " << file_name << std::endl;
    std::string crc_content;
    // read from file and transmit
    std::ifstream content(file_name);
    if (content.is_open()) {
        std::string line;
        while (content >> line) {
            for (std::size_t i = 0; i < line.size(); ++i)
            {
                crc_content += line;
                std::bitset<8> bits = std::bitset<8>(line.c_str()[i]);
                generate_bfsk_signal(bits.to_string(), HIGH_FREQ, LOW_FREQ, BFSK_FREQ, LOAD_FACTOR);
            }
            generate_bfsk_signal(std::bitset<8>('\n').to_string(), HIGH_FREQ, LOW_FREQ, BFSK_FREQ, LOAD_FACTOR);
            crc_content += '\n';
        }
    }

    content.close();
    std::cout << "---PAYLOAD TRANSMISSION END---" << std::endl;
    // computing CRC
    generate_crc(crc_content);
}

/**
 * Generates a static 10101010 preamble.
 */
void generate_preamble() {
    std::cout << "---PREAMBLE START---" << std::endl;
    generate_bfsk_signal("10101010", HIGH_FREQ, LOW_FREQ, BFSK_FREQ, LOAD_FACTOR);
    std::cout << "---PREAMBLE END---" << std::endl;
}

int main() {
    generate_preamble();
    generate_signal_from_file("test.txt");
}
