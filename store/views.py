from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from .models import CartProduct, Category, Product, Address, Order, Review, Card, Balance
from .forms import AddressForm, ProductQuantityForm, ProductIDQuantityForm, ReviewForm, BalanceForm, ContactForm, RefundForm, CardForm
from cities_light.models import SubRegion
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q, Avg
import decimal
from .mba import get_associated

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

        query = request.GET.get('q')
        if query:
            products = products.filter(name__icontains=query)

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


class ProductView(View):
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        reviews = Review.objects.filter(product=product)

        rec_products = get_associated(product.id)

        try:
            if request.user.is_authenticated:
                user_review = reviews.get(user=request.user)
            else:
                user_review = None
        except ObjectDoesNotExist:
            user_review = None

        purchased = True
        user_orders = Order.objects.filter(user=request.user, ordered=True)
        if user_orders == None:
            purchased = False
        else:
            for o in user_orders:
                try:
                    purchased_product = o.items.get(item=product)
                    purchased = True 
                    break              
                except ObjectDoesNotExist:
                    purchased = False

        rating_percentages = []
        for i in range(5,0,-1):
            # rating_percentages.append(str(reviews.filter(rating=i).count()/review_count * 100) + "%")
            rating_percentages.append((reviews.filter(rating=i).count()))
        # form = ProductQuantityForm()

        reviews = reviews.exclude(comment='').order_by('-updated_at')

        
        paginator = Paginator(reviews, 3)

        # Filter only get with more than 10 reviews but for this project not needed.
        best_rated = Product.objects.filter(category=product.category).annotate(avg_score=Avg('review__rating')).order_by('-avg_score')[0:4]

        context = {
            'object': product,
            'reviews': reviews,
            'percentages': rating_percentages,
            'user_review': user_review,
            'page_count': paginator.num_pages,
            'best_rated': best_rated,
            'purchased': purchased,
            'rec_products': rec_products
        }
        return render(request, 'product.html', context)

    def post(self, request, *args, **kwargs):
        slug = kwargs['slug']
        if 'submit-add' in request.POST:
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
        else:   #Review part
            user = request.user
            item = get_object_or_404(Product, slug=slug)
            review, created = Review.objects.get_or_create(
                product=item,
                user=request.user,
            )
            review.updated_at = timezone.now()
            form = ReviewForm(request.POST,instance=review)
            form.save()
            
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
        print(cart_product)

        if request.POST.get('delete'):
            print(cartproduct_id)
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


class AddAddressView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(request, "Successfully added address.")
            return redirect('my_account')
        return render(request, 'add_address.html', {'form': form , 'user': user})

    def get(self, request):
        form = AddressForm()
        user = request.user
        return render(request, 'add_address.html', {'form': form , 'user': user})

class DeleteAddressView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        id = kwargs['id']
        address = Address.objects.get(id=id)
        address.user = None
        address.save()
        messages.success(request, "Successfully deleted address.")
        return redirect('my_account')

class LoadSubregionsView(LoginRequiredMixin, View):
    def get(self, request):
        region_id = request.GET.get('region_id')
        subregions = SubRegion.objects.filter(region_id=region_id)
        return render(request, 'ajax_form/subregion_dropdown_list.html', { 'subregions': subregions})

class ContactView(View):
    def get(self, request, *args, **kwargs):
        form = ContactForm()
        return render(request, "contact.html", {'form': form})

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = "Website Inquiry"
            body = {
			'first_name': form.cleaned_data['first_name'], 
			'last_name': form.cleaned_data['last_name'], 
			'email': form.cleaned_data['email_address'], 
			'message':form.cleaned_data['message'], 
			}
            message = "\n".join(body.values())
            try:
                send_mail(subject, message, 'admin@example.com', ['admin@example.com']) 
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect ("contact")

class AjaxReviewsView(View):
    def get(self, request):
        pageNo = int(request.GET.get('page'))
        product_id = request.GET.get('product_id')
        pageSize = 3

        starting_number = (pageNo - 1) * pageSize
        ending_number = pageNo * pageSize

        reviews = Review.objects.filter(product_id=product_id).exclude(comment='').order_by('-updated_at')[starting_number:ending_number]

        return render(request, 'ajax_reviews.html', { 'reviews': reviews})
            

