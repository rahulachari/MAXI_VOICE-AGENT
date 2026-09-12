"""
JARVIS Application Lifecycle Manager
Central orchestrator managing HUD states, tray, hotkeys, audio sessions, routing, and history logging.
"""

import re
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
from jarvis.app.live_mode import LiveSessionManager


class LifecycleManager(QObject):
    # Cross-thread GUI signals
    sig_set_state = Signal(str, str)
    sig_set_energy = Signal(float)
    sig_show_action = Signal(str, str, str, bool)
    sig_show_folder = Signal(str, str, list)
    sig_toggle_history = Signal()
    sig_open_settings = Signal()
    sig_popup = Signal()
    sig_disappear = Signal()
    sig_action_step = Signal(str, str, bool)
    sig_clear_pipeline = Signal()
    sig_show_prompt = Signal(str, str)
    sig_show_emails = Signal(list)
    sig_show_job = Signal(dict)

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

        # Safety watchdog to prevent any stuck "Thinking..." state
        self._processing_watchdog = QTimer(self)
        self._processing_watchdog.setSingleShot(True)
        self._processing_watchdog.timeout.connect(self._on_processing_timeout)

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
        self._latest_cursor_capture = None
        self._cursor_ready_event = threading.Event()
        self._cursor_ready_event.set()  # Initially ready
        
        self.live_session = LiveSessionManager(
            on_state_change=lambda state, text: self.sig_set_state.emit(state, text),
            start_listening_callback=lambda: self.recorder.start_listening(push_to_talk=False)
        )

        self._connect_signals()

    def _connect_signals(self):
        # GUI Signal connections
        self.sig_set_state.connect(self._on_set_state_wrapper)
        self.sig_set_energy.connect(self.notch.update_energy)
        self.sig_show_action.connect(self.notch.show_action_preview)
        self.sig_show_folder.connect(self.notch.show_folder_preview)
        self.sig_toggle_history.connect(self.sidebar.toggle)
        self.sig_open_settings.connect(self.settings_dialog.show)
        self.sig_popup.connect(self.notch.pop_up)
        self.sig_disappear.connect(self.notch.disappear)
        self.sig_action_step.connect(self.notch.add_pipeline_step)
        self.sig_clear_pipeline.connect(self.notch.clear_pipeline)
        self.sig_show_prompt.connect(self.notch.show_prompt_card)
        self.sig_show_emails.connect(self.notch.show_email_list)
        self.sig_show_job.connect(self.notch.show_job_card)

        # Notch signals
        self.notch.clicked.connect(self.toggle_session)
        self.notch.confirmed.connect(self._on_action_confirmed)
        self.notch.cancelled.connect(self._on_action_cancelled)
        self.notch.close_requested.connect(self.dismiss_notch)
        self.notch.live_toggled.connect(self._on_live_toggled)

        # Tray signals
        self.tray.activate_requested.connect(self.toggle_session)
        self.tray.history_requested.connect(self.toggle_history)
        self.tray.settings_requested.connect(self.open_settings)
        self.tray.pause_toggled.connect(self._on_pause_toggled)
        self.tray.mode_toggled.connect(self.notch.set_mode)
        self.tray.exit_requested.connect(self.shutdown)
        self.tray.restart_requested.connect(self.restart)

        # Sidebar signals
        self.sidebar.run_again_requested.connect(self.execute_command_text)

        # Settings signals
        self.settings_dialog.settings_saved.connect(self._on_settings_reloaded)

    @Slot(str, str)
    def _on_set_state_wrapper(self, state: str, text: str):
        if state == "PROCESSING":
            self._processing_watchdog.start(7500)
        else:
            self._processing_watchdog.stop()
        self.notch.set_state(state, text)

    @Slot()
    def _on_processing_timeout(self):
        """Auto-recovers from any stuck processing state."""
        if getattr(self.notch, "_state", "") == "PROCESSING":
            print("[Lifecycle] Processing watchdog triggered. Auto-recovering to IDLE.")
            self.notch.set_state("IDLE", "Ready • Hold Ctrl+Alt to speak")

    def _on_pause_toggled(self, is_paused: bool):
        """Disables or resumes hotkeys and mic access."""
        if is_paused:
            self.hotkeys.pause()
            if self.recorder.is_recording:
                self.recorder.stop_listening()
            tts_engine.stop()
            self.notch.set_state("IDLE", "Assistant Paused")
            print("[Lifecycle] Assistant paused from system tray.")
        else:
            self.hotkeys.resume()
            self.notch.set_state("IDLE", "Ready • Hold Ctrl+Alt to speak")
            print("[Lifecycle] Assistant resumed from system tray.")

    def start(self):
        """Starts background workers, tray icon, and global hotkeys."""
        self.tray.show()
        # Keep Notch hidden by default until hotkey Ctrl+Alt is pressed
        self.notch.set_mode(config.get("active_mode", "agent"))
        self.hotkeys.start()
        print("[Lifecycle] JARVIS VoiceOS operational (hidden background mode, press Ctrl+Alt to activate).")

    def shutdown(self):
        print("[Lifecycle] Shutting down JARVIS...")
        self.hotkeys.stop()
        self.recorder.stop_listening()
        tts_engine.stop()
        self.tray.hide()
        self.notch.close()
        self.sidebar.close()
        self.floating_action_overlay.close()
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
        from jarvis.utils.cursor_logger import log_layer
        log_layer(1, "Global hotkey Ctrl+Alt detected DOWN")

        if tts_engine.is_speaking():
            tts_engine.stop()

        self._pending_confirmation = False
        self.sig_popup.emit()
        self.sig_set_state.emit("LISTENING", "Listening...")

        # 1. Capture cursor coordinates & start in-memory ROI snapshot at exact moment of hotkey press
        try:
            from PySide6.QtGui import QCursor
            pos = QCursor.pos()
            cx, cy = pos.x(), pos.y()
            log_layer(2, f"Cursor position recorded at hotkey trigger", x=cx, y=cy)

            self._cursor_ready_event.clear()

            def _capture_cursor_roi():
                try:
                    res = self.router.screen_tool.execute("capture_cursor_region", cursor_pos=(cx, cy))
                    if res.is_success():
                        self._latest_cursor_capture = res.data
                        log_layer(3, "In-memory cursor ROI capture ready", bytes=len(res.data.get("image_bytes", b"")))
                except Exception as e:
                    log_layer(3, "In-memory pre-capture error", error=str(e))
                finally:
                    self._cursor_ready_event.set()

            threading.Thread(target=_capture_cursor_roi, daemon=True).start()
        except Exception as e:
            log_layer(2, "Cursor capture initialization failed", error=str(e))
            self._cursor_ready_event.set()

        if not self.recorder.is_recording:
            self.recorder.start_listening(push_to_talk=True)

    def on_hotkey_up(self, duration: float):
        """Called as soon as Ctrl+Alt is released (Push-to-Talk end)."""
        if duration >= 0.15:
            if self.recorder.is_recording:
                print(f"[Lifecycle] Hold-to-talk released ({duration:.2f}s). Processing speech...")
                self.sig_set_state.emit("PROCESSING", "Thinking...")
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
            self.sig_set_state.emit("IDLE", self.notch.prompt_label.text())
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
            self.recorder.start_listening(push_to_talk=False)

    @Slot()
    def toggle_history(self):
        """Toggles the sidebar history panel"""
        self.sig_toggle_history.emit()

    @Slot(bool)
    def _on_live_toggled(self, is_active: bool):
        if is_active:
            self.sig_popup.emit()
            self.live_session.start()
        else:
            self.live_session.stop()
            self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak")

    @Slot()
    def open_settings(self):
        self.sig_open_settings.emit()

    def _on_settings_reloaded(self):
        self.stt_provider = get_stt_provider()
        self.notch.set_mode(config.get("active_mode", "agent"))

    @staticmethod
    def _clean_for_display(text: str) -> str:
        """Strip markdown formatting for clean HUD display."""
        if not text:
            return text
        # Remove markdown headers (###, ##, #)
        t = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Remove bold/italic markers
        t = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', t)
        t = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', t)
        # Remove bullet points (• , - , * at line start)
        t = re.sub(r'^[•\-\*]\s+', '', t, flags=re.MULTILINE)
        # Remove code backticks
        t = re.sub(r'`([^`]+)`', r'\1', t)
        # Remove emojis (common unicode ranges)
        t = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F]', '', t)
        # Collapse multiple blank lines
        t = re.sub(r'\n{3,}', '\n\n', t)
        return t.strip()

    def _on_audio_energy(self, energy: float):
        self.sig_set_energy.emit(energy)

    def _on_speech_finished(self, audio_data: np.ndarray):
        """Called asynchronously when user finishes speaking (VAD silence detected)."""
        if self.live_session.is_active:
            self.sig_set_state.emit("PROCESSING", "Transcribing speech...")
            def _live_worker():
                try:
                    transcript = self.stt_provider.transcribe(audio_data)
                    if transcript and transcript.strip():
                        self.live_session.process_turn(transcript)
                    else:
                        self.live_session.start_listening()
                except Exception as e:
                    print(f"Live STT error: {e}")
                    self.live_session.start_listening()
            threading.Thread(target=_live_worker, daemon=True).start()
            return
            
        self.sig_set_state.emit("PROCESSING", "Transcribing speech...")

        def _worker():
            # 1. Speech to Text
            try:
                t0 = time.perf_counter()
                transcript = self.stt_provider.transcribe(audio_data)
                t_stt = time.perf_counter() - t0
                print(f"[Profiler] STT (Transcription) latency: {t_stt:.3f}s")
            except Exception as e:
                print(f"[Lifecycle] STT failed: {e}")
                transcript = ""

            if not transcript or not transcript.strip():
                self.sig_set_state.emit("IDLE", "I couldn't hear you.")
                time.sleep(1.8)
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
            from jarvis.utils.cursor_logger import log_layer
            # Layer 5: Guarantee cursor capture is ready (prevent race condition between speech & screen capture)
            if hasattr(self, "_cursor_ready_event") and not self._cursor_ready_event.is_set():
                log_layer(5, "Awaiting in-memory cursor ROI before routing", transcript=transcript)
                self._cursor_ready_event.wait(timeout=1.5)

            cursor_data = getattr(self, "_latest_cursor_capture", None)
            log_layer(5, "Routing command with cursor context", has_cursor=bool(cursor_data), transcript=transcript)
            
            t0 = time.perf_counter()
            intent, result = self.router.route_and_execute(transcript, cursor_data=cursor_data)
            t_llm = time.perf_counter() - t0
            print(f"[Profiler] LLM Intent Classification & Action Execution latency: {t_llm:.3f}s")

            # Check if confirmation is required OR staged action (email sending, message, reminder)
            is_staged = (
                result.requires_confirmation
                or (intent and intent.category.value == "CALENDAR")
                or (intent and intent.category.value == "MESSAGING")
                or (intent and intent.category.value == "EMAIL" and intent.action not in ["read_emails", "check_emails", "check_gmail", "read_inbox", "read_gmail"])
            )
            if is_staged:
                self._pending_confirmation = result.requires_confirmation
                self._pending_intent = intent
                title = intent.target or intent.category.value.title()
                details = result.confirmation_prompt or result.message
                icon = "✉️" if intent.category.value == "EMAIL" else ("📅" if intent.category.value == "CALENDAR" else "⚡")

                self.sig_show_action.emit(title, details, icon, result.requires_confirmation)

                if result.requires_confirmation:
                    self.sig_set_state.emit("CONFIRMATION_REQUIRED", result.message)
                    tts_engine.speak(result.message)
                    return

            self._process_result(intent, result, transcript)

        threading.Thread(target=_worker, daemon=True).start()

    def _process_result(self, intent, result, transcript: str):
        status_text = result.message

        # Check if job application card needs to be rendered in the notch
        if result.data and result.data.get("is_job_card"):
            self.sig_show_job.emit(result.data)

        # Check if folder browser view needs to be rendered in the top-center notch
        elif result.data and result.data.get("is_folder_browser"):
            f_name = result.data.get("folder_name", "Folder")
            f_path = result.data.get("folder_path", "")
            items = result.data.get("items", [])
            self.sig_show_folder.emit(f_name, f_path, items)

        # Check if prompt card needs to be rendered in the notch
        elif result.data and result.data.get("is_prompt_card"):
            topic = result.data.get("topic", "Custom Prompt")
            prompt_text = result.data.get("prompt_text", "")
            self.sig_show_prompt.emit(topic, prompt_text)

        # Check if email list card needs to be rendered in the notch
        elif result.data and result.data.get("is_email_list"):
            emails = result.data.get("emails", [])
            self.sig_show_emails.emit(emails)

        # Pull full_details from: 1) tool result data, 2) intent params, 3) status_text
        full_details = (
            (result.data or {}).get("full_details")
            or intent.params.get("full_details")
            or status_text
        )

        # Strip markdown formatting for clean HUD display
        hud_text = self._clean_for_display(full_details)

        # Multi-step pipeline tracking
        if result.next_steps:
            self.sig_set_state.emit("EXECUTING", "Performing action sequence...")
            self.sig_action_step.emit(f"Step 1: {intent.action}", "⚡", True)
            
            step_count = 1
            for next_step in result.next_steps:
                step_count += 1
                self.sig_action_step.emit(f"Step {step_count}: {next_step}", "⚡", True)

        # Immediately display clean text in top notch HUD
        if result.is_success():
            self.sig_set_state.emit("SPEAKING", hud_text)
        else:
            self.sig_set_state.emit("ERROR", self._clean_for_display(status_text))

        # Feed turn into Chat Composer Thread
        try:
            self.sidebar.add_chat_turn(transcript, hud_text)
        except Exception as e:
            print(f"[Lifecycle] Failed to add chat turn: {e}")

        # Log to persistent SQLite history
        if config.get("save_history", True):
            self.history_repo.log_interaction(
                command_text=transcript,
                response_text=full_details,
                tool=str(intent.category.value),
                action=intent.action,
                params=intent.params,
                status=result.status,
                result_summary=status_text,
            )

        # Immediate Google Assistant-style voice response:
        # Speak the first 1-2 punchy sentences so TTS starts instantly without buffering delay,
        # while hud_text displays the complete visual card for reading.
        raw_speech = status_text
        import re
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_speech) if s.strip()]
        if len(sentences) > 2:
            spoken_text = " ".join(sentences[:2])
        else:
            spoken_text = raw_speech

        def on_tts_finish():
            # Keep notch open so the user can read the complete response
            self.sig_set_state.emit("IDLE", hud_text)

        tts_engine.speak(spoken_text, on_finish=on_tts_finish)

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

    def _on_live_toggled(self, is_live: bool):
        if is_live:
            print("[Lifecycle] Starting Gemini Live mode session.")
            self.live_session.start()
        else:
            print("[Lifecycle] Stopping Gemini Live mode session.")
            self.live_session.stop()
            self.sig_set_state.emit("IDLE", "Ready • Hold Ctrl+Alt to speak")
