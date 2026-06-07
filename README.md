# GymPro - Attendance & Management System

GymPro is a desktop gym management app built with Python and Tkinter. It supports member management, attendance, monthly fee tracking, reports, and webcam-based face recognition.

## Requirements

- Python 3.9 or newer
- Windows 10/11
- Webcam for face recognition

## Quick Start on Windows

1. Double-click `install_and_run.bat`.
2. Wait for packages to install the first time.
3. The app launches automatically.

## Manual Install

```bash
pip install -r requirements.txt
python gym_pro.py
```

## Features

- Face recognition attendance
- Manual attendance marking
- SQLite local database
- Member management with photos
- Monthly fees tracking
- Reports and CSV export
- Dashboard with live stats

## Data

The app creates `gymPro.db` in the same folder at runtime. This file contains local member, attendance, fee, and photo data, so it is intentionally ignored by Git.

## Build EXE

Run:

```bat
build_exe_v2.bat
```

The generated executable is created in `dist/`.

## Troubleshooting

- Camera not opening: check if another app is using the camera.
- `face_recognition` or `dlib` install fails: install Visual C++ Build Tools first.
- No face detected: use good lighting and keep the face clearly visible.
