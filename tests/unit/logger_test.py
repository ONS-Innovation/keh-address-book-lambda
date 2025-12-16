from logger import wrapped_logging

class TestWrappedLogging:

    def test_log_info(self, caplog):
        logger = wrapped_logging(debug=False)
        logger.log_info("Info message")
        assert "Info message" in caplog.text

    def test_log_error(self, caplog):
        logger = wrapped_logging(debug=False)
        logger.log_error("Error message")
        assert "Error message" in caplog.text

    def test_log_warning(self, caplog):
        logger = wrapped_logging(debug=False)
        logger.log_warning("Warning message")
        assert "Warning message" in caplog.text

    def test_debug_log(self, caplog):
        logger = wrapped_logging(debug=True)
        logger.log_info("Info message")
        logger.log_error("Error message")
        logger.log_warning("Warning message")
        assert "Info message" in caplog.text
        assert "Error message" in caplog.text
        assert "Warning message" in caplog.text