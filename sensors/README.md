# Sensors

Python scripts for reading TDS and other sensors via the ADS1115 (I2C).

## Setup

From the project root (parent of this folder):

```bash
source bin/activate   # or: source sensors-env/bin/activate
pip install -r sensors/requirements.txt
```

## Run

**Option A – from project root** (activate venv first):

```bash
source bin/activate
python sensors/read_tds.py
```

**Option B – from this folder** (activate venv from parent, then run):

```bash
source ../bin/activate
python read_tds.py
```

**Option C – run script** (no need to activate manually):

```bash
./run_read_tds.sh
```

Stop with `Ctrl+C`.
