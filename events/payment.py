import razorpay
from django.conf import settings

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_payment_link(amount, currency='INR'):
    # Create an order in Razorpay
    order = client.order.create(dict(
        amount=amount * 100,  # Convert to paise
        currency=currency,
        payment_capture='1'
    ))
    return order
