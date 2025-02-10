from django.urls import path
from django.contrib.auth.decorators import login_required, user_passes_test
from . import views

def is_superuser(user):
    return user.is_superuser

urlpatterns = [
    path('', login_required(views.dashboard), name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Superuser only paths
    path('product/add/', user_passes_test(is_superuser)(views.product_add), name='product_add'),
    path('color/add/', user_passes_test(is_superuser)(views.color_add), name='color_add'),
    path('size/add/', user_passes_test(is_superuser)(views.size_add), name='size_add'),
    path('delete_page/', views.delete_page, name='delete_page'),
    path('delete/<str:item_type>/<int:item_id>/', views.delete_item, name='delete_item'),

    
    # Normal user paths
    path('stock/in/', login_required(views.stock_in), name='stock_in'),
    path('stock/out/', login_required(views.stock_out), name='stock_out'),
    path('stock/list/', login_required(views.stock_list), name='stock_list'),
    path('get-product-options/', views.get_product_options, name='get_product_options'),
    path('export_stock/', views.export_stock, name='export_stock'),

]

# Custom error views
handler404 = 'Inventory.views.custom_404'  # Adjust 'myapp' to your app's name
handler500 = 'Inventory.views.custom_500'  # Adjust 'myapp' to your app's name