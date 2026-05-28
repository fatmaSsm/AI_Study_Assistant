import customtkinter as ctk
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import threading
import json
import os
from tkinter import messagebox

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg":        "#0D0F14",
    "surface":   "#151820",
    "card":      "#1C2030",
    "border":    "#252A3A",
    "accent":    "#4F8EF7",
    "accent2":   "#7C5CFC",
    "green":     "#3DDC84",
    "red":       "#FF5C5C",
    "yellow":    "#FFD166",
    "text":      "#E8EAF2",
    "muted":     "#6B7280",
    "highlight": "#2A3050",
}

FONT_TITLE = ("Georgia", 22, "bold")
FONT_HEAD  = ("Georgia", 15, "bold")
FONT_BODY  = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_BTN   = ("Segoe UI", 12, "bold")
FONT_TAG   = ("Segoe UI", 10, "bold")

# ── Pydantic Şemaları (Gemini Yapılandırılmış Çıktı Güvencesi) ───────────────
class KeywordsSchema(BaseModel):
    keywords: List[str] = Field(description="List of 8-12 extracted keywords")

class QuizQuestionSchema(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="4 options starting with A), B), C), D)")
    answer: str = Field(description="Only the single letter of the correct option (A, B, C, or D)")

class QuizSchema(BaseModel):
    quiz: List[QuizQuestionSchema] = Field(description="List of exactly 5 multiple-choice questions")

