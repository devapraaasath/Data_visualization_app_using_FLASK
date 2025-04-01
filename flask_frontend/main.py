from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
import requests
import json
import os
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
import pandas as pd
from datetime import datetime

# Load the KV file
Builder.load_file("design.kv")

# Color constants
DARK_BG = '#1A1A1A'
HEADER_BG = '#2D2D2D'
BORDER_COLOR = '#404040'
SUCCESS_COLOR = '#2ECC71'
ERROR_COLOR = '#E74C3C'
BUTTON_BG = '#4A90E2'

class AnimatedButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation = None
        self.bind(on_press=self.on_press_animation)
        self.bind(on_release=self.on_release_animation)

    def on_press_animation(self, instance):
        self.animation = Animation(scale_x=0.95, scale_y=0.95, duration=0.1).start(self)

    def on_release_animation(self, instance):
        self.animation = Animation(scale_x=1, scale_y=1, duration=0.1).start(self)

class ModernPopup(Popup):
    def __init__(self, title, message, is_error=False):
        super().__init__()
        self.title = title
        self.background_color = get_color_from_hex(HEADER_BG)
        self.size_hint = (None, None)
        self.size = (dp(300), dp(180))
        
        # Create content layout
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Add message label
        content.add_widget(Label(
            text=message,
            color=get_color_from_hex(ERROR_COLOR if is_error else SUCCESS_COLOR)
        ))
        
        # Add close button
        close_button = Button(
            text='Close',
            size_hint_y=None,
            height=dp(40),
            background_color=get_color_from_hex(BORDER_COLOR)
        )
        close_button.bind(on_press=self.dismiss)
        content.add_widget(close_button)
        
        self.content = content

class ImageUploadPopup(ModalView):
    def __init__(self, file_id, on_upload_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.8)
        self.file_id = file_id
        self.on_upload_complete = on_upload_complete
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Title
        layout.add_widget(Label(
            text='Upload Image',
            size_hint_y=0.1,
            bold=True,
            font_size=dp(18)
        ))
        
        # File chooser
        self.file_chooser = FileChooserIconView(
            size_hint_y=0.7,
            filters=['*.png', '*.jpg', '*.jpeg', '*.gif']
        )
        layout.add_widget(self.file_chooser)
        
        # Buttons
        buttons = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        cancel_btn = Button(
            text='Cancel',
            size_hint_x=0.5,
            on_press=self.dismiss
        )
        buttons.add_widget(cancel_btn)
        
        upload_btn = Button(
            text='Upload Image',
            size_hint_x=0.5,
            background_color=(0.2, 0.7, 0.3, 1),
            on_press=self.upload_image
        )
        buttons.add_widget(upload_btn)
        
        layout.add_widget(buttons)
        self.add_widget(layout)
    
    def upload_image(self, instance):
        if not self.file_chooser.selection:
            Popup(
                title='Error',
                content=Label(text='No image selected'),
                size_hint=(0.6, 0.4)
            ).open()
            return
        
        image_path = self.file_chooser.selection[0]
        files = {'image': open(image_path, 'rb')}
        data = {'file_id': self.file_id}
        
        try:
            response = requests.post(
                'http://127.0.0.1:5000/upload_image',
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                Popup(
                    title='Success',
                    content=Label(text='Image uploaded successfully'),
                    size_hint=(0.6, 0.4)
                ).open()
                self.dismiss()
                if self.on_upload_complete:
                    self.on_upload_complete()
            else:
                Popup(
                    title='Error',
                    content=Label(text=f'Upload failed: {response.json().get("error", "")}'),
                    size_hint=(0.6, 0.4)
                ).open()
        except Exception as e:
            Popup(
                title='Error',
                content=Label(text=f'Connection error: {str(e)}'),
                size_hint=(0.6, 0.4)
            ).open()

class DataCell(BoxLayout):
    def __init__(self, text='', is_header=False):
        super().__init__()
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(45) if is_header else dp(100)
        self.padding = dp(8)
        
        # Add background and border
        with self.canvas.before:
            Color(*get_color_from_hex(HEADER_BG if is_header else DARK_BG))
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(*get_color_from_hex(BORDER_COLOR))
            self.border = Rectangle(
                pos=(self.pos[0] + 1, self.pos[1] + 1),
                size=(self.size[0] - 2, self.size[1] - 2)
            )
        
        # Add label
        self.add_widget(Label(
            text=str(text),
            bold=is_header,
            color=get_color_from_hex('#FFFFFF' if is_header else '#B3B3B3'),
            font_size=dp(14) if is_header else dp(12)
        ))
        
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.pos = (self.pos[0] + 1, self.pos[1] + 1)
        self.border.size = (self.size[0] - 2, self.size[1] - 2)

class ImageCell(BoxLayout):
    def __init__(self, image_url):
        super().__init__()
        self.orientation = 'vertical'
        self.padding = dp(8)
        
        # Create image container
        image_container = BoxLayout(orientation='vertical', padding=dp(5))
        
        # Add image
        image = AsyncImage(
            source=image_url if image_url.startswith(('http://', 'https://')) 
                   else f'http://127.0.0.1:5000/get_image/{image_url}',
            size_hint_y=1,
            allow_stretch=True,
            keep_ratio=True
        )
        image_container.add_widget(image)
        self.add_widget(image_container)

class TableRow(BoxLayout):
    def __init__(self, is_header=False):
        super().__init__()
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50) if is_header else dp(120)
        self.spacing = dp(2)
        self.padding = dp(2)
        
        with self.canvas.before:
            Color(*get_color_from_hex(HEADER_BG if is_header else DARK_BG))
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size

