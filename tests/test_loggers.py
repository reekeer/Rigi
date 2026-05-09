"""Tests for specialized loggers."""
import logging


def test_ui_logger_exists():
    """Test rigi.ui logger can be created."""
    ui_log = logging.getLogger("rigi.ui")
    assert ui_log is not None
    assert ui_log.name == "rigi.ui"


def test_dev_logger_exists():
    """Test rigi.dev logger can be created."""
    dev_log = logging.getLogger("rigi.dev")
    assert dev_log is not None
    assert dev_log.name == "rigi.dev"


def test_terminal_logger_exists():
    """Test rigi.terminal logger can be created."""
    terminal_log = logging.getLogger("rigi.terminal")
    assert terminal_log is not None
    assert terminal_log.name == "rigi.terminal"


def test_logger_hierarchy():
    """Test logger hierarchy."""
    rigi_log = logging.getLogger("rigi")
    ui_log = logging.getLogger("rigi.ui")
    dev_log = logging.getLogger("rigi.dev")
    
    assert ui_log.parent == rigi_log or ui_log.parent.name == "rigi"
    assert dev_log.parent == rigi_log or dev_log.parent.name == "rigi"


def test_logger_levels():
    """Test logger level setting."""
    logger = logging.getLogger("rigi.test")
    logger.setLevel(logging.DEBUG)
    assert logger.level == logging.DEBUG
    
    logger.setLevel(logging.INFO)
    assert logger.level == logging.INFO


def test_logger_names():
    """Test logger naming convention."""
    loggers = [
        "rigi.ui",
        "rigi.dev",
        "rigi.terminal"
    ]
    
    for name in loggers:
        logger = logging.getLogger(name)
        assert logger.name == name
        assert logger.name.startswith("rigi.")
