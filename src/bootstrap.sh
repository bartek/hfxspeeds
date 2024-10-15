#!/bin/bash


python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip

cat << EOF > requirements.txt
opencv-python==4.10.0.84
google-cloud-storage
google-cloud-videointelligence
numpy
EOF

python -m pip install -r requirements.txt
