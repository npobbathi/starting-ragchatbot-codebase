#!/bin/bash
cd backend
/opt/miniconda3/envs/ragchatbot/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30