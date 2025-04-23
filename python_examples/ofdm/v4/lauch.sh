python3 main.py modulate -i input.txt -o ofdm_signal.bin --binary --modulation QAM16 --subcarriers 1024 --pilot-spacing 64
gcc -o soapy_pluto_sdr_timestamp soapy_pluto_sdr_timestamp.c $(pkg-config --cflags --libs SoapySDR)
sudo ./soapy_pluto_sdr_timestamp > iq.txt
python3 main.py demodulate -i rxdata.pcm -o recovered2.txt --binary --modulation QAM16 --subcarriers 1024 --pilot-spacing 64