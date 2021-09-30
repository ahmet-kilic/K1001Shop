from django.contrib import admin
from .models import Address, CartProduct, Product, Category, Order
# Register your models here.


admin.site.register(Product)
admin.site.register(Category)
admin.site.register(CartProduct)
admin.site.register(Order)
admin.site.register(Address)
