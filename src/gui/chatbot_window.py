from queue import Empty, Queue
from threading import Thread
import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, ttk

from src.speech.exceptions import (
    SpeechInputTimeoutError,
    SpeechNotUnderstoodError,
    SpeechRecognitionServiceError,
)


class ChatbotWindow:
    def __init__(
        self,
        root: tk.Tk,
        controller,
        speech_to_text_cache,
        close_callback=None,
        default_engine: str = "whisper",
    ) -> None:
        self._root = root
        self._controller = controller
        self._speech_to_text_cache = (
            speech_to_text_cache
        )
        self._close_callback = close_callback
        self._events = Queue()
        self._busy = False
        self._closed = False

        self._engine_var = tk.StringVar(
            value=default_engine
        )
        self._question_var = tk.StringVar()
        self._status_var = tk.StringVar(
            value="Pronto"
        )

        self._configure_window()
        self._build_widgets()

        self._root.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )
        self._root.after(
            100,
            self._poll_events,
        )

    def _configure_window(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._root.title(
            "Chatbot NLP - Arte a Napoli"
        )
        self._root.geometry("980x700")
        self._root.minsize(820, 600)
        self._root.configure(
            fg_color="#F4F7FB"
        )

        self._root.columnconfigure(
            0,
            weight=1,
        )
        self._root.rowconfigure(
            1,
            weight=1,
        )

    def _build_widgets(self) -> None:
        header = ctk.CTkFrame(
            self._root,
            fg_color="#FFFFFF",
            corner_radius=18,
            border_width=1,
            border_color="#E6EAF0",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=24,
            pady=(24, 16),
        )
        header.columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            header,
            text=(
                "Chatbot sulle opere visitabili a Napoli"
            ),
            font=ctk.CTkFont(
                family="Segoe UI",
                size=24,
                weight="bold",
            ),
            text_color="#172033",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(22, 12),
            pady=(18, 2),
        )

        ctk.CTkLabel(
            header,
            text=(
                "Esplora Caravaggio e Battistello "
                "Caracciolo attraverso una conversazione."
            ),
            font=ctk.CTkFont(
                family="Segoe UI",
                size=13,
            ),
            text_color="#667085",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(22, 12),
            pady=(0, 18),
        )

        engine_frame = ctk.CTkFrame(
            header,
            fg_color="transparent",
        )
        engine_frame.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(12, 22),
        )

        ctk.CTkLabel(
            engine_frame,
            text="Riconoscimento vocale",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold",
            ),
            text_color="#475467",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self._engine_selector = ctk.CTkSegmentedButton(
            engine_frame,
            values=("whisper", "google"),
            variable=self._engine_var,
            command=self._on_engine_changed,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold",
            ),
            height=34,
            corner_radius=10,
        )
        self._engine_selector.grid(
            row=1,
            column=0,
            sticky="e",
        )

        history_frame = ctk.CTkFrame(
            self._root,
            fg_color="#FFFFFF",
            corner_radius=18,
            border_width=1,
            border_color="#E6EAF0",
        )
        history_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=24,
            pady=(0, 16),
        )
        history_frame.columnconfigure(
            0,
            weight=1,
        )
        history_frame.rowconfigure(
            1,
            weight=1,
        )

        ctk.CTkLabel(
            history_frame,
            text="Conversazione",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold",
            ),
            text_color="#344054",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(16, 8),
        )

        self._history = ctk.CTkTextbox(
            history_frame,
            wrap="word",
            state=tk.DISABLED,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
            ),
            fg_color="#F8FAFC",
            text_color="#172033",
            corner_radius=12,
            border_width=0,
            padx=14,
            pady=14,
        )
        self._history.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(0, 16),
        )

        self._history._textbox.tag_configure(
            "role_system",
            foreground="#667085",
            font=("Segoe UI", 11, "bold"),
            spacing1=4,
            spacing3=2,
        )
        self._history._textbox.tag_configure(
            "role_user",
            foreground="#3448A5",
            font=("Segoe UI", 11, "bold"),
            spacing1=4,
            spacing3=2,
        )
        self._history._textbox.tag_configure(
            "role_chatbot",
            foreground="#287A4B",
            font=("Segoe UI", 11, "bold"),
            spacing1=4,
            spacing3=2,
        )

        input_frame = ctk.CTkFrame(
            self._root,
            fg_color="#FFFFFF",
            corner_radius=18,
            border_width=1,
            border_color="#E6EAF0",
        )
        input_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 12),
        )
        input_frame.columnconfigure(
            0,
            weight=1,
        )

        self._question_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self._question_var,
            placeholder_text="Scrivi una domanda sulle opere...",
            height=48,
            corner_radius=12,
            border_width=1,
            border_color="#D0D5DD",
            fg_color="#F8FAFC",
            text_color="#172033",
            placeholder_text_color="#98A2B3",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
            ),
        )
        self._question_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(16, 10),
            pady=16,
        )
        self._question_entry.bind(
            "<Return>",
            self._on_submit_event,
        )

        self._send_button = ctk.CTkButton(
            input_frame,
            text="Invia",
            command=self._submit_text,
            width=96,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold",
            ),
        )
        self._send_button.grid(
            row=0,
            column=1,
            padx=(0, 10),
            pady=16,
        )

        self._speak_button = ctk.CTkButton(
            input_frame,
            text="🎙  Parla",
            command=self._start_listening,
            width=112,
            height=48,
            corner_radius=12,
            fg_color="#EEF2FF",
            hover_color="#E0E7FF",
            text_color="#3448A5",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold",
            ),
        )
        self._speak_button.grid(
            row=0,
            column=2,
            padx=(0, 16),
            pady=16,
        )

        footer = ctk.CTkFrame(
            self._root,
            fg_color="transparent",
        )
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 20),
        )
        footer.columnconfigure(
            0,
            weight=1,
        )

        status_frame = ctk.CTkFrame(
            footer,
            fg_color="#EAF7EF",
            corner_radius=10,
        )
        status_frame.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            status_frame,
            textvariable=self._status_var,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
                weight="bold",
            ),
            text_color="#287A4B",
        ).grid(
            row=0,
            column=0,
            padx=12,
            pady=7,
        )

        ctk.CTkButton(
            footer,
            text="Termina conversazione",
            command=self._on_close,
            width=158,
            height=36,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#FEECEC",
            border_width=1,
            border_color="#D0D5DD",
            text_color="#667085",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=12,
            ),
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        self._append_message(
            "Sistema",
            (
                "Puoi scrivere una domanda oppure "
                "premere Parla."
            ),
        )
        self._question_entry.focus_set()

    def _on_submit_event(self, _event) -> None:
        self._submit_text()

    def _submit_text(self) -> None:
        if self._busy:
            return

        question = self._question_var.get().strip()

        if not question:
            self._status_var.set(
                "Inserisci una domanda."
            )
            return

        self._question_var.set("")
        self._append_message(
            "Utente",
            question,
        )
        self._set_busy(
            True,
            "Sto elaborando la risposta...",
        )

        Thread(
            target=self._process_text,
            args=(question,),
            daemon=True,
        ).start()

    def _process_text(self, question: str) -> None:
        try:
            response = self._controller.submit_text(
                question,
                speak_response=False,
            )
            self._events.put(
                (
                    "response",
                    response.text,
                )
            )
            self._controller.speak_response(
                response
            )
            self._events.put(
                ("speech_done",)
            )
        except Exception as error:
            self._events.put(
                (
                    "error",
                    str(error),
                )
            )

    def _start_listening(self) -> None:
        if self._busy:
            return

        self._set_busy(
            True,
            "In ascolto...",
        )

        engine_name = self._engine_var.get()

        Thread(
            target=self._process_voice,
            args=(engine_name,),
            daemon=True,
        ).start()

    def _process_voice(
        self,
        engine_name: str,
    ) -> None:
        try:
            speech_to_text = (
                self._speech_to_text_cache.get(
                    engine_name
                )
            )
            self._controller.set_speech_to_text(
                speech_to_text
            )

            transcription, response = (
                self._controller.listen_and_submit(
                    speak_response=False,
                )
            )

            self._events.put(
                (
                    "voice_response",
                    transcription,
                    response.text,
                )
            )
            self._controller.speak_response(
                response
            )
            self._events.put(
                ("speech_done",)
            )

        except SpeechInputTimeoutError:
            self._events.put(
                (
                    "error",
                    "Nessun parlato rilevato.",
                )
            )

        except SpeechNotUnderstoodError:
            self._events.put(
                (
                    "error",
                    "Non ho compreso l'audio.",
                )
            )

        except SpeechRecognitionServiceError:
            self._events.put(
                (
                    "error",
                    (
                        "Il servizio di riconoscimento "
                        "vocale non ? disponibile."
                    ),
                )
            )

        except Exception as error:
            self._events.put(
                (
                    "error",
                    str(error),
                )
            )

    def _poll_events(self) -> None:
        try:
            while True:
                event = self._events.get_nowait()
                self._handle_event(event)
        except Empty:
            pass

        if not self._closed:
            self._root.after(
                100,
                self._poll_events,
            )

    def _handle_event(self, event: tuple) -> None:
        event_type = event[0]

        if event_type == "response":
            self._append_message(
                "Chatbot",
                event[1],
            )
            self._status_var.set(
                "Riproduzione della risposta..."
            )
            return

        if event_type == "voice_response":
            self._append_message(
                "Utente",
                event[1],
            )
            self._append_message(
                "Chatbot",
                event[2],
            )
            self._status_var.set(
                "Riproduzione della risposta..."
            )
            return

        if event_type == "speech_done":
            self._set_busy(
                False,
                "Pronto",
            )
            return

        if event_type == "error":
            message = (
                event[1]
                if event[1]
                else "Errore imprevisto."
            )
            self._append_message(
                "Sistema",
                message,
            )
            self._set_busy(
                False,
                "Operazione non riuscita",
            )

    def _append_message(
        self,
        role: str,
        text: str,
    ) -> None:
        self._history.configure(
            state=tk.NORMAL
        )

        role_tag = {
            "Sistema": "role_system",
            "Utente": "role_user",
            "Chatbot": "role_chatbot",
        }.get(
            role,
            "role_system",
        )

        self._history.insert(
            tk.END,
            f"{role}\n",
            role_tag,
        )
        self._history.insert(
            tk.END,
            f"{text}\n\n",
        )

        self._history.configure(
            state=tk.DISABLED
        )
        self._history.see(tk.END)

    def _set_busy(
        self,
        busy: bool,
        status: str,
    ) -> None:
        self._busy = busy
        self._status_var.set(status)

        state = (
            tk.DISABLED
            if busy
            else tk.NORMAL
        )
        selector_state = (
            tk.DISABLED
            if busy
            else tk.NORMAL
        )

        self._question_entry.configure(
            state=state
        )
        self._send_button.configure(
            state=state
        )
        self._speak_button.configure(
            state=state
        )
        self._engine_selector.configure(
            state=selector_state
        )

        if not busy:
            self._question_entry.focus_set()

    def _on_engine_changed(self, _event) -> None:
        engine_name = self._engine_var.get()
        self._status_var.set(
            f"Motore selezionato: {engine_name}"
        )

    def _on_close(self) -> None:
        if self._closed:
            return

        self._closed = True

        if callable(self._close_callback):
            self._close_callback()

        self._root.destroy()