# ── i18n ───────────────────────────────────────────────────────────────────────
STRINGS = {
    "TR": {
        "subtitle":          "Özetle · Keşfet · Sına",
        "settings_title":    "⚙  API Ayarları",
        "api_label":         "Google Gemini API Anahtarı",
        "api_placeholder":   "AIzaSy...",
        "api_save":          "Kaydet & Kapat",
        "api_saved":         "✅  API anahtarı kaydedildi.",
        "api_empty":         "API anahtarı boş bırakılamaz.",
        "panel_title":       "📄  Metninizi Girin",
        "panel_sub":         "Analiz etmek istediğiniz metni aşağıya yapıştırın.",
        "placeholder":       "Buraya analiz etmek istediğiniz metni yapıştırın...\n\nDers notları, makale özeti, kitap bölümü — her türlü metin olabilir.",
        "ph_start":          "Buraya analiz",
        "word_count":        "{n} kelime",
        "btn_analyze":       "✨  Analiz Et",
        "btn_quiz":          "🎯  Quiz Başlat",
        "btn_clear":         "🧹 Temizle",
        "tab_summary":       "📝 Özet",
        "tab_keywords":      "🔑 Anahtar Kelimeler",
        "tab_quiz":          "🎯 Quiz",
        "summary_head":      "📝  Özet",
        "kw_head":           "🔑  Anahtar Kelimeler",
        "question_label":    "Soru {n}",
        "btn_check":         "✨  Cevapları Kontrol Et",
        "status_init":       "Metninizi girin ve 'Analiz Et' butonuna tıklayın.",
        "status_analyzing":  "⏳ Analiz ediliyor, lütfen bekleyin...",
        "status_summary":    "📝 Özet oluşturuluyor...",
        "status_keywords":   "🔑 Anahtar kelimeler çıkarılıyor...",
        "status_done":       "✅ Analiz tamamlandı! Quiz için hazır.",
        "status_quiz_gen":   "🎯 Quiz soruları oluşturuluyor...",
        "status_quiz_ready": "🎯 Quiz hazır! Soruları cevaplayın.",
        "status_quiz_done":  "Quiz tamamlandı: {s}/{t} (%{p})",
        "status_err":        "❌ Hata: {e}",
        "status_quiz_err":   "❌ Quiz hatası: {e}",
        "quiz_loading":      "⏳  Quiz soruları hazırlanıyor...",
        "quiz_score":        "{e}  {s}/{t} doğru  —  %{p}",
        "warn_no_text":      "Lütfen önce bir metin girin.",
        "warn_short":        "Metin çok kısa. En az 20 kelime girin.",
        "warn_no_analysis":  "Önce metin girip analiz yapmalısınız.",
        "warn_title":        "Uyarı",
        "no_api_title":      "API Anahtarı Yok",
        "no_api_msg":        "Google Gemini API anahtarı bulunamadı.\nLütfen sağ üstteki ⚙ butonuna tıklayarak anahtarınızı girin.",
        "sys_summary":       "Sen bir akademik asistansın. Kullanıcının verdiği metni Türkçe olarak açık, akıcı ve anlaşılır biçimde özetle. Özet 3-6 paragraf arasında olsun. Madde işareti kullanma, düz paragraf yaz.",
        "prompt_summary":    "Şu metni özetle:\n\n{text}",
        "sys_keywords":      "Sen bir akademik asistansın. Verilen metinden en önemli 8-12 anahtar kelimeyi veya kavramı çıkar.",
        "prompt_keywords":   "Anahtar kelimeleri çıkar:\n\n{text}",
        "sys_quiz":          "Sen bir eğitim asistansın. Verilen metne göre 5 adet çoktan seçmeli soru üret. Şıkların 'A) ', 'B) ' gibi başladığından emin ol.",
        "prompt_quiz":       "5 soruluk quiz üret:\n\n{text}",
    },
    "EN": {
        "subtitle":          "Summarize · Discover · Test",
        "settings_title":    "⚙  API Settings",
        "api_label":         "Google Gemini API Key",
        "api_placeholder":   "AIzaSy...",
        "api_save":          "Save & Close",
        "api_saved":         "✅  API key saved.",
        "api_empty":         "API key cannot be empty.",
        "panel_title":       "📄  Enter Your Text",
        "panel_sub":         "Paste the text you want to analyze below.",
        "placeholder":       "Paste the text you want to analyze here...\n\nLecture notes, article summaries, book chapters — any text works.",
        "ph_start":          "Paste the text",
        "word_count":        "{n} words",
        "btn_analyze":       "✨  Analyze",
        "btn_quiz":          "🎯  Start Quiz",
        "btn_clear":         "🧹 Clear",
        "tab_summary":       "📝 Summary",
        "tab_keywords":      "🔑 Keywords",
        "tab_quiz":          "🎯 Quiz",
        "summary_head":      "📝  Summary",
        "kw_head":           "🔑  Keywords",
        "question_label":    "Question {n}",
        "btn_check":         "✨  Check Answers",
        "status_init":       "Enter your text and click 'Analyze'.",
        "status_analyzing":  "⏳ Analyzing, please wait...",
        "status_summary":    "📝 Generating summary...",
        "status_keywords":   "🔑 Extracting keywords...",
        "status_done":       "✅ Analysis complete! Ready for quiz.",
        "status_quiz_gen":   "🎯 Generating quiz questions...",
        "status_quiz_ready": "🎯 Quiz ready! Answer the questions.",
        "status_quiz_done":  "Quiz done: {s}/{t} ({p}%)",
        "status_err":        "❌ Error: {e}",
        "status_quiz_err":   "❌ Quiz error: {e}",
        "quiz_loading":      "⏳  Generating quiz questions...",
        "quiz_score":        "{e}  {s}/{t} correct  —  {p}%",
        "warn_no_text":      "Please enter a text first.",
        "warn_short":        "Text is too short. Enter at least 20 words.",
        "warn_no_analysis":  "Please enter and analyze a text first.",
        "warn_title":        "Warning",
        "no_api_title":      "No API Key",
        "no_api_msg":        "Google Gemini API key not found.\nPlease click the ⚙ button in the top right to enter your key.",
        "sys_summary":       "You are an academic assistant. Summarize the given text in clear, fluent, and easy-to-understand English. The summary should be 3-6 paragraphs. Do not use bullet points; write in plain paragraphs.",
        "prompt_summary":    "Summarize this text:\n\n{text}",
        "sys_keywords":      "You are an academic assistant. Extract the 8-12 most important keywords or concepts from the given text.",
        "prompt_keywords":   "Extract keywords:\n\n{text}",
        "sys_quiz":          "You are an educational assistant. Generate 5 multiple-choice questions based on the given text. Ensure options start with 'A) ', 'B) ' etc.",
        "prompt_quiz":       "Generate a 5-question quiz:\n\n{text}",
    }
}

# ── API key helpers ────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ai_study_config.json")

def load_api_key() -> str:
    env = os.environ.get("GEMINI_API_KEY", "")
    if env:
        return env
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return data.get("api_key", "")
        except Exception:
            pass
    return ""

def save_api_key(key: str):
    os.environ["GEMINI_API_KEY"] = key
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_key": key}, f)
    except Exception:
        pass

# ── Gemini API Helpers ──────────────────────────────────────────────────────────
def call_gemini(prompt: str, system: str = "", response_schema=None) -> str:
    key = load_api_key()
    client = genai.Client(api_key=key)
    
    config_args = {"temperature": 0.3}
    if system:
        config_args["system_instruction"] = system
    if response_schema:
        config_args["response_mime_type"] = "application/json"
        config_args["response_schema"] = response_schema
        
    config = types.GenerateContentConfig(**config_args)
    
    resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=config
    )
    return resp.text.strip()

def get_summary(text: str, lang: str) -> str:
    s = STRINGS[lang]
    return call_gemini(s["prompt_summary"].format(text=text), s["sys_summary"])

def get_keywords(text: str, lang: str) -> list:
    s = STRINGS[lang]
    raw_json = call_gemini(s["prompt_keywords"].format(text=text), s["sys_keywords"], response_schema=KeywordsSchema)
    data = json.loads(raw_json)
    return data.get("keywords", [])

def get_quiz(text: str, lang: str) -> list:
    s = STRINGS[lang]
    raw_json = call_gemini(s["prompt_quiz"].format(text=text), s["sys_quiz"], response_schema=QuizSchema)
    data = json.loads(raw_json)
    return data.get("quiz", [])


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, lang: str, on_save=None):
        super().__init__(master)
        self._lang = lang
        self._on_save = on_save
        s = STRINGS[lang]

        self.title(s["settings_title"])
        self.geometry("480x260")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["surface"])
        self.grab_set()
        self.lift()
        self.focus_force()

        ctk.CTkLabel(self, text=s["settings_title"],
                     font=FONT_HEAD, text_color=COLORS["text"]
                     ).pack(anchor="w", padx=24, pady=(22, 4))

        ctk.CTkLabel(self, text=s["api_label"],
                     font=FONT_SMALL, text_color=COLORS["muted"]
                     ).pack(anchor="w", padx=24, pady=(10, 2))

        self.entry = ctk.CTkEntry(
            self, placeholder_text=s["api_placeholder"],
            font=FONT_BODY, height=42, corner_radius=8,
            fg_color=COLORS["card"], text_color=COLORS["text"],
            border_color=COLORS["border"], show="•"
        )
        self.entry.pack(fill="x", padx=24)

        existing = load_api_key()
        if existing:
            self.entry.insert(0, existing)

        self.lbl_status = ctk.CTkLabel(self, text="",
                                       font=FONT_SMALL, text_color=COLORS["green"])
        self.lbl_status.pack(anchor="w", padx=24, pady=(6, 0))

        ctk.CTkButton(
            self, text=s["api_save"],
            font=FONT_BTN, height=42,
            fg_color=COLORS["accent"], hover_color="#3A7AE4",
            text_color="white", corner_radius=8,
            command=self._save
        ).pack(fill="x", padx=24, pady=(12, 20))

    def _save(self):
        key = self.entry.get().strip()
        s = STRINGS[self._lang]
        if not key:
            self.lbl_status.configure(text=s["api_empty"], text_color=COLORS["red"])
            return
        save_api_key(key)
        self.lbl_status.configure(text=s["api_saved"], text_color=COLORS["green"])
        if self._on_save:
            self._on_save()
        self.after(800, self.destroy)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
class SmartStudyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Study Assistant")
        
        # ── Temel Geometri ve Sınırlar ─────────────────────────────────────────
        self.geometry("1160x780")
        self.minsize(920, 640)
        self.configure(fg_color=COLORS["bg"])

        # ── Zaman Ayarlı Güvenli Tam Ekran Çözümü ──────────────────────────────
        self.after(100, self._make_full_screen)

        self._lang         = "TR"
        self._quiz_data    = []
        self._answers      = {}
        self._quiz_widgets = []
        self._dyn = {}

        self._build_ui()
        self._check_api_on_start()

    def _make_full_screen(self):
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

    def _check_api_on_start(self):
        if not load_api_key():
            self.after(400, self._open_settings)

    def _build_ui(self):
        self._build_header()
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)
        self._build_left(body)
        self._build_right(body)

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORS["surface"],
                           corner_radius=0, height=68)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="✨  AI Study Assistant",
                     font=FONT_TITLE, text_color=COLORS["text"]
                     ).pack(side="left", padx=28, pady=14)

        right_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        right_frame.pack(side="right", padx=16)

        ctk.CTkButton(
            right_frame, text="⚙", width=38, height=38,
            font=("Segoe UI", 16), corner_radius=8,
            fg_color=COLORS["card"], hover_color=COLORS["highlight"],
            text_color=COLORS["muted"], border_width=1,
            border_color=COLORS["border"],
            command=self._open_settings
        ).pack(side="right", padx=(8, 0))

        lang_frame = ctk.CTkFrame(right_frame, fg_color=COLORS["card"],
                                  corner_radius=8, border_width=1,
                                  border_color=COLORS["border"])
        lang_frame.pack(side="right")

        self.btn_tr = ctk.CTkButton(
            lang_frame, text="TR", width=44, height=34,
            font=FONT_BTN, corner_radius=6,
            fg_color=COLORS["accent"], hover_color="#3A7AE4",
            text_color="white",
            command=lambda: self._set_lang("TR")
        )
        self.btn_tr.pack(side="left", padx=3, pady=3)

        self.btn_en = ctk.CTkButton(
            lang_frame, text="EN", width=44, height=34,
            font=FONT_BTN, corner_radius=6,
            fg_color="transparent", hover_color=COLORS["highlight"],
            text_color=COLORS["muted"],
            command=lambda: self._set_lang("EN")
        )
        self.btn_en.pack(side="left", padx=(0, 3), pady=3)

        self._dyn["subtitle"] = ctk.CTkLabel(
            right_frame, text=STRINGS[self._lang]["subtitle"],
            font=FONT_SMALL, text_color=COLORS["muted"]
        )
        self._dyn["subtitle"].pack(side="right", padx=12)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color=COLORS["surface"],
                            corner_radius=14, border_width=1,
                            border_color=COLORS["border"])
        left.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left.configure(width=390)
        left.pack_propagate(False)

        self._dyn["panel_title"] = ctk.CTkLabel(
            left, text=STRINGS[self._lang]["panel_title"],
            font=FONT_HEAD, text_color=COLORS["text"])
        self._dyn["panel_title"].pack(anchor="w", padx=20, pady=(18, 6))

        self._dyn["panel_sub"] = ctk.CTkLabel(
            left, text=STRINGS[self._lang]["panel_sub"],
            font=FONT_SMALL, text_color=COLORS["muted"],
            wraplength=340, justify="left")
        self._dyn["panel_sub"].pack(anchor="w", padx=20, pady=(0, 10))

        self.txt_input = ctk.CTkTextbox(
            left, font=FONT_BODY,
            fg_color=COLORS["card"], text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=1,
            corner_radius=10, wrap="word",
            scrollbar_button_color=COLORS["border"]
        )
        self.txt_input.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        self.txt_input.insert("0.0", STRINGS[self._lang]["placeholder"])
        self.txt_input.bind("<FocusIn>", self._clear_placeholder)
        self.txt_input.bind("<KeyRelease>", self._update_wc)

        # ── Meta Alt Çubuk (Temizle Butonu ve Kelime Sayacı) ───────────────────
        meta_frame = ctk.CTkFrame(left, fg_color="transparent")
        meta_frame.pack(fill="x", padx=20, pady=(4, 6))

        self.btn_clear = ctk.CTkButton(
            meta_frame, text=STRINGS[self._lang]["btn_clear"],
            font=FONT_SMALL, width=80, height=26, corner_radius=6,
            fg_color=COLORS["card"], hover_color=COLORS["highlight"],
            text_color=COLORS["red"], border_width=1, border_color=COLORS["border"],
            command=self._clear_input_completely
        )
        self.btn_clear.pack(side="left")

        self.lbl_wc = ctk.CTkLabel(meta_frame, text="", font=FONT_SMALL,
                                   text_color=COLORS["muted"])
        self.lbl_wc.pack(side="right")
        self._update_wc()

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(6, 18))

        self.btn_analyze = ctk.CTkButton(
            btn_frame, text=STRINGS[self._lang]["btn_analyze"],
            font=FONT_BTN, height=44,
            fg_color=COLORS["accent"], hover_color="#3A7AE4",
            text_color="white", corner_radius=10,
            command=self._start_analysis
        )
        self.btn_analyze.pack(fill="x", pady=(0, 8))

        self.btn_quiz_btn = ctk.CTkButton(
            btn_frame, text=STRINGS[self._lang]["btn_quiz"],
            font=FONT_BTN, height=44,
            fg_color=COLORS["accent2"], hover_color="#6B4EE0",
            text_color="white", corner_radius=10,
            command=self._start_quiz, state="disabled"
        )
        self.btn_quiz_btn.pack(fill="x")

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        tab_bar = ctk.CTkFrame(right, fg_color="transparent", height=48)
        tab_bar.pack(fill="x", pady=(0, 10))
        tab_bar.pack_propagate(False)

        self._tabs = {}
        tab_keys = ["summary", "keywords", "quiz"]
        for name in tab_keys:
            btn = ctk.CTkButton(
                tab_bar, text=STRINGS[self._lang][f"tab_{name}"],
                font=FONT_BTN, height=38, corner_radius=9,
                fg_color=COLORS["card"], hover_color=COLORS["highlight"],
                text_color=COLORS["muted"], border_width=1,
                border_color=COLORS["border"],
                command=lambda n=name: self._show_tab(n)
            )
            btn.pack(side="left", padx=(0, 8))
            self._tabs[name] = btn

        self.content = ctk.CTkFrame(right, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self._panels = {}
        for name in tab_keys:
            p = ctk.CTkFrame(self.content, fg_color=COLORS["surface"],
                             corner_radius=14, border_width=1,
                             border_color=COLORS["border"])
            self._panels[name] = p

        self._build_summary_panel()
        self._build_keywords_panel()
        self._build_quiz_panel()
        self._show_tab("summary")

        self.status_var = ctk.StringVar(value=STRINGS[self._lang]["status_init"])
        self.status_bar = ctk.CTkLabel(
            right, textvariable=self.status_var,
            font=FONT_SMALL, text_color=COLORS["muted"], anchor="w"
        )
        self.status_bar.pack(fill="x", pady=(8, 0))

    def _build_summary_panel(self):
        p = self._panels["summary"]
        self._dyn["summary_head"] = ctk.CTkLabel(
            p, text=STRINGS[self._lang]["summary_head"],
            font=FONT_HEAD, text_color=COLORS["text"])
        self._dyn["summary_head"].pack(anchor="w", padx=20, pady=(18, 8))

        self.summary_box = ctk.CTkTextbox(
            p, font=FONT_BODY, fg_color="transparent",
            text_color=COLORS["text"], wrap="word",
            border_width=0, corner_radius=0,
            scrollbar_button_color=COLORS["border"]
        )
        self.summary_box.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self.summary_box.configure(state="disabled")

    def _build_keywords_panel(self):
        p = self._panels["keywords"]
        self._dyn["kw_head"] = ctk.CTkLabel(
            p, text=STRINGS[self._lang]["kw_head"],
            font=FONT_HEAD, text_color=COLORS["text"])
        self._dyn["kw_head"].pack(anchor="w", padx=20, pady=(18, 8))

        self.kw_scroll = ctk.CTkScrollableFrame(
            p, fg_color="transparent",
            scrollbar_button_color=COLORS["border"]
        )
        self.kw_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 18))

    def _build_quiz_panel(self):
        p = self._panels["quiz"]
        self.quiz_scroll = ctk.CTkScrollableFrame(
            p, fg_color="transparent",
            scrollbar_button_color=COLORS["border"]
        )
        self.quiz_scroll.pack(fill="both", expand=True, padx=16, pady=16)

    def _set_lang(self, lang: str):
        if self._lang == lang:
            return
        self._lang = lang
        s = STRINGS[lang]

        if lang == "TR":
            self.btn_tr.configure(fg_color=COLORS["accent"], text_color="white")
            self.btn_en.configure(fg_color="transparent", text_color=COLORS["muted"])
        else:
            self.btn_en.configure(fg_color=COLORS["accent"], text_color="white")
            self.btn_tr.configure(fg_color="transparent", text_color=COLORS["muted"])

        self._dyn["subtitle"].configure(text=s["subtitle"])
        self._dyn["panel_title"].configure(text=s["panel_title"])
        self._dyn["panel_sub"].configure(text=s["panel_sub"])
        self._dyn["summary_head"].configure(text=s["summary_head"])
        self._dyn["kw_head"].configure(text=s["kw_head"])

        self.btn_analyze.configure(text=s["btn_analyze"])
        self.btn_quiz_btn.configure(text=s["btn_quiz"])
        self.btn_clear.configure(text=s["btn_clear"])

        for name in ("summary", "keywords", "quiz"):
            self._tabs[name].configure(text=s[f"tab_{name}"])

        self.status_var.set(s["status_init"])

        current = self.txt_input.get("0.0", "end").strip()
        old_ph_tr = STRINGS["TR"]["placeholder"].strip()
        old_ph_en = STRINGS["EN"]["placeholder"].strip()
        if current in (old_ph_tr, old_ph_en, ""):
            self.txt_input.delete("0.0", "end")
            self.txt_input.insert("0.0", s["placeholder"])
        self._update_wc()

    def _show_tab(self, name: str):
        for n, p in self._panels.items():
            p.place_forget()
        self._panels[name].place(relx=0, rely=0, relwidth=1, relheight=1)

        for n, btn in self._tabs.items():
            if n == name:
                btn.configure(fg_color=COLORS["accent"], text_color="white",
                              border_color=COLORS["accent"])
            else:
                btn.configure(fg_color=COLORS["card"], text_color=COLORS["muted"],
                              border_color=COLORS["border"])

    def _open_settings(self):
        SettingsWindow(self, self._lang,
                       on_save=lambda: self._set_status(STRINGS[self._lang]["api_saved"]))

    def _clear_placeholder(self, _=None):
        s = STRINGS[self._lang]
        current = self.txt_input.get("0.0", "end").strip()
        if current == STRINGS["TR"]["placeholder"].strip() or current == STRINGS["EN"]["placeholder"].strip():
            self.txt_input.delete("0.0", "end")

    # ── Yenilenen Temizleme Fonksiyonu ─────────────────────────────────────────
    def _clear_input_completely(self):
        # 1. Giriş alanını sil
        self.txt_input.delete("0.0", "end")
        self._update_wc()
        
        # 2. Özet, Anahtar kelimeler ve Quiz panellerindeki eski verileri uçur
        self._clear_results()
        
        # 3. Quiz başlatma butonunu tekrar kilitle (çünkü metin yok)
        self.btn_quiz_btn.configure(state="disabled")
        
        # 4. Durum çubuğunu başlangıç moduna getir
        self._set_status(STRINGS[self._lang]["status_init"])
        
        # 5. İmleci tekrar metin kutusuna odakla
        self.txt_input.focus_set()

    def _update_wc(self, _=None):
        text = self.txt_input.get("0.0", "end").strip()
        ph_tr = STRINGS["TR"]["placeholder"].strip()
        ph_en = STRINGS["EN"]["placeholder"].strip()
        if not text or text in (ph_tr, ph_en):
            wc = 0
        else:
            wc = len(text.split())
        self.lbl_wc.configure(text=STRINGS[self._lang]["word_count"].format(n=wc))

    def _get_text(self) -> str:
        return self.txt_input.get("0.0", "end").strip()

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _set_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.btn_analyze.configure(state=state)

    def _start_analysis(self):
        if not load_api_key():
            messagebox.showwarning(
                STRINGS[self._lang]["no_api_title"],
                STRINGS[self._lang]["no_api_msg"]
            )
            self._open_settings()
            return

        text = self._get_text()
        s = STRINGS[self._lang]

        ph_tr = STRINGS["TR"]["placeholder"].strip()
        ph_en = STRINGS["EN"]["placeholder"].strip()
        if not text or text in (ph_tr, ph_en):
            messagebox.showwarning(s["warn_title"], s["warn_no_text"])
            return
        if len(text.split()) < 20:
            messagebox.showwarning(s["warn_title"], s["warn_short"])
            return

        self._set_buttons(False)
        self.btn_quiz_btn.configure(state="disabled")
        self._set_status(s["status_analyzing"])
        self._clear_results()

        threading.Thread(target=self._run_analysis, args=(text,), daemon=True).start()

    def _clear_results(self):
        self.summary_box.configure(state="normal")
        self.summary_box.delete("0.0", "end")
        self.summary_box.configure(state="disabled")
        for w in self.kw_scroll.winfo_children():
            w.destroy()
        for w in self.quiz_scroll.winfo_children():
            w.destroy()
        self._quiz_data = []
        self._answers = {}

    def _run_analysis(self, text: str):
        lang = self._lang
        s = STRINGS[lang]
        try:
            self.after(0, lambda: self._set_status(s["status_summary"]))
            summary = get_summary(text, lang)
            self.after(0, self._display_summary, summary)

            self.after(0, lambda: self._set_status(s["status_keywords"]))
            keywords = get_keywords(text, lang)
            self.after(0, self._display_keywords, keywords)

            self.after(0, lambda: self._set_status(s["status_done"]))
            self.after(0, lambda: self._set_buttons(True))
            self.after(0, lambda: self.btn_quiz_btn.configure(state="normal"))
        except Exception as e:
            err = str(e)[:90]
            self.after(0, lambda: self._set_status(s["status_err"].format(e=err)))
            self.after(0, lambda: self._set_buttons(True))

    def _display_summary(self, text: str):
        self.summary_box.configure(state="normal")
        self.summary_box.delete("0.0", "end")
        self.summary_box.insert("0.0", text)
        self.summary_box.configure(state="disabled")
        self._show_tab("summary")

    def _display_keywords(self, keywords: list):
        for w in self.kw_scroll.winfo_children():
            w.destroy()
        tag_colors = [COLORS["accent"], COLORS["accent2"], COLORS["green"],
                      COLORS["yellow"], "#FF8C42", "#E879F9", "#22D3EE"]
        row = ctk.CTkFrame(self.kw_scroll, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))
        for i, kw in enumerate(keywords):
            color = tag_colors[i % len(tag_colors)]
            ctk.CTkLabel(
                row, text=f"  {kw}  ",
                font=FONT_TAG, text_color="white",
                fg_color=color, corner_radius=16, padx=4, pady=4
            ).grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="w")
        for c in range(3):
            row.columnconfigure(c, weight=1)

    def _start_quiz(self):
        text = self._get_text()
        s = STRINGS[self._lang]
        ph_tr = STRINGS["TR"]["placeholder"].strip()
        ph_en = STRINGS["EN"]["placeholder"].strip()
        if not text or text in (ph_tr, ph_en):
            messagebox.showwarning(s["warn_title"], s["warn_no_analysis"])
            return

        self._show_tab("quiz")
        for w in self.quiz_scroll.winfo_children():
            w.destroy()
        self._quiz_data = []
        self._answers = {}

        ctk.CTkLabel(self.quiz_scroll, text=s["quiz_loading"],
                     font=FONT_HEAD, text_color=COLORS["muted"]
                     ).pack(pady=40)

        self._set_status(s["status_quiz_gen"])
        self.btn_quiz_btn.configure(state="disabled")
        threading.Thread(target=self._run_quiz, args=(text,), daemon=True).start()

    def _run_quiz(self, text: str):
        lang = self._lang
        s = STRINGS[lang]
        try:
            questions = get_quiz(text, lang)
            self.after(0, self._display_quiz, questions)
            self.after(0, lambda: self._set_status(s["status_quiz_ready"]))
        except Exception as e:
            err = str(e)[:90]
            self.after(0, lambda: self._set_status(s["status_quiz_err"].format(e=err)))
        finally:
            self.after(0, lambda: self.btn_quiz_btn.configure(state="normal"))

    def _display_quiz(self, questions: list):
        self._quiz_data = questions
        self._answers = {}
        self._quiz_widgets = []
        for w in self.quiz_scroll.winfo_children():
            w.destroy()
        for i, q in enumerate(questions):
            self._build_question(i, q)

        s = STRINGS[self._lang]
        self._btn_check = ctk.CTkButton(
            self.quiz_scroll, text=s["btn_check"],
            font=FONT_BTN, height=46,
            fg_color=COLORS["accent"], hover_color="#3A7AE4",
            text_color="white", corner_radius=10,
            command=self._check_answers
        )
        self._btn_check.pack(fill="x", padx=4, pady=(8, 4))

        self.quiz_result_label = ctk.CTkLabel(
            self.quiz_scroll, text="", font=FONT_HEAD,
            text_color=COLORS["green"])
        self.quiz_result_label.pack(pady=6)

    def _build_question(self, idx: int, q: dict):
        s = STRINGS[self._lang]
        card = ctk.CTkFrame(
            self.quiz_scroll, fg_color=COLORS["card"],
            corner_radius=12, border_width=1,
            border_color=COLORS["border"]
        )
        card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(card, text=s["question_label"].format(n=idx + 1),
                     font=FONT_SMALL, text_color=COLORS["accent"]
                     ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(card, text=q["question"],
                     font=FONT_BODY, text_color=COLORS["text"],
                     wraplength=580, justify="left", anchor="w"
                     ).pack(anchor="w", padx=16, pady=(0, 10))

        var = ctk.StringVar(value="")
        self._answers[idx] = var
        option_btns = []
        for opt in q["options"]:
            rb = ctk.CTkRadioButton(
                card, text=opt, variable=var, value=opt[0],
                font=FONT_BODY, text_color=COLORS["text"],
                fg_color=COLORS["accent"], hover_color=COLORS["highlight"]
            )
            rb.pack(anchor="w", padx=20, pady=3)
            option_btns.append(rb)

        self._quiz_widgets.append({"card": card, "radios": option_btns, "q": q})
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _check_answers(self):
        correct_count = 0
        total_questions = len(self._quiz_data)
        s = STRINGS[self._lang]

        for idx, widget_info in enumerate(self._quiz_widgets):
            selected_letter = self._answers[idx].get()
            correct_letter = widget_info["q"]["answer"].strip().upper()
            widget_info["card"].configure(border_color=COLORS["border"])

            for rb in widget_info["radios"]:
                opt_val = rb.cget("value")
                if opt_val == correct_letter:
                    rb.configure(text_color=COLORS["green"])
                elif opt_val == selected_letter and selected_letter != correct_letter:
                    rb.configure(text_color=COLORS["red"])
                else:
                    rb.configure(text_color=COLORS["text"])

            if selected_letter == correct_letter:
                correct_count += 1
                widget_info["card"].configure(border_color=COLORS["green"])
            else:
                widget_info["card"].configure(border_color=COLORS["red"])

        percentage = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        emoji = "🎉" if percentage >= 70 else "📚"
        
        score_text = s["quiz_score"].format(e=emoji, s=correct_count, t=total_questions, p=percentage)
        self.quiz_result_label.configure(text=score_text)
        
        status_done_text = s["status_quiz_done"].format(s=correct_count, t=total_questions, p=percentage)
        self._set_status(status_done_text)


if __name__ == "__main__":
    app = SmartStudyApp()
    app.mainloop()