from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class HelloApp(App):
    def build(self):
        self.title = "Hello - Kivy"
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.label = Label(text="Hello, World!")
        button = Button(text="Click me")
        button.bind(on_press=self.on_click)
        layout.add_widget(self.label)
        layout.add_widget(button)
        return layout

    def on_click(self, instance):
        self.label.text = "Button clicked!"


HelloApp().run()
