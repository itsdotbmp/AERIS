import core.main as main
from core.main import log_info, log_error
import os
from views.config_editor import config_summary_view

def _config_editor_flow(stdscr):
    config_edits = config_summary_view(stdscr, main.config)


