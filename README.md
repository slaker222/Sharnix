


<p align="center">

<img width="917" height="181" alt="logo" src="https://github.com/user-attachments/assets/81444b6c-8db3-4303-a39d-e3de83b87deb" />
<br><br>
</p>

<div align="center">

### Sharnix is a ShareX alternative for Linux. It replicates the functionality of the Windows program ShareX and its basic features: screenshot gallery, OCR, cloud upload, detailed editing, coordinate display, and text addition. It's a good option for screenshots on Linux

<br><br>

<img width="798" height="638" alt="screenshot_1768340031_X929Y420_X1727Y1058" src="https://github.com/user-attachments/assets/5eb5fd09-e4d9-4150-9d3f-522bbfa4ec47" />

</div>


## Download the finished build

👉 **[Download Sharnix](https://github.com/slaker222/Sharnix/releases)**

---
<br><br>

## Building from source code
If you want to build the build manually, follow the instructions below (recommended for better compatibility)

<br>


## Building the application

### 1. Cloning a repository
```bash
git clone https://github.com/slaker222/Sharnix.git
cd sharnix
```

### 2. Installing system dependencies


**Arch Linux:**
```bash
sudo pacman -S python python-pip tk scrot rtl-sdr
```

**Debian / Ubuntu:**
```bash
sudo apt install python3 python3-pip python3-venv tk-dev scrot librtlsdr-dev -y
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip tk-devel scrot rtl-sdr-devel -y
```

### 3. Setting up a virtual environment

```bash
python3 -m venv .venv
```
### For Bash

```bash
source .venv/bin/activate
```

### For Fish

```bash
source .venv/bin/activate.fish
```


### 4. Installing Python packages

```bash
pip install pillow requests pynput pyscreenshot pyinstaller
```

## Building an executable file

```bash
pyinstaller --onefile --windowed --noconsole --clean --noupx \
--add-data "$PWD/ico.png:." \
--icon="$PWD/ico.png" \
--hidden-import=pyscreenshot \
--hidden-import=tkinter \
--hidden-import=PIL \
--hidden-import=PIL.ImageTk \
--hidden-import=PIL.ImageDraw \
--hidden-import=PIL.ImageFilter \
--hidden-import=PIL.ImageOps \
--hidden-import=PIL.ImageFont \
--hidden-import=PIL._tkinter_finder \
--hidden-import=PIL._imagingtk \
--hidden-import=pynput \
--hidden-import=pynput.keyboard \
--hidden-import=requests \
--name Sharnix sharnix.py
```

## Launch

```bash
chmod +x dist/Sharnix
dist/Sharnix
