#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 ЛАГІРАВАННЕ ПАДЗЕЙ
"""

import logging
from datetime import datetime
from pathlib import Path

def setup_logger(name):
    """Наладжванне логера"""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    log_file = log_dir / f"{datetime.now().strftime('%Y%m')}.log"
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger('belarus-etalon')
