
# js8call-bbs 📡

** Automated bulletin board and message broadcaster for JS8Call.  Schedule and transmit periodic messages on HF digital modes with a modern, user-friendly interface.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Use Cases](#use-cases)
- [How It Works](#how-it-works)
- [Configuration File](#configuration-file)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Features

- ** Automated Transmission** - Schedule periodic message broadcasts
- ** Flexible Scheduling** - Multiple interval options:
  - Fixed intervals (10 min to 24 hours)
  - Even/odd hours scheduling
- ** Modern Dark Theme GUI** - Easy on the eyes for long operating sessions
- ** Save/Load Configurations** - Store bulletin messages and settings
- ** Auto-start Option** - Start transmissions automatically on launch
- ** Configurable Settings**:
  - Message length limits (70-500+ characters)
  - Custom frequency or auto-detect from JS8Call
  - TCP connection settings
- ** Real-time Monitoring**:
  - Character counter with visual feedback
  - Transmission duration estimates
  - Activity log with timestamps
  - Next transmission countdown
- ** Manual Override** - Send messages immediately when needed
- ** Network Flexibility** - Connect to local or remote JS8Call instances

---

## 📸 Screenshots

Soon ...

---

## 🔧 Requirements

### Software Requirements

- **Python 3.7+** with tkinter support
- **JS8Call** (latest version recommended)
  - Download from: https://js8call.com

### Python Dependencies

**Standard library only** - No external packages required!

- `tkinter` (usually included with Python)
- `json`, `socket`, `threading`, `datetime`, `os` (all standard library)

### Operating Systems

- ✅ **Windows** 10/11
- ✅ **Linux** (Ubuntu, Debian, Fedora, etc.) Soon ...

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/lifreg/js8call-bbs.git
cd js8call-bbs
```

### 2. Verify Python Installation

```bash
python --version  # Should be 3.7 or higher
```

### 3. Configure JS8Call

**Enable TCP Server API in JS8Call:**

1. Open JS8Call
2. Go to **File → Settings**
3. Navigate to **Reporting** tab
4. Check **"Enable TCP Server API"**
5. Note the port (default: **2442**)
6. Click **OK**

### 4. Run js8call-bbs

```bash
python js8_bulletin_autostart.py
```

Or on some systems:

```bash
python3 js8_bulletin_autostart.py
```

---

## ⚙️ Configuration

### First Launch Setup

1. **Launch js8call-bbs** - The application will start with default settings
2. **Open Settings** - Click **⚙️ Settings** or go to **Tools → JS8Call Settings**
3. **Configure Connection**:
   - **IP Address**: `127.0.0.1` (local) or remote IP
   - **Port**: `2442` (JS8Call default)
   - Test connection with **🔍 Test Connection**

4. **Set Frequency** (optional):
   - **Auto mode** (recommended): Uses JS8Call's current frequency
   - **Fixed frequency**: Enter frequency in Hz (e.g., `7078000` for 7.078 MHz)

5. **Auto-start** (optional):
   - Enable **"Start transmissions automatically on launch"**
   - Transmissions will start automatically when you launch the app

---

## Usage

### Creating a Bulletin Message

1. **Type your message** in the text area
2. **Set message length limit**:
   - Choose preset: Short (70), Medium (140), Long (210)
   - Or use **Custom** for custom length
3. **Monitor character count** - Visual feedback shows when approaching limit

### Scheduling Transmissions

**Select transmission interval:**

- **Quick intervals**: 10, 15, 30 minutes
- **Hourly intervals**: 1, 2, 3, 4, 6, 12, 24 hours
- **Time-based**: Even hours only, Odd hours only

### Starting/Stopping

- ** Start Transmissions** - Start automatic broadcasts
- ** Stop** - Stop automatic broadcasts
- ** Send Now** - Send message immediately (manual override)

### Saving Your Work

- ** Save** - Save current message and settings
- ** Save As...** - Save as new file
- ** Open** - Load saved configuration

Files are saved in JSON format with all settings preserved.

---

## Use Cases

### Emergency Communications (EMCOMM)

```
EMCOMM NET - 14.078 MHz
Daily at 1800Z
NCS: W1ABC
Check-ins welcome
```

**Schedule**: Every 24 hours at fixed time


### Net Announcements

```
FRENCH HF NET
Every Sunday 1400Z on 7.078 MHz
All stations welcome - Slow speed
Topic: Emergency preparedness
```

**Schedule**: Odd hours (repeats every 2 hours)

```

**Schedule**: Every 10 minutes

### Club Bulletins

```
RADIO CLUB DE PARIS
Meeting: First Monday 2000 local
New members welcome
Info: www.clubradio.fr
73 de F1ABC
```

**Schedule**: Every 6 hours

---

## How It Works

### Architecture

```
┌─────────────────┐         TCP Socket         ┌──────────────┐
│   js8call-bbs   │ ◄────────────────────────► │   JS8Call    │
│   (Python GUI)  │      Port 2442 (default)   │   (Radio SW) │
└─────────────────┘                            └──────────────┘
         │                                             │
         │                                             │
         ▼                                             ▼
  ┌─────────────┐                              ┌─────────────┐
  │ Config File │                              │  Radio TX   │
  │   (JSON)    │                              │     📻      │
  └─────────────┘                              └─────────────┘
```

### Message Flow

1. **Scheduler** monitors time and triggers transmission when interval elapses
2. **Message validation** checks character limit and content
3. **TCP connection** sends JSON command to JS8Call API
4. **JS8Call** encodes message and transmits via radio
5. **Status updates** displayed in activity log

### JS8Call API Commands

```json
{
  "type": "TX.SEND_MESSAGE",
  "value": "Your message here",
  "params": {
    "FREQ": 0,
    "SPEED": 0
  }
}
```

### Transmission Timing

- **Segment duration**: ~15 seconds per 13 characters
- **210 character message**: ~4 minutes transmission time
- **Automatic scheduling** ensures messages don't overlap

---

## Configuration File

Settings are automatically saved in `js8_bulletin_last.json`:

```json
{
  "message": "Your bulletin message",
  "interval": "15",
  "max_chars": 210,
  "js8_host": "127.0.0.1",
  "js8_port": 2442,
  "js8_frequency": 0,
  "autostart_enabled": false,
  "saved_at": "2025-01-19T14:30:00"
}
```

**Location**: Same directory as the script

---

## Troubleshooting

### JS8Call Connection Issues

**Problem**: "JS8Call: ✗ Not connected"

**Solutions**:
1. Verify JS8Call is running
2. Check TCP Server API is enabled:
   - File → Settings → Reporting → Enable TCP Server API
3. Confirm port number (default 2442)
4. Test with **Reconnect** button
5. Check firewall settings if using remote connection

### Messages Not Transmitting

**Problem**: Messages scheduled but not sending

**Solutions**:
1. Check JS8Call is in RX mode (not currently transmitting)
2. Verify radio is connected and configured
3. Check frequency is valid for your license class
4. Review activity log for error messages
5. Try manual send (**📡 Send Now**) to test

### Character Limit Issues

**Problem**: Message gets truncated

**Solutions**:
1. Check current limit setting (shown at top of text area)
2. Increase limit: Max length → select higher preset or Custom
3. Note: Longer messages = longer transmission time
4. 210 chars ≈ 4 minutes TX time

### Auto-start Not Working

**Problem**: Transmissions don't start automatically

**Solutions**:
1. Check **Settings** → Autostart is enabled
2. Ensure message is loaded and valid
3. Verify JS8Call connection before app launch
4. Check activity log for autostart messages

### Font Display Issues (Linux)

**Problem**: Monospace font not displaying correctly

**Solutions**:
Install recommended fonts:

```bash
# Debian/Ubuntu
sudo apt install fonts-source-code-pro

# Fedora
sudo dnf install source-code-pro-fonts

# Arch
sudo pacman -S adobe-source-code-pro-fonts
```

Then restart js8call-bbs.

---

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Bugs

1. Check existing issues first
2. Create detailed bug report with:
   - Operating system and Python version
   - JS8Call version
   - Steps to reproduce
   - Error messages/logs
   - Screenshots if applicable

### Feature Requests

1. Open an issue with `[Feature Request]` tag
2. Describe the feature and use case
3. Explain why it would be useful

### Pull Requests

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Style

- Follow PEP 8 guidelines
- Add comments for complex logic
- Update README if adding features
- Test on multiple platforms if possible

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**TL;DR**: Free to use, modify, and distribute. Attribution appreciated but not required.

---

## Acknowledgments

### Projects & Developers

- **JS8Call** by KN4CRD - The excellent digital mode software that makes this possible
- **The amateur radio community** - For continuous innovation and knowledge sharing

### Inspiration

- Traditional packet radio bulletin boards
- APRS messaging systems
- Emergency communication needs

### Tools Used

- Python and tkinter for the GUI
- JSON for configuration management
- The power of open source software

---

## 📞 Contact & Support

- **Issues**: https://github.com/lifreg/js8call-bbs/issues
- **Discussions**: https://github.com/lifreg/js8call-bbs/discussions

---

## Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

## Additional Resources

### JS8Call Documentation
- Official website: https://js8call.com
- User manual: http://files.js8call.com/latest.html
- Groups.io forum: https://groups.io/g/js8call

### Amateur Radio Digital Modes
- ARRL Digital Modes: http://www.arrl.org/digital
- Signal Identification Wiki: https://www.sigidwiki.com

### Related Projects
- **Direwolf** - Software TNC for packet radio
- **WSJT-X** - Weak signal digital modes (FT8, FT4, etc.)
- **Fldigi** - Multi-mode digital modem
