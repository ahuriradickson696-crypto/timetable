"""CLI: start the folder watcher. Usage: py scripts\watch.py"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.core.logging import setup_logging
from app.services.watcher import start_watcher

setup_logging()
start_watcher()