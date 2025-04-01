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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex('#2D2D2D')
        self.title_color = get_color_from_hex('#FFFFFF')
        self.separator_color = get_color_from_hex('#404040')
        self.size_hint = (None, None)
        self.auto_dismiss = False
        
        # Create custom title bar with close button
        title_bar = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), 0],
            spacing=dp(10)
        )
        
        # Add title label
        title_label = Label(
            text=self.title,
            color=self.title_color,
            bold=True,
            font_size=dp(16),
            size_hint_x=0.9
        )
        title_bar.add_widget(title_label)
        
        # Add close button
        close_button = Button(
            text='×',
            size_hint_x=None,
            width=dp(30),
            background_color=get_color_from_hex('#404040'),
            color=get_color_from_hex('#FFFFFF'),
            bold=True,
            font_size=dp(20),
            on_press=self.dismiss
        )
        title_bar.add_widget(close_button)
        
        # Replace default title bar with custom one
        self._title = title_bar

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
    def __init__(self, text='', is_header=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(45) if is_header else dp(100)
        self.padding = dp(10)
        
        # Initialize rectangle variables
        self.rect = None
        self.border = None
        self.hover_color = None
        
        # Add background color with subtle border and hover effect
        with self.canvas.before:
            if is_header:
                Color(*get_color_from_hex('#2D2D2D'))
            else:
                Color(*get_color_from_hex('#1A1A1A'))
            self.rect = Rectangle(size=self.size, pos=self.pos)
            
            # Add subtle border
            Color(*get_color_from_hex('#404040'))
            self.border = Rectangle(
                size=(self.size[0] - dp(2), self.size[1] - dp(2)),
                pos=(self.pos[0] + dp(1), self.pos[1] + dp(1))
            )
            
            # Add hover effect using color opacity
            if not is_header:
                self.hover_color = Color(*get_color_from_hex('#2A2A2A'))
                self.hover_rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # Add label with better styling
        lbl = Label(
            text=str(text),
            bold=is_header,
            color=get_color_from_hex('#FFFFFF') if is_header else get_color_from_hex('#B3B3B3'),
            halign='center',
            valign='middle',
            text_size=(dp(120), None),
            font_size=dp(14) if is_header else dp(12)
        )
        self.add_widget(lbl)
    
    def _update_rect(self, instance, value):
        if hasattr(self, 'rect') and self.rect:
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        if hasattr(self, 'border') and self.border:
            self.border.pos = (instance.pos[0] + dp(1), instance.pos[1] + dp(1))
            self.border.size = (instance.size[0] - dp(2), instance.size[1] - dp(2))
        if hasattr(self, 'hover_rect') and self.hover_rect:
            self.hover_rect.pos = instance.pos
            self.hover_rect.size = instance.size

class ImageCell(BoxLayout):
    def __init__(self, image_url, file_id=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(8)
        self.spacing = dp(5)
        self.file_id = file_id
        self.image_url = image_url

        # Create image container with shadow effect
        self.image_container = BoxLayout(
            orientation='vertical',
            size_hint_y=1,
            padding=dp(5)
        )
        
        # Add image with animation and better styling
        self.image = AsyncImage(
            source=self.image_url if self.image_url.startswith(('http://', 'https://')) else f'http://127.0.0.1:5000/get_image/{self.image_url}',
            size_hint_y=1,
            allow_stretch=True,
            keep_ratio=True,
            nocache=True
        )
        
        # Add background and border to image container
        with self.image_container.canvas.before:
            Color(*get_color_from_hex('#2D2D2D'))
            self.rect = Rectangle(size=self.image_container.size, pos=self.image_container.pos)
            
            # Add subtle border
            Color(*get_color_from_hex('#404040'))
            self.border = Rectangle(
                size=(self.image_container.size[0] - dp(2), self.image_container.size[1] - dp(2)),
                pos=(self.image_container.pos[0] + dp(1), self.image_container.pos[1] + dp(1))
            )
        
        self.image_container.bind(size=self._update_rect, pos=self._update_rect)
        self.image_container.add_widget(self.image)
        self.add_widget(self.image_container)
    
    def _update_rect(self, instance, value):
        if self.rect:
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        if self.border:
            self.border.pos = (instance.pos[0] + dp(1), instance.pos[1] + dp(1))
            self.border.size = (instance.size[0] - dp(2), instance.size[1] - dp(2))

class TableRow(BoxLayout):
    def __init__(self, is_header=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50) if is_header else dp(120)
        self.size_hint_x = None
        self.spacing = dp(2)
        self.padding = dp(2)
        
        # Initialize rectangle variables
        self.rect = None
        self.border = None
        self.hover_color = None
        
        # Add better styling with subtle border and hover effect
        with self.canvas.before:
            if is_header:
                Color(*get_color_from_hex('#2D2D2D'))
            else:
                Color(*get_color_from_hex('#1A1A1A'))
            self.rect = Rectangle(size=self.size, pos=self.pos)
            
            # Add subtle border
            Color(*get_color_from_hex('#404040'))
            self.border = Rectangle(
                size=(self.size[0] - dp(2), self.size[1] - dp(2)),
                pos=(self.pos[0] + dp(1), self.pos[1] + dp(1))
            )
            
            # Add hover effect using color opacity
            if not is_header:
                self.hover_color = Color(*get_color_from_hex('#2A2A2A'))
                self.hover_rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        if hasattr(self, 'rect') and self.rect:
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        if hasattr(self, 'border') and self.border:
            self.border.pos = (instance.pos[0] + dp(1), instance.pos[1] + dp(1))
            self.border.size = (instance.size[0] - dp(2), instance.size[1] - dp(2))
        if hasattr(self, 'hover_rect') and self.hover_rect:
            self.hover_rect.pos = instance.pos
            self.hover_rect.size = instance.size

class FileUploader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_file_id = None
        self.upload_animation = None
        self.search_animation = None
        self.setup_animations()
        self.bind(on_parent=self.on_parent)
        
        # Set search input placeholder and bind to on_text_validate
        self.ids.search_input.hint_text = "Search in data..."
        self.ids.search_input.hint_text_color = get_color_from_hex('#808080')
        self.ids.search_input.bind(on_text_validate=self.search_data)
        self.ids.search_button.bind(on_press=self.search_data)

    def setup_animations(self):
        # Fade in animation for the main layout
        self.opacity = 0
        self.animation = Animation(opacity=1, duration=0.5)
        self.animation.start(self)

    def on_parent(self, instance, parent):
        if parent:
            self.animation.start(self)

    def upload_file(self):
        if not self.ids.file_chooser.selection:
            self.show_error_popup("Please select a file first")
            return

        file_path = self.ids.file_chooser.selection[0]
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension not in ['.csv', '.xlsx', '.xls']:
            self.show_error_popup("Please select a CSV or Excel file")
            return

        # Upload animation
        self.upload_animation = Animation(
            background_color=get_color_from_hex('#357ABD'),
            duration=0.2
        ) + Animation(
            background_color=get_color_from_hex('#4A90E2'),
            duration=0.2
        )
        self.upload_animation.start(self.ids.upload_button)

        try:
            files = {'file': open(file_path, 'rb')}
            response = requests.post('http://127.0.0.1:5000/upload', files=files)
            
            if response.status_code == 200:
                self.show_success_popup("File uploaded successfully!")
                self.process_file(response.json().get('filename'))
                # Enable search functionality after successful upload
                self.ids.search_input.disabled = False
                self.ids.search_button.disabled = False
            else:
                self.show_error_popup(f"Error uploading file: {response.text}")
        except Exception as e:
            self.show_error_popup(f"Error: {str(e)}")

    def process_file(self, filename):
        try:
            response = requests.post('http://127.0.0.1:5000/process', json={'filename': filename})
            
            if response.status_code == 200:
                result = response.json()
                self.current_file_id = result.get('file_id')
                self.fetch_data(self.current_file_id)
            else:
                self.show_error_popup(f'File processing failed: {response.json().get("error", "")}')
        except Exception as e:
            self.show_error_popup(f'Connection error: {str(e)}')
    
    def fetch_data(self, file_id):
        try:
            response = requests.get(f'http://127.0.0.1:5000/get_data/{file_id}')
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                self.display_data(data)
            else:
                self.show_error_popup(f'Failed to fetch data: {response.json().get("error", "")}')
        except Exception as e:
            self.show_error_popup(f'Connection error: {str(e)}')
    
    def display_data(self, data):
        # Update the label with the number of records
        self.ids.result_label.text = f'Displaying {len(data)} records'
        
        # Clear the table layout
        table_layout = self.ids.table_layout
        table_layout.clear_widgets()
        
        if not data:
            table_layout.add_widget(Label(
                text="No data available",
                color=get_color_from_hex('#B3B3B3'),
                size_hint_y=None,
                height=dp(50)
            ))
            return
            
        # Get headers from first record
        headers = list(data[0].keys())
        
        # Calculate total width based on number of columns (150dp per column)
        total_width = len(headers) * dp(150)
        
        # Set table width to calculated width or window width, whichever is larger
        table_layout.width = max(total_width, Window.width - dp(40))
        
        # Create header row
        header_row = TableRow(is_header=True)
        header_row.width = table_layout.width
        
        for header in headers:
            cell = DataCell(text=header, is_header=True)
            cell.size_hint_x = 1 / len(headers)
            header_row.add_widget(cell)
        
        table_layout.add_widget(header_row)
        
        # Add data rows with animation
        for i, item in enumerate(data):
            row = TableRow()
            row.width = table_layout.width
            row.opacity = 0  # Start with 0 opacity for animation
            
            for key in headers:
                if key == 'image_url':
                    cell = ImageCell(
                        image_url=item.get(key, ''),
                        file_id=self.current_file_id
                    )
                else:
                    cell = DataCell(text=item.get(key, ''))
                cell.size_hint_x = 1 / len(headers)
                row.add_widget(cell)
            
            table_layout.add_widget(row)
            
            # Animate row appearance with proper delay
            anim = Animation(opacity=1, duration=0.3)
            Clock.schedule_once(lambda dt, r=row: anim.start(r), i * 0.05)
        
        # Update scroll view
        self.ids.table_scroll.scroll_y = 0
        self.ids.table_scroll.scroll_x = 0
    
    def show_image_upload(self, file_id):
        popup = ImageUploadPopup(
            file_id=file_id,
            on_upload_complete=lambda: self.fetch_data(self.current_file_id)
        )
        popup.open()
    
    def search_data(self, instance=None):
        if not self.current_file_id:
            self.show_error_popup("Please upload a file first")
            return
            
        query = self.ids.search_input.text.strip()
        if not query:
            self.show_error_popup("Please enter a search query")
            return

        # Search animation
        self.search_animation = Animation(
            background_color=get_color_from_hex('#27AE60'),
            duration=0.2
        ) + Animation(
            background_color=get_color_from_hex('#2ECC71'),
            duration=0.2
        )
        self.search_animation.start(self.ids.search_button)

        try:
            response = requests.post('http://127.0.0.1:5000/search', 
                                    json={'file_id': self.current_file_id, 'query': query})
            if response.status_code == 200:
                search_results = response.json().get('results', [])
                if not search_results:
                    self.show_error_popup("No results found")
                    return
                self.display_data(search_results)
            else:
                self.show_error_popup(f"Error searching data: {response.text}")
        except Exception as e:
            self.show_error_popup(f"Error: {str(e)}")
    
    def show_error_popup(self, message):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Add message label with better styling
        content.add_widget(Label(
            text=message,
            color=get_color_from_hex('#E74C3C'),
            size_hint_y=0.7,
            text_size=(dp(250), None),
            halign='center',
            valign='middle'
        ))
        
        # Add close button with better styling
        close_button = Button(
            text='Close',
            size_hint_y=None,
            height=dp(40),
            background_color=get_color_from_hex('#404040'),
            color=get_color_from_hex('#FFFFFF'),
            bold=True,
            font_size=dp(14)
        )
        content.add_widget(close_button)
        
        popup = ModernPopup(
            title='Error',
            content=content,
            size_hint=(None, None),
            size=(dp(300), dp(180)),
            auto_dismiss=True
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def show_success_popup(self, message):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Add message label with better styling
        content.add_widget(Label(
            text=message,
            color=get_color_from_hex('#2ECC71'),
            size_hint_y=0.7,
            text_size=(dp(250), None),
            halign='center',
            valign='middle'
        ))
        
        # Add close button with better styling
        close_button = Button(
            text='Close',
            size_hint_y=None,
            height=dp(40),
            background_color=get_color_from_hex('#4A90E2'),
            color=get_color_from_hex('#FFFFFF'),
            bold=True,
            font_size=dp(14)
        )
        content.add_widget(close_button)
        
        popup = ModernPopup(
            title='Success',
            content=content,
            size_hint=(None, None),
            size=(dp(300), dp(180)),
            auto_dismiss=True
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def on_search_text(self, instance, value):
        # This method will be called whenever the text changes
        # We can use this to update the search input's appearance
        instance.foreground_color = [1, 1, 1, 1]  # White text
        instance.hint_text_color = [0.5, 0.5, 0.5, 1]  # Gray hint text

class DataApp(App):
    def build(self):
        # Set window size and title
        Window.size = (1200, 800)
        Window.clearcolor = get_color_from_hex('#1A1A1A')
        return FileUploader()

if __name__ == '__main__':
    DataApp().run()