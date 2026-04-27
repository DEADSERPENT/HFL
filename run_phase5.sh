#!/bin/bash
source ~/HFL/hfl_env/bin/activate
cd ~/HFL/SIMULATORS
python run_phase5.py --steps 5,6,7,8,9,11 2>&1 | tee results/phase5/run_log.txt
