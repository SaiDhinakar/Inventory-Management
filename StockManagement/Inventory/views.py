from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from .models import Product, Color, Size, StockInward, StockOutward, Stock
from django.contrib.auth.models import User
from .forms import ProductForm, ColorForm, SizeForm
from django.db.models.functions import Coalesce
from itertools import chain
from operator import attrgetter
import logging
from django.http import JsonResponse
import csv
from django.http import HttpResponse
from .models import Stock, Product, Color, Size

logger = logging.getLogger(__name__)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Please fill all fields')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    try:
        # Convert filter parameters to integers if present
        product_id = int(request.GET.get('product')) if request.GET.get('product') else None
        color_id = int(request.GET.get('color')) if request.GET.get('color') else None
        size_id = int(request.GET.get('size')) if request.GET.get('size') else None

        stock_data = []
        products = Product.objects.all()
        
        if product_id:
            products = products.filter(id=product_id)

        for product in products:
            colors = product.colors.all()
            if color_id:
                colors = colors.filter(id=color_id)
                
            for color in colors:
                sizes = product.sizes.all()
                if size_id:
                    sizes = sizes.filter(id=size_id)
                    
                for size in sizes:
                    stock = Stock.objects.filter(
                        product=product,
                        color=color,
                        size=size
                    ).first()

                    current_qty = stock.quantity if stock else 0
                    
                    stock_data.append({
                        'product': product,
                        'color': color,
                        'size': size,
                        'quantity': current_qty,
                        'status': 'danger' if current_qty == 0 else 'warning' if current_qty < 10 else 'success'
                    })

        context = {
            'stocks': stock_data,
            'products': Product.objects.all(),
            'colors': Color.objects.all(),
            'sizes': Size.objects.all(),
            'selected_product': product_id,
            'selected_color': color_id,
            'selected_size': size_id,
        }
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return render(request, 'dashboard.html', {'stocks': []})

@login_required 
def stock_in(request):
    try:
        if request.method == 'POST':
            product = get_object_or_404(Product, id=request.POST.get('product'))
            color = get_object_or_404(Color, id=request.POST.get('color'))
            size = get_object_or_404(Size, id=request.POST.get('size'))
            quantity = int(request.POST.get('quantity'))

            print(f"Adding stock: {product}-{color}-{size}: {quantity}")

            # Create inward entry
            inward = StockInward.objects.create(
                product=product,
                color=color,
                size=size,
                quantity=quantity,
                added_by=request.user
            )
            print(f"Created inward entry: {inward.id}")

            # Update or create stock record
            stock, created = Stock.objects.get_or_create(
                product=product,
                color=color,
                size=size,
                defaults={'quantity': quantity}
            )
            
            if not created:
                stock.quantity += quantity
                stock.save()
            
            print(f"Updated stock: {stock.product}-{stock.color}-{stock.size}: {stock.quantity}")

            messages.success(request, f'Stock added successfully. Current quantity: {stock.quantity}')
            return redirect('dashboard')

    except Exception as e:
        print(f"Error in stock_in: {str(e)}")
        messages.error(request, f'Error adding stock: {str(e)}')
        return redirect('stock_in')

    context = {
        'products': Product.objects.all(),
        'colors': Color.objects.all(),
        'sizes': Size.objects.all(),
        'is_stock_in': True
    }
    return render(request, 'stock_form.html', context)

@login_required
def stock_out(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST.get('product'))
        color = get_object_or_404(Color, id=request.POST.get('color'))
        size = get_object_or_404(Size, id=request.POST.get('size'))
        quantity = int(request.POST.get('quantity'))

        # Check if enough stock exists
        stock = Stock.objects.filter(
            product=product,
            color=color,
            size=size,
            quantity__gte=quantity
        ).first()

        if not stock:
            messages.error(request, 'Not enough stock available')
            return redirect('stock_out')

        # Create outward entry
        StockOutward.objects.create(
            product=product,
            color=color,
            size=size,
            quantity=quantity,
            removed_by=request.user
        )

        # Update stock
        stock.quantity -= quantity
        stock.save()

        messages.success(request, 'Stock removed successfully')
        return redirect('dashboard')

    context = {
        'products': Product.objects.all(),
        'colors': Color.objects.all(),
        'sizes': Size.objects.all(),
        'is_stock_in': False
    }
    return render(request, 'stock_form.html', context)

