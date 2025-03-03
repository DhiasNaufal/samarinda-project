# samarinda-project

Deteksi sawit

Step Menjalankan Scripts

## Environment Setup

1. Create local virtual environment

```powershell
 python -m venv venv
```

2. Activate virtual environment

```powershell
.\venv\Scripts\activate
```

3. Install Requirement packages

```powershell
pip install -r samarinda.txt
```

## Running The Application

1. Activate virtual environment

```powershell
.\venv\Scripts\activate
```

2. Run the main.py file

```powershell
python main.py
```

## Project Structure

```
src/
├── ui/               # UI and Components/widgets
│   ├── widgets/
├── logic/            # Business logics
│   ├── gee/
├── utils/            # Reusable functions and enums
├── assets/           # Static files
├── main.py           # Application entry point
```