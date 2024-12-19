from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.db.models.signals import post_save


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=50)
    address1 = models.CharField(max_length=300)
    address2 = models.CharField(max_length=300, null=True, blank=True)
    city = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    zipcode = models.CharField(max_length=10)
    country = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Shipping Address"

    def __str__(self):
        return f'Shipping Address - {self.user} - {self.full_name}'
    
# create a user profile by default when user signs up
def create_shipping(sender, instance, created, **kwargs):
    if created:
        user_shipping = ShippingAddress(user=instance)
        user_shipping.full_name = f'{instance.first_name} {instance.last_name}'
        user_shipping.email = instance.email
        user_shipping.save()

# Automate the profile things
post_save.connect(create_shipping, sender=User)


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=50)
    shipping_address = models.TextField(max_length=15000)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_ordered = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'Order - {str(self.id)}'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f'Order Item - {str(self.id)}'