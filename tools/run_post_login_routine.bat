@echo off
setlocal
cd /d "%~dp0\.."
python tools\run_post_login_routine.py --account Acc_1
