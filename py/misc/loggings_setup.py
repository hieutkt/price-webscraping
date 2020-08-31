#!/usr/bin/env python3
"""Setup logging interface for scrapers"""

import os
import logging
import logging.handlers as handlers
import coloredlogs

def setup_loggings(log_path, site_name):
    """Setting up logging functions"""
    # Setting up logging
    if not os.path.exists(log_path):
        os.makedirs(log_path)
        os.makedirs(log_path + "/aggregated_error/")
    log_format = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p'
    )
    log_writer = logging.FileHandler(log_path + site_name + '.log')
    log_stout = logging.StreamHandler()
    log_error = handlers.TimedRotatingFileHandler(
        log_path + 'aggregated_error/errors.log',
        when='midnight', interval=1)
    log_error.suffix = '%Y-%m-%d_' + site_name

    log_writer.setFormatter(log_format)
    log_stout.setFormatter(log_format)
    log_error.setFormatter(log_format)
    log_error.setLevel("ERROR")

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[log_writer, log_stout, log_error]
    )

    coloredlogs.install()