class FileUploader(BoxLayout):
    def __init__(self):
        super().__init__()
        self.current_file_id = None
        self.setup_search()
    
    def setup_search(self):
        self.ids.search_input.bind(on_text_validate=self.search_data)
        self.ids.search_button.bind(on_press=self.search_data)
        self.ids.search_input.hint_text = "Search in data..."
        self.ids.search_input.hint_text_color = get_color_from_hex('#808080')
        self.ids.search_input.foreground_color = [1, 1, 1, 1]
    
    def on_search_text(self, instance, value):
        """Called when text changes in the search input"""
        instance.foreground_color = [1, 1, 1, 1]  # White text
        instance.hint_text_color = [0.5, 0.5, 0.5, 1]  # Gray hint text
    
    def upload_file(self):
        if not self.ids.file_chooser.selection:
            self.show_error_popup("Please select a file first")
            return
        
        file_path = self.ids.file_chooser.selection[0]
        if not file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
            self.show_error_popup("Please select a CSV or Excel file")
            return
        
        try:
            with open(file_path, 'rb') as file:
                response = requests.post('http://127.0.0.1:5000/upload', files={'file': file})
            
            if response.status_code == 200:
                self.show_success_popup("File uploaded successfully!")
                self.process_file(response.json()['filename'])
                self.enable_search()
            else:
                self.show_error_popup(f"Error uploading file: {response.text}")
        except Exception as e:
            self.show_error_popup(f"Error: {str(e)}")
    
    def enable_search(self):
        self.ids.search_input.disabled = False
        self.ids.search_button.disabled = False
    
    def process_file(self, filename):
        try:
            response = requests.post('http://127.0.0.1:5000/process', json={'filename': filename})
            if response.status_code == 200:
                self.current_file_id = response.json()['file_id']
                self.fetch_data(self.current_file_id)
            else:
                self.show_error_popup(f'File processing failed: {response.json().get("error", "")}')
        except Exception as e:
            self.show_error_popup(f'Connection error: {str(e)}')
    
    def fetch_data(self, file_id):
        try:
            response = requests.get(f'http://127.0.0.1:5000/get_data/{file_id}')
            if response.status_code == 200:
                self.display_data(response.json()['data'])
            else:
                self.show_error_popup(f'Failed to fetch data: {response.json().get("error", "")}')
        except Exception as e:
            self.show_error_popup(f'Connection error: {str(e)}')
    
    def display_data(self, data):
        # Setup table
        table = self.ids.table_layout
        table.clear_widgets()
        
        if not data:
            return
        
        headers = list(data[0].keys())
        table.width = max(len(headers) * dp(150), Window.width - dp(40))
        
        # Add header row
        header_row = TableRow(is_header=True)
        header_row.width = table.width
        for header in headers:
            cell = DataCell(text=header, is_header=True)
            cell.size_hint_x = 1 / len(headers)
            header_row.add_widget(cell)
        table.add_widget(header_row)
        
        # Add data rows with animation
        for i, item in enumerate(data):
            row = TableRow()
            row.width = table.width
            
            for key in headers:
                cell = (ImageCell(item.get(key, '')) if key == 'image_url' 
                       else DataCell(text=item.get(key, '')))
                cell.size_hint_x = 1 / len(headers)
                row.add_widget(cell)
            
            table.add_widget(row)
            anim = Animation(opacity=1, duration=0.3)
            Clock.schedule_once(lambda dt, r=row: anim.start(r), i * 0.05)
    
    def search_data(self, instance=None):
        if not self.current_file_id:
            self.show_error_popup("Please upload a file first")
            return
        
        query = self.ids.search_input.text.strip()
        if not query:
            self.show_error_popup("Please enter a search query")
            return
        
        try:
            response = requests.post('http://127.0.0.1:5000/search', 
                                  json={'file_id': self.current_file_id, 'query': query})
            if response.status_code == 200:
                results = response.json()['results']
                if not results:
                    self.show_error_popup("No results found")
                    return
                self.display_data(results)
            else:
                self.show_error_popup(f"Error searching data: {response.text}")
        except Exception as e:
            self.show_error_popup(f"Error: {str(e)}")
    
    def show_error_popup(self, message):
        ModernPopup(title='Error', message=message, is_error=True).open()
    
    def show_success_popup(self, message):
        ModernPopup(title='Success', message=message, is_error=False).open()

class DataApp(App):
    def build(self):
        Window.size = (1200, 800)
        Window.clearcolor = get_color_from_hex(DARK_BG)
        return FileUploader()

if __name__ == '__main__':
    DataApp().run()