class CheckoutView(LoginRequiredMixin, View):
    def order_checkout(self, request, order, address):
        products = order.items.all()
        for product in products:
            if product.quantity > product.item.stock:
                return product.item

        for product in products:
            product.item.stock -= product.quantity
            product.item.save()
        order.ordered = True
        order.shipping_address = address
        order.save()
        request.session['items_total'] = 0
        return "success"

    def get(self, request):

        order = Order.objects.get(user=request.user, ordered=False)
        adresses = Address.objects.filter(user=request.user)
        cards = Card.objects.filter(user=request.user)
        wallet = Balance.objects.get(user=request.user)

        balance_left = round(float(wallet.balance) - order.get_total(),2)
        context = {
            'order' : order,
            'addresses': adresses,
            'cards': cards,
            'wallet': wallet,
            'balance_left': balance_left
        }
        return render(request, 'checkout.html', context)

    def post(self, request):
        address_id = request.POST.get('address')
        order = Order.objects.get(user=request.user, ordered=False)
        user = request.user

        if 'newcard' in request.POST:
            form = CardForm(request.POST)
            if form.is_valid():
                if 'save' in request.POST:
                    card = form.save(commit=False)
                    card.user = request.user
                    card.save()
            else:
                messages.error(request, "Invalid card")
                return redirect('checkout')
        elif 'savedcard' in request.POST:
            if 'radio-button' not in request.POST:
                messages.error(request, "Please choose a card.")
                return redirect('checkout')
        elif 'deletecard' in request.POST:
            if 'radio-button' not in request.POST:
                messages.error(request, "Please choose a card.")
                return redirect('checkout')
            card_id = request.POST.get('radio-button')
            Card.objects.get(id=card_id).delete()
            messages.success(request, "Successfully deleted card.")
            return redirect('checkout')
        else:
            wallet = Balance.objects.get(user=user)
            order_total = order.get_total()
            if wallet.balance < order_total:
                messages.error(request, "Insufficient balance.")
                return redirect('checkout')

            wallet.balance = decimal.Decimal(str(round(float(wallet.balance) - order_total,2)))
            wallet.save()
            self.request.session['balance'] = str(wallet.balance)

        address_id = int(request.POST.get('address'))
        address = Address.objects.get(id=address_id)
        stat = self.order_checkout( request, order, address)
        if not isinstance(stat, str):
            messages.error(request, f"Quantity of {stat.name} exceeds stock, please review your cart.")
            return redirect('checkout')
        else:
            messages.success(request, "Successfully ordered.")
            return redirect('home')

        return redirect('checkout')



class OrdersView(LoginRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.filter(user=request.user, ordered=True)
        context = {
            'orders': orders
        }
        return render(request, 'orders.html', context)

class RefundView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        form = RefundForm()
        order = get_object_or_404(Order, pk=pk)
        return render(request, 'refund.html', {'form': form, 'order': order})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        order = get_object_or_404(Order, pk=pk)
        form = RefundForm(request.POST)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.order = order
            refund.save()
            order.refund_requested = True
            order.save()
            messages.success(request, 'Refund requested.')
            return redirect('orders')
        return render(request, 'refund.html', {'form': form, 'order': order})


class BalanceView(LoginRequiredMixin, View):
    def get(self, request):

        form = BalanceForm()
        cards = Card.objects.filter(user=request.user)
        wallet = Balance.objects.get(user=request.user)
        context = {
            'form': form,
            'cards': cards,
            'wallet': wallet,
        }
        return render(request, 'wallet.html', context)

    def post(self, request):
        user = request.user
        valid = False
        if 'newcard' in request.POST:
            form = CardForm(request.POST)
            if form.is_valid():
                if 'save' in request.POST:
                    card = form.save(commit=False)
                    card.user = request.user
                    card.save()
                valid = True
            else:
                messages.error(request, "Invalid card")
        elif 'savedcard' in request.POST:
            if 'radio-button' not in request.POST:
                messages.error(request, "Please choose a card.")
            else:
                valid = True
        elif 'deletecard' in request.POST:
            if 'radio-button' not in request.POST:
                messages.error(request, "Please choose a card.")
            card_id = request.POST.get('radio-button')
            Card.objects.get(id=card_id).delete()
            messages.success(request, "Successfully deleted card.")
            return redirect('wallet')

        wallet = Balance.objects.get(user=user)
        balance_form = BalanceForm(request.POST)
        if balance_form.is_valid() and valid:
            wallet.balance += balance_form.cleaned_data['amount']
            wallet.balance = decimal.Decimal(str(round(float(wallet.balance),2)))

            wallet.save()
            self.request.session['balance'] = str(wallet.balance)
            messages.success(request, "Successfully loaded balance.")


        cards = Card.objects.filter(user=request.user)
        context = {
            'form': balance_form,
            'cards': cards,
            'wallet': wallet,
        }
        return render(request, 'wallet.html', context)

class AddCardView(LoginRequiredMixin, View):
    def get(self, request):
        form = CardForm()
        return render(request, 'addcard.html', {'form' : form})


    def post(self, request):
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            messages.success(request, 'Card successfully added.')
            return redirect('my_account')
        messages.error(request, 'Invalid Card')
        return render(request, 'addcard.html', {'form' : form})
        

# Create your views here.
