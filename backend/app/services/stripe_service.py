"""
Stripe integration service for subscription management
"""

import stripe
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

class StripeService:
    def __init__(self):
        self.webhook_secret = settings.stripe_webhook_secret
    
    def create_customer(self, email: str, name: str) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            
            logger.info(f"Stripe customer created: {customer.id}")
            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise Exception(f"Failed to create customer: {str(e)}")
    
    def create_subscription(
        self, 
        customer_id: str, 
        price_id: str,
        trial_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a subscription for a customer"""
        try:
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "payment_settings": {"save_default_payment_method": "on_subscription"},
                "expand": ["latest_invoice.payment_intent"]
            }
            
            if trial_period_days:
                subscription_data["trial_period_days"] = trial_period_days
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            logger.info(f"Stripe subscription created: {subscription.id}")
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_start": subscription.trial_start,
                "trial_end": subscription.trial_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {str(e)}")
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Stripe subscription canceled: {subscription.id}")
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel Stripe subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "subscription_id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_start": subscription.trial_start,
                "trial_end": subscription.trial_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "canceled_at": subscription.canceled_at,
                "price_id": subscription.items.data[0].price.id if subscription.items.data else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get Stripe subscription: {str(e)}")
            raise Exception(f"Failed to get subscription: {str(e)}")
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            
            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get Stripe customer: {str(e)}")
            raise Exception(f"Failed to get customer: {str(e)}")
    
    def create_payment_intent(
        self, 
        amount: int, 
        currency: str = "usd",
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payments"""
        try:
            intent_data = {
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True}
            }
            
            if customer_id:
                intent_data["customer"] = customer_id
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {str(e)}")
            raise Exception(f"Failed to create payment intent: {str(e)}")
    
    def create_checkout_session(
        self,
        price_id: str,
        customer_id: str,
        success_url: str,
        cancel_url: str,
        trial_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session"""
        try:
            session_data = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url
            }
            
            if trial_period_days:
                session_data["subscription_data"] = {
                    "trial_period_days": trial_period_days
                }
            
            session = stripe.checkout.Session.create(**session_data)
            
            return {
                "session_id": session.id,
                "url": session.url,
                "customer_id": customer_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    def list_prices(self) -> Dict[str, Any]:
        """List available subscription prices"""
        try:
            prices = stripe.Price.list(active=True, type="recurring")
            
            price_list = []
            for price in prices.data:
                price_list.append({
                    "price_id": price.id,
                    "nickname": price.nickname,
                    "amount": price.unit_amount,
                    "currency": price.currency,
                    "interval": price.recurring.interval,
                    "interval_count": price.recurring.interval_count,
                    "trial_period_days": price.metadata.get("trial_period_days")
                })
            
            return {"prices": price_list}
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list prices: {str(e)}")
            raise Exception(f"Failed to list prices: {str(e)}")
    
    def construct_webhook_event(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Construct and verify webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload in webhook: {str(e)}")
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in webhook: {str(e)}")
            raise Exception("Invalid signature")

# Global instance
stripe_service = StripeService()
