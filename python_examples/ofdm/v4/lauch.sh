python3 main.py modulate -i input.txt -o output.bin --binary --modulation QAM64 --subcarriers 2048 --pilot-spacing 128

python3 main.py demodulate -i output.bin -o recovered.txt --binary --modulation QAM64 --subcarriers 2048 --pilot-spacing 128