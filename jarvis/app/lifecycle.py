"""
JARVIS Application Lifecycle Manager
Central orchestrator managing HUD states, tray, hotkeys, audio sessions, routing, and history logging.
"""

import sys
import threading
import time
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot, QTimer
import numpy as np

from jarvis.app.config import config
from jarvis.app.hotkey_manager import GlobalHotkeyManager
from jarvis.ui.notch import VoiceOSNotch
from jarvis.ui.history_sidebar import HistorySidebar
from jarvis.ui.tray import SystemTray
from jarvis.ui.settings import SettingsDialog
from jarvis.voice.microphone import MicrophoneRecorder
from jarvis.voice.speech_to_text import get_stt_provider
from jarvis.voice.text_to_speech import tts_engine
from jarvis.intelligence.router import CommandRouter
from jarvis.storage.history_repository import HistoryRepository


class LifecycleManager(QObject):
    # Cross-thread GUI signals
    sig_set_state = Signal(str, str)
    sig_set_energy = Signal(float)
    sig_show_action = Signal(str, str, str, bool)
    sig_toggle_history = Signal()
    sig_open_settings = Signal()
    sig_popup = Signal()
    sig_disappear = Signal()
    sig_action_step = Signal(str, str, bool)
    sig_clear_pipeline = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.router = CommandRouter()
        self.history_repo = HistoryRepository()
        self.stt_provider = get_stt_provider()

        # UI Components
        self.notch = VoiceOSNotch()
        self.sidebar = HistorySidebar(self.history_repo)
        self.tray = SystemTray()
        self.settings_dialog = SettingsDialog()

        # Recorder
        self.recorder = MicrophoneRecorder(
            energy_callback=self._on_audio_energy,
            finished_callback=self._on_speech_finished,
        )

        # Hotkeys
        self.hotkeys = GlobalHotkeyManager(
            on_press=self.on_hotkey_down,
            on_release=self.on_hotkey_up,
            on_activate=self.toggle_session,
            on_history=self.toggle_history,
        )

        self._current_transcript = ""
        self._pending_confirmation = False
        self._pending_intent = None

        self._connect_signals()

    def _connect_signals(self):
        # GUI Signal connections
        self.sig_set_state.connect(self.notch.set_state)
        self.sig_set_energy.connect(self.notch.update_energy)
        self.sig_show_action.connect(self.notch.show_action_preview)
        self.sig_toggle_history.connect(self.sidebar.toggle)
        self.sig_open_settings.connect(self.settings_dialog.show)
        self.sig_popup.connect(self.notch.pop_up)
        self.sig_disappear.connect(self.notch.disappear)
        self.sig_action_step.connect(self.notch.add_pipeline_step)
        self.sig_clear_pipeline.connect(self.notch.clear_pipeline)

        # Notch signals
        self.notch.clicked.connect(self.toggle_session)
        self.notch.confirmed.connect(self._on_action_confirmed)
        self.notch.cancelled.connect(self._on_action_cancelled)
        self.notch.close_requested.connect(self.dismiss_notch)

        # Tray signals
        self.tray.activate_requested.connect(self.toggle_session)
        self.tray.history_requested.connect(self.toggle_history)
        self.tray.settings_requested.connect(self.open_settings)
        self.tray.mode_toggled.connect(self.notch.set_mode)
        self.tray.exit_requested.connect(self.shutdown)
        self.tray.restart_requested.connect(self.restart)

        # Sidebar signals
        self.sidebar.run_again_requested.connect(self.execute_command_text)

        # Settings signals
        self.settings_dialog.settings_saved.connect(self._on_settings_reloaded)

    def start(self):
        """Starts background workers, tray icon, and global hotkeys."""
        self.tray.show()
        # Keep Notch hidden until Ctrl+Alt is pressed or clicked
        self.notch.hide()
        self.notch.set_state("IDLE", "Ready • Hold Ctrl+Alt to speak")
        self.notch.set_mode(config.get("active_mode", "agent"))
        self.hotkeys.start()
        print("[Lifecycle] JARVIS VoiceOS operational (Notch HUD hidden, waiting for Ctrl+Alt).")

    def shutdown(self):
        print("[Lifecycle] Shutting down JARVIS...")
        self.hotkeys.stop()
        self.recorder.stop_listening()
        tts_engine.stop()
        self.tray.hide()
        self.notch.close()
        self.sidebar.close()
        sys.exit(0)

    def restart(self):
        self.hotkeys.stop()
        self.recorder.stop_listening()
        tts_engine.stop()
        import os
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # === Interaction Lifecycle ===

    def on_hotkey_down(self):
        """Called as soon as Ctrl+Alt is pressed down (Push-to-Talk start)."""
        if tts_engine.is_speaking():
            tts_engine.stop()

        if not self.recorder.is_recording:
            self._pending_confirmation = False
            self.sig_popup.emit()
            self.sig_set_state.emit("LISTENING", "Listening...")
            self.recorder.start_listening()

    def on_hotkey_up(self, duration: float):
        """Called as soon as Ctrl+Alt is released (Push-to-Talk end)."""
        if duration >= 0.25:
            if self.recorder.is_recording:
                print(f"[Lifecycle] Hold-to-talk released ({duration:.2f}s). Processing speech...")
                self.sig_set_state.emit("PROCESSING", "Analyzing speech...")
                self.recorder.stop_listening()
        else:
            print(f"[Lifecycle] Hotkey tap detected ({duration:.2f}s). Keeping listener active...")

    @Slot()
    def dismiss_notch(self):
        """Immediately silences speech, cancels recording, and smoothly dismisses the notch."""
        tts_engine.stop()
        if self.recorder.is_recording:
            self.recorder.stop_listening()
        self.sig_disappear.emit()
        self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak")

    @Slot()
    def toggle_session(self):
        """Called when user clicks the orb or tray icon."""
        # If TTS is speaking, pause the voice, but KEEP the notch visible so the user can read!
        if tts_engine.is_speaking():
            tts_engine.stop()
            self.sig_set_state.emit("IDLE", "Speech paused.")
            return

        # If currently analyzing or executing an action, ignore clicks to prevent conflicting sessions
        if self.notch._state in ["PROCESSING", "EXECUTING"]:
            return

        if self.recorder.is_recording:
            # Clicked while listening: stop listening and execute immediately!
            print("[Lifecycle] Clicked while listening -> Stopping mic and executing speech...")
            self.sig_set_state.emit("PROCESSING", "Analyzing speech...")
            self.recorder.stop_listening()
        else:
            # Start listening session: pop up the notch HUD immediately!
            self._pending_confirmation = False
            self.sig_popup.emit()
            self.sig_set_state.emit("LISTENING", "Listening...")
            self.recorder.start_listening()

    @Slot()
    def toggle_history(self):
        self.sig_toggle_history.emit()

    @Slot()
    def open_settings(self):
        self.sig_open_settings.emit()

    def _on_settings_reloaded(self):
        self.stt_provider = get_stt_provider()
        self.notch.set_mode(config.get("active_mode", "agent"))

    def _on_audio_energy(self, energy: float):
        self.sig_set_energy.emit(energy)

    def _on_speech_finished(self, audio_data: np.ndarray):
        """Called asynchronously when user finishes speaking (VAD silence detected)."""
        self.sig_set_state.emit("PROCESSING", "Transcribing speech...")

        def _worker():
            # 1. Speech to Text
            try:
                transcript = self.stt_provider.transcribe(audio_data)
            except Exception as e:
                print(f"[Lifecycle] STT failed: {e}")
                transcript = ""

            if not transcript or not transcript.strip():
                self.sig_set_state.emit("IDLE", "I couldn't hear you.")
                time.sleep(1.2)
                self.sig_disappear.emit()
                self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak")
                return

            self._current_transcript = transcript
            self.execute_command_text(transcript)

        threading.Thread(target=_worker, daemon=True).start()

    def execute_command_text(self, transcript: str):
        """Processes and executes a command string through the router."""
        self.sig_set_state.emit("PROCESSING", f"'{transcript}'")
        self.sig_clear_pipeline.emit()

        def _worker():
            intent, result = self.router.route_and_execute(transcript)

            # Check if confirmation is required
            if result.requires_confirmation:
                self._pending_confirmation = True
                self._pending_intent = intent
                self.sig_show_action.emit(
                    intent.target or "Safety Guard",
                    result.confirmation_prompt or result.message,
                    "⚠️",
                    True,
                )
                self.sig_set_state.emit("CONFIRMATION_REQUIRED", result.message)
                tts_engine.speak(result.message)
                return

            self._process_result(intent, result, transcript)

        threading.Thread(target=_worker, daemon=True).start()

    def _process_result(self, intent, result, transcript: str):
        status_text = result.message

        # Multi-step pipeline tracking
        if result.next_steps:
            self.sig_set_state.emit("EXECUTING", "Performing action sequence...")
            self.sig_action_step.emit(f"Step 1: {intent.action}", "⚡", True)
            
            step_count = 1
            for next_step in result.next_steps:
                step_count += 1
                self.sig_action_step.emit(f"Step {step_count}: {next_step}", "⚡", False)
                time.sleep(1.0) # simulate processing step
                self.sig_action_step.emit(f"Step {step_count}: {next_step}", "⚡", True)

            self.sig_set_state.emit("SPEAKING", status_text)
            if result.is_success():
                self.sig_set_state.emit("SPEAKING", status_text)
            else:
                self.sig_set_state.emit("ERROR", status_text)

        # Feed turn into Chat Composer Thread
        try:
            self.sidebar.add_chat_turn(transcript, status_text)
        except Exception as e:
            print(f"[Lifecycle] Failed to add chat turn: {e}")

        # Log to persistent SQLite history
        if config.get("save_history", True):
            self.history_repo.log_interaction(
                command_text=transcript,
                response_text=status_text,
                tool=str(intent.category.value),
                action=intent.action,
                params=intent.params,
                status=result.status,
                result_summary=status_text,
            )

        # Spoken response with barge-in support and auto-disappear upon completion
        def on_tts_finish():
            # Keep notch visible for 2.5s after audio finishes so user can read the response
            time.sleep(2.5)
            if not tts_engine.is_speaking() and not self.recorder.is_recording:
                self.sig_disappear.emit()
                self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak")

        tts_engine.speak(status_text, on_finish=on_tts_finish)

    def _on_action_confirmed(self):
        if self._pending_intent:
            intent = self._pending_intent
            self._pending_confirmation = False
            self._pending_intent = None
            intent.params["confirmed"] = True

            self.sig_set_state.emit("EXECUTING", "Executing confirmed action...")
            threading.Thread(
                target=lambda: self._execute_confirmed(intent), daemon=True
            ).start()

    def _execute_confirmed(self, intent):
        result = self.router._dispatch_tool(intent)
        self._process_result(intent, result, str(intent.action))

    def _on_action_cancelled(self):
        self._pending_confirmation = False
        self._pending_intent = None
        self.sig_set_state.emit("IDLE", "Action cancelled.")
        QTimer.singleShot(1000, self.sig_disappear.emit)
        QTimer.singleShot(1200, lambda: self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak"))
