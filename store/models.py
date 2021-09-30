from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django_countries.fields import CountryField
from cities_light.models import City, Region, SubRegion
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    ordering = models.IntegerField(default=1, verbose_name="Category Ordering")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ("ordering",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("category_home", kwargs={ "slug": self.slug} )


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    stock = models.IntegerField(default=0)
    slug = models.SlugField()
    discount_price = models.FloatField(blank=True, null=True)
    image = models.ImageField(upload_to='product_pic', default='default.jpg')
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    date_added = models.DateTimeField(
        auto_now_add=True, verbose_name="Product Date Added"
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("-date_added",)
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product", kwargs={ "slug": self.slug})    

    # def get_rating(self):
    #     rate_avg = Review.objects.filter(product=self).aggregate(average=Avg('rate'))
    #     avg = 0
    #     if rate_avg['average'] is not None:
    #         avg = float(rate_avg['average'])
    #     return avg

    # def count_reviews(self):
    #     counts = Review.objects.filter(product=self).aggregate(count=Count('id'))
    #     count = 0
    #     if counts['count'] is not None:
    #         count = int(counts['count'])
    #     return count

# class Review(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     subject = models.CharField(max_length=50, blank=True)
#     comment = models.CharField(max_length=400, blank=True)
#     rate = models.IntegerField(default=1)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.subject


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=400)
    region = models.ForeignKey(Region, on_delete=models.RESTRICT)
    subregion = models.ForeignKey(SubRegion, on_delete=models.RESTRICT, null=True)
    zip = models.CharField(max_length=50)
    
    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = "Addresses"


class CartProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.name}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartProduct)
    date_ordered = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_cart_items(self):
        return self.items.all()

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total