@user_passes_test(lambda u: u.is_superuser)
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        colors = request.POST.getlist('colors')
        sizes = request.POST.getlist('sizes')

        product = Product.objects.create(name=name, description=description)
        product.colors.set(colors)
        product.sizes.set(sizes)
        messages.success(request, 'Product added successfully')
        return redirect('dashboard')

    context = {
        'colors': Color.objects.all(),
        'sizes': Size.objects.all(),
        'item_type': 'Product'
    }
    return render(request, 'add_item.html', context)

@user_passes_test(lambda u: u.is_superuser)
def color_add(request):
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Color added successfully')
            return redirect('dashboard')
    else:
        form = ColorForm()
    return render(request, 'add_item.html', {'form': form, 'item_type': 'Color'})

@user_passes_test(lambda u: u.is_superuser)
def size_add(request):
    if request.method == 'POST':
        form = SizeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Size added successfully')
            return redirect('dashboard')
    else:
        form = SizeForm()
    return render(request, 'add_item.html', {'form': form, 'item_type': 'Size'})

@login_required
def stock_list(request):
    # Get both inward and outward transactions
    inward = StockInward.objects.all().order_by('-date')
    outward = StockOutward.objects.all().order_by('-date')
    
    # Combine and sort both querysets
    combined_stocks = sorted(
        chain(inward, outward),
        key=attrgetter('date'),
        reverse=True
    )
    
    context = {
        'stocks': combined_stocks
    }
    return render(request, 'stock_list.html', context)

@user_passes_test(lambda u: u.is_superuser)
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

@login_required
def get_product_options(request):
    product_id = request.GET.get('product_id')
    if product_id:
        product = Product.objects.get(id=product_id)
        colors = [{'id': c.id, 'name': c.name} for c in product.colors.all()]
        sizes = [{'id': s.id, 'name': s.name} for s in product.sizes.all()]
        return JsonResponse({'colors': colors, 'sizes': sizes})
    return JsonResponse({'colors': [], 'sizes': []})

def delete_item(request, item_type, item_id):
    """
    View to handle the deletion of a product, color, or size.
    """
    # Check if the user has permission to delete (optional)
    if not request.user.is_superuser:
        messages.error(request, "You must be superuser in to delete items.")
        return redirect('dashboard')  # Redirect to login page if not logged in

    if item_type == 'product':
        item = get_object_or_404(Product, pk=item_id)
        item.delete()
        messages.success(request, f"The product '{item.name}' has been deleted successfully.")

    elif item_type == 'color':
        item = get_object_or_404(Color, pk=item_id)
        item.delete()
        messages.success(request, f"The color '{item.name}' has been deleted successfully.")

    elif item_type == 'size':
        item = get_object_or_404(Size, pk=item_id)
        item.delete()
        messages.success(request, f"The size '{item.name}' has been deleted successfully.")

    else:
        messages.error(request, "Invalid item type.")
        return redirect('dashboard')  # Redirect to a safe page

    return redirect('delete_page')  # Redirect to a relevant page (like the homepage or item list)

def delete_page(request):
    # Assuming you have all the necessary objects
    products = Product.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    return render(request, 'delete_item.html', {
        'products': products,
        'colors': colors,
        'sizes': sizes,
    })

import csv
from django.http import HttpResponse
from .models import Stock, Product, Color, Size

def export_stock(request):
    # Get filter parameters
    product_id = request.GET.get('product')
    color_id = request.GET.get('color')
    size_id = request.GET.get('size')

    # Filter the stock data based on the filters provided
    stocks = Stock.objects.all()

    if product_id and product_id.isdigit():  # Ensure product_id is not None and is a valid number
        stocks = stocks.filter(product_id=product_id)
    if color_id and color_id.isdigit():  # Ensure color_id is not None and is a valid number
        stocks = stocks.filter(color_id=color_id)
    if size_id and size_id.isdigit():  # Ensure size_id is not None and is a valid number
        stocks = stocks.filter(size_id=size_id)

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_data.csv"'
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Product', 'Color', 'Size', 'Available Stock'])

    # Write the data rows
    for stock in stocks:
        writer.writerow([stock.product.name, stock.color.name, stock.size.name, stock.quantity])

    return response


# Define custom error views
def custom_404(request, exception):
    return render(request, '404.html')

def custom_500(request):
    return render(request, '500.html')

