from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    colors = models.ManyToManyField(Color)
    sizes = models.ManyToManyField(Size)
    
    def __str__(self):
        return self.name

class StockInward(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.product} - {self.quantity}"

class StockOutward(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    removed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.product} - {self.quantity}"

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'color', 'size')

    def __str__(self):
        return f"{self.product} - {self.color} - {self.size}: {self.quantity}"