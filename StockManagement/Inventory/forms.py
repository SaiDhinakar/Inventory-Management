from django import forms
from .models import Product, Color, Size

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'colors', 'sizes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'colors': forms.CheckboxSelectMultiple(),
            'sizes': forms.CheckboxSelectMultiple()
        }

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }