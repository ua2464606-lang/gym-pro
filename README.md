# 💪 GYM PRO — Attendance & Management System

## Requirements
- Python 3.9 or newer  →  https://python.org
- Windows 10/11 (or Linux/Mac with minor adjustments)
- Webcam (for face recognition)

## Quick Start (Windows)
1. Double-click **install_and_run.bat**
2. Wait for packages to install (first time only)
3. App will launch automatically!

## Manual Install
```bash
pip install face_recognition opencv-python pillow numpy
python gym_pro.py
```

## Face Recognition — How It Works
- Uses **dlib** face recognition (99.38% accuracy on LFW benchmark)
- Each member's photo is encoded into a 128-point face vector
- On scan, captured face is compared against ALL stored encodings
- Match threshold: 55% similarity (adjustable in code: `best_dist = 0.55`)
- **Only the closest matching face is selected** — no false matches

## Features
- ✅ Real face recognition (not pixel matching)
- ✅ Manual attendance marking
- ✅ SQLite database (gymPro.db) — permanent storage
- ✅ Member management with photos
- ✅ Monthly fees tracking (Paid/Unpaid)
- ✅ Reports + CSV export
- ✅ Dashboard with live stats

## Data Location
All data stored in: `gymPro.db` (same folder as gym_pro.py)
Back up this file to keep your data safe.

## Troubleshooting
- **Camera not opening**: Check if another app is using the camera
- **face_recognition install fails**: Install Visual C++ Build Tools first
  → https://visualstudio.microsoft.com/visual-cpp-build-tools/
- **No face detected**: Ensure good lighting, face clearly visible in frame
