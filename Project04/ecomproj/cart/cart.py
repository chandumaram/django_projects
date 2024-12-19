from store.models import Product, Profile

class Cart():
    def __init__(self, request):
        self.session = request.session
        # get request
        self.request = request
        # get the current session key if it exists
        cart = self.session.get('session_key')
        # If the user is new, no session key! Create one.
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
        # Make sure cart is available on all pages of site
        self.cart = cart

    def add(self, productId, quantity):
        product_id = str(productId)
        product_qty = int(quantity)
        # logic
        if product_id in self.cart:
            # pass
            self.cart[product_id] += product_qty
        else:
            # self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = product_qty

        self.session.modified = True

        # Deal with logged in user
        if self.request.user.is_authenticated:
            # get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            # save cart to the profile model
            current_user.update(old_cart=str(carty))

    def update(self, productId, quantity):
        product_id = str(productId)
        product_qty = int(quantity)
        # get cart
        ourcart = self.cart
        # update cart
        ourcart[product_id] = product_qty
        self.session.modified = True

        # Deal with logged in user
        if self.request.user.is_authenticated:
            # get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            # save cart to the profile model
            current_user.update(old_cart=str(carty))

        thing = self.cart
        return thing
    
    def delete(self, productId):
        product_id = str(productId)
        # delete product from cart
        if product_id in self.cart:
            del self.cart[product_id]
        self.session.modified = True

        # Deal with logged in user
        if self.request.user.is_authenticated:
            # get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            # save cart to the profile model
            current_user.update(old_cart=str(carty))

    def __len__(self):
        return len(self.cart)
    
    def get_prods(self):
        # get ids from cart
        products_ids = self.cart.keys()
        # use ids to lookup products in database model
        products = Product.objects.filter(id__in = products_ids)
        return products
    
    def get_quants(self):
        quantities = self.cart
        return quantities
    
    def cart_total(self):
        cartList = self.cart
        total = 0
        for key, value in cartList.items():
            productId = int(key)
            quantity = value
            product = Product.objects.get(id=productId)
            if product:
                if product.is_sale:
                    total += product.sale_price * quantity
                else:
                    total += product.price * quantity
        return total