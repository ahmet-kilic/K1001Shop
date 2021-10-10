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

    def get_rating(self):
        rate_avg = Review.objects.filter(product=self).aggregate(average=Avg('rating'))
        avg = 0
        if rate_avg['average'] is not None:
            avg = round(float(rate_avg['average']),1)
        return avg

    def count_reviews(self):
        counts = Review.objects.filter(product=self).aggregate(count=Count('id'))
        count = 0
        if counts['count'] is not None:
            count = int(counts['count'])
        return count

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=40, blank=True)
    comment = models.TextField(blank=True)
    rating = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class Address(models.Model):
    name = models.CharField(max_length=100, default="Default Address")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=400)
    region = models.ForeignKey(Region, on_delete=models.RESTRICT, verbose_name="City")
    subregion = models.ForeignKey(SubRegion, on_delete=models.RESTRICT, verbose_name="Province", null=True)
    zip = models.CharField(max_length=50)
    
    def __str__(self):
        return f' {self.name}, {self.address}, {self.region} / {self.subregion}'
        
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
            return round(self.get_total_discount_item_price(),2)
        return round(self.get_total_item_price(),2)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartProduct)
    date_ordered = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_cart_items(self):
        return self.items.all()

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return round(total,2)

class Balance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Balance {self.balance} of user {self.user}"

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pk}"


class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=60)
    number = models.CharField(max_length=20, default="0000 0000 0000 0000")
    cvc = models.CharField(max_length=20)
    expiry = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username}'s card with number {self.number}"