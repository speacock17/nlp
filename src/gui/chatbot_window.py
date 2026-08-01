from queue import Empty, Queue
from threading import Thread
import tkinter as tk
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
        self._root.title(
            "Chatbot NLP"
        )
        self._root.geometry("760x560")
        self._root.minsize(620, 450)

        self._root.columnconfigure(
            0,
            weight=1,
        )
        self._root.rowconfigure(
            1,
            weight=1,
        )

    def _build_widgets(self) -> None:
        header = ttk.Frame(
            self._root,
            padding=12,
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            header,
            text=(
                "Chatbot sulle opere visitabili a Napoli"
            ),
            font=("Segoe UI", 15, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        engine_frame = ttk.Frame(header)
        engine_frame.grid(
            row=0,
            column=1,
            sticky="e",
        )

        ttk.Label(
            engine_frame,
            text="Riconoscimento:",
        ).grid(
            row=0,
            column=0,
            padx=(0, 6),
        )

        self._engine_selector = ttk.Combobox(
            engine_frame,
            textvariable=self._engine_var,
            values=("whisper", "google"),
            state="readonly",
            width=10,
        )
        self._engine_selector.grid(
            row=0,
            column=1,
        )
        self._engine_selector.bind(
            "<<ComboboxSelected>>",
            self._on_engine_changed,
        )

        history_frame = ttk.Frame(
            self._root,
            padding=(12, 0, 12, 8),
        )
        history_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        history_frame.columnconfigure(
            0,
            weight=1,
        )
        history_frame.rowconfigure(
            0,
            weight=1,
        )

        self._history = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            padx=10,
            pady=10,
        )
        self._history.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        input_frame = ttk.Frame(
            self._root,
            padding=(12, 0, 12, 8),
        )
        input_frame.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        input_frame.columnconfigure(
            0,
            weight=1,
        )

        self._question_entry = ttk.Entry(
            input_frame,
            textvariable=self._question_var,
        )
        self._question_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        self._question_entry.bind(
            "<Return>",
            self._on_submit_event,
        )

        self._send_button = ttk.Button(
            input_frame,
            text="Invia",
            command=self._submit_text,
        )
        self._send_button.grid(
            row=0,
            column=1,
            padx=(0, 8),
        )

        self._speak_button = ttk.Button(
            input_frame,
            text="Parla",
            command=self._start_listening,
        )
        self._speak_button.grid(
            row=0,
            column=2,
        )

        footer = ttk.Frame(
            self._root,
            padding=(12, 0, 12, 12),
        )
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            footer,
            textvariable=self._status_var,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            footer,
            text="Termina conversazione",
            command=self._on_close,
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
        self._history.insert(
            tk.END,
            f"{role}: {text}\n\n",
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
            else "readonly"
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
