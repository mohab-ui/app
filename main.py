from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import MDScrollView
from kivymd.toast import toast
from kivy.utils import platform
from PyPDF2 import PdfReader, PdfWriter
import os
import threading
import requests
import json
from plyer import filechooser

# --- ضع مفتاحك هنا ---
MY_API_KEY = "AIzaSyByJY2EkjgE-s-VyIxdWrQclUkNSONVPFo" 
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={MY_API_KEY}"

SYSTEM_PROMPT = "أنت دكتور مخضرم تشرح لطالب سنة أولى طب. لخص واشرح النص التالي بنقاط واضحة:"

if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE, Permission.INTERNET])

class DrSplitterApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        screen = Screen()
        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=20)
        layout.add_widget(MDTopAppBar(title="Dr. Splitter 🩺"))
        
        self.lbl_status = MDLabel(text="اختر ملف PDF للبدء", halign="center")
        layout.add_widget(self.lbl_status)
        
        layout.add_widget(MDRaisedButton(text="📂 اختر الملف", pos_hint={'center_x': .5}, on_release=self.choose_file))
        
        self.start_page = MDTextField(hint_text="من صفحة", input_type='number')
        self.end_page = MDTextField(hint_text="إلى صفحة", input_type='number')
        layout.add_widget(self.start_page)
        layout.add_widget(self.end_page)
        
        layout.add_widget(MDRaisedButton(text="✂️ قص وشرح", pos_hint={'center_x': .5}, on_release=self.start_process))
        layout.add_widget(MDLabel()) # فراغ
        
        screen.add_widget(layout)
        self.file_path = ""
        self.extracted_text = ""
        return screen

    def choose_file(self, obj):
        filechooser.open_file(on_selection=self.handle_selection, filters=[("*.pdf")])

    def handle_selection(self, selection):
        if selection:
            self.file_path = selection[0]
            self.lbl_status.text = os.path.basename(self.file_path)

    def start_process(self, obj):
        if not self.file_path: return
        threading.Thread(target=self.split_logic).start()

    def split_logic(self):
        try:
            start = int(self.start_page.text) - 1
            end = int(self.end_page.text)
            reader = PdfReader(self.file_path)
            writer = PdfWriter()
            text_content = ""
            for i in range(start, end):
                page = reader.pages[i]
                writer.add_page(page)
                text = page.extract_text()
                if text: text_content += text + "\n"
            
            self.extracted_text = text_content
            save_path = f"/storage/emulated/0/Download/Split_{os.path.basename(self.file_path)}"
            with open(save_path, "wb") as f: writer.write(f)
            self.show_dialog("نجاح", "تم الحفظ. هل تريد الشرح؟", True)
        except Exception as e:
            self.show_dialog("خطأ", str(e), False)

    def show_dialog(self, title, text, ask_ai):
        buttons = [MDFlatButton(text="إغلاق", on_release=lambda x: self.dialog.dismiss())]
        if ask_ai:
            buttons.append(MDRaisedButton(text="نعم اشرح", on_release=self.get_ai_explanation))
        
        from kivy.clock import Clock
        def _open(dt):
            self.dialog = MDDialog(title=title, text=text, buttons=buttons)
            self.dialog.open()
        Clock.schedule_once(_open)

    def get_ai_explanation(self, obj):
        self.dialog.dismiss()
        toast("جاري الاتصال بالدكتور... 🩺")
        threading.Thread(target=self.call_gemini).start()

    def call_gemini(self):
        try:
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n" + self.extracted_text[:10000]}]}]}
            response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                self.show_dialog("الشرح", response.json()['candidates'][0]['content']['parts'][0]['text'], False)
            else:
                self.show_dialog("خطأ", "فشل الاتصال", False)
        except Exception as e:
            self.show_dialog("خطأ", str(e), False)

DrSplitterApp().run()
