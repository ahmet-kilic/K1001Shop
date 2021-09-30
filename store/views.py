from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from .models import CartProduct, Category, Product, Address, Order
from .forms import AddressForm, ProductQuantityForm, ProductIDQuantityForm
from cities_light.models import SubRegion
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages

class HomeView(View):
    def get(self, request, *args, **kwargs):
        if 'slug' in kwargs:
            category_slug = kwargs['slug']
        else:
            category_slug = None
        category = None
        if category_slug:
            categories = Category.objects.all()
            category = get_object_or_404(Category, slug=category_slug)
            products = Product.objects.filter(category=category)
        else:
            categories = Category.objects.all()
            products = Product.objects.all()

        page = request.GET.get('page', 1)

        paginator = Paginator(products, 8)
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        context = {
            'categories': categories,
            'category': category,
            'products': products,
        }

        return render(request, 'home.html', context)

class AboutView(View):
    def get(self, request):
        return render(request, 'about.html')

class ContactView(View):
    def get(self, request):
        return render(request, 'contact.html')

class ProductView(View):
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        # form = ProductQuantityForm()
        context = {
            'object': get_object_or_404(Product, slug=slug),
           # 'form': form,
        }
        return render(request, 'product.html', context)

    def post(self, request, *args, **kwargs):
        slug = kwargs['slug']
        form = ProductQuantityForm(request.POST)
        item = get_object_or_404(Product, slug=slug)
        quantity = int(form.data['quantity'])

        if quantity > item.stock:
            messages.error(request, 'Chosen quantity exceeds stock.')
            return redirect('product', slug=slug)

        if quantity <= 0:
            messages.error(request, 'Choose a valid amount.')
            return redirect('product', slug=slug)

        order_item, created = CartProduct.objects.get_or_create(
            item=item,
            user=request.user,
            ordered=False
        )

        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                if (order_item.quantity + quantity) > item.stock:
                    messages.error(request, 'You already have this item in cart. Total quantity exceeds stock.')
                    return redirect('product', slug=slug)

                order_item.quantity += quantity
                order_item.save()
            else:
                order_item.quantity = quantity
                order_item.save()
                order.items.add(order_item)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                user=request.user, date_ordered=ordered_date)
            order_item.quantity = quantity
            order.items.add(order_item)
        request.session['items_total'] = order.items.count()
        messages.success(request, 'Item added to cart.')
        return redirect('product', slug=slug)

class CartView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        try:
            order = Order.objects.get(user=user, ordered=False)
            request.session['items_total'] = order.items.count()
        except ObjectDoesNotExist:
            order = None
            request.session['items_total'] = 0

        context = {
            'order' : order,
        }
        
        return render(request, 'cart.html', context)

    def post(self, request):
        
        form = ProductIDQuantityForm(request.POST)
        cartproduct_id = int(form.data['product_id'])
        quantity = int(form.data['quantity'])
        cart_product = get_object_or_404(CartProduct, id=cartproduct_id)

        if request.POST.get('delete'):
            cart_product.delete()
            messages.success(request, f'{cart_product.item.name} successfully deleted from cart.')
            request.session['items_total'] -= 1
            return redirect('cart')

        elif request.POST.get('change'):
            if quantity > cart_product.item.stock:
                messages.error(request, 'Chosen quantity exceeds stock.')
                return redirect('cart')

            if quantity <= 0:
                messages.error(request, 'Choose a valid amount.')
                return redirect('cart')

            cart_product.quantity = quantity
            cart_product.save()

            messages.success(request, f'Quantity of {cart_product.item.name} successfully changed.')
            return redirect('cart')




class AddressesView(LoginRequiredMixin, View):
    def get(self,request):
        user = request.user
        addresses = Address.objects.filter(user=user)
        context = {
            'addresses': addresses
        }
        return render(request, 'addresses.html', context)

class AddAddressView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
        return redirect('addresses')

    def get(self, request):
        form = AddressForm()
        user = request.user
        return render(request, 'add_address.html', {'form': form , 'user': user})

class DeleteAddressView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        id = kwargs['id']
        Address.objects.filter(id=id).delete()
        return redirect('addresses')

class LoadSubregionsView(LoginRequiredMixin, View):
    def get(self, request):
        region_id = request.GET.get('region_id')
        subregions = SubRegion.objects.filter(region_id=region_id)
        return render(request, 'ajax_form/subregion_dropdown_list.html', { 'subregions': subregions})


# class AddToCartView(LoginRequiredMixin, View):
#     def get


# Create your views here.
