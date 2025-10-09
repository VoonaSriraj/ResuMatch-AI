"""
Stripe webhook endpoints for handling subscription events
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.activity_log import ActivityLog
from app.services.stripe_service import stripe_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body and signature header
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Construct and verify the webhook event
        try:
            event = stripe_service.construct_webhook_event(payload, sig_header)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook signature verification failed"
            )
        
        # Handle the event
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        logger.info(f"Processing Stripe webhook event: {event_type}")
        
        if event_type == "customer.subscription.created":
            await handle_subscription_created(event_data, db)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data, db)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event_data, db)
        elif event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(event_data, db)
        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(event_data, db)
        elif event_type == "customer.created":
            await handle_customer_created(event_data, db)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

async def handle_subscription_created(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription created event"""
    try:
        customer_id = subscription_data["customer"]
        subscription_id = subscription_data["id"]
        
        # Find user by Stripe customer ID
        user = db.query(User).filter(User.id.in_(
            db.query(Subscription.user_id).filter(
                Subscription.stripe_customer_id == customer_id
            )
        )).first()
        
        if not user:
            logger.warning(f"No user found for Stripe customer: {customer_id}")
            return
        
        # Create or update subscription record
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id
            )
            db.add(subscription)
        else:
            subscription.stripe_subscription_id = subscription_id
            subscription.stripe_customer_id = customer_id
        
        # Update subscription details
        subscription.status = subscription_data["status"]
        subscription.current_period_start = subscription_data["current_period_start"]
        subscription.current_period_end = subscription_data["current_period_end"]
        
        if subscription_data.get("trial_start"):
            subscription.trial_start = subscription_data["trial_start"]
        if subscription_data.get("trial_end"):
            subscription.trial_end = subscription_data["trial_end"]
        
        # Determine plan type from price ID
        price_id = subscription_data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        if price_id:
            subscription.stripe_price_id = price_id
            # Map price ID to plan type (you'll need to configure this)
            subscription.plan_type = map_price_to_plan_type(price_id)
            user.subscription_plan = subscription.plan_type
        
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action_type="subscription_created",
            description=f"Subscription created: {subscription.plan_type}",
            meta_data={
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "plan_type": subscription.plan_type
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Subscription created for user {user.id}: {subscription.plan_type}")
        
    except Exception as e:
        logger.error(f"Failed to handle subscription created: {str(e)}")
        raise

async def handle_subscription_updated(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription updated event"""
    try:
        subscription_id = subscription_data["id"]
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"No subscription found for Stripe ID: {subscription_id}")
            return
        
        # Update subscription details
        subscription.status = subscription_data["status"]
        subscription.current_period_start = subscription_data["current_period_start"]
        subscription.current_period_end = subscription_data["current_period_end"]
        subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
        
        if subscription_data.get("canceled_at"):
            subscription.canceled_at = subscription_data["canceled_at"]
        
        # Update user subscription plan
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            if subscription.status == "active":
                user.subscription_plan = subscription.plan_type
            elif subscription.status in ["canceled", "unpaid", "past_due"]:
                user.subscription_plan = "free"
        
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=subscription.user_id,
            action_type="subscription_updated",
            description=f"Subscription updated: {subscription.status}",
            meta_data={
                "subscription_id": subscription_id,
                "status": subscription.status,
                "plan_type": subscription.plan_type
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Subscription updated for user {subscription.user_id}: {subscription.status}")
        
    except Exception as e:
        logger.error(f"Failed to handle subscription updated: {str(e)}")
        raise

async def handle_subscription_deleted(subscription_data: Dict[str, Any], db: Session):
    """Handle subscription deleted event"""
    try:
        subscription_id = subscription_data["id"]
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if not subscription:
            logger.warning(f"No subscription found for Stripe ID: {subscription_id}")
            return
        
        # Update subscription status
        subscription.status = "canceled"
        subscription.canceled_at = subscription_data.get("canceled_at")
        
        # Update user subscription plan to free
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.subscription_plan = "free"
        
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=subscription.user_id,
            action_type="subscription_canceled",
            description=f"Subscription canceled: {subscription.plan_type}",
            meta_data={
                "subscription_id": subscription_id,
                "plan_type": subscription.plan_type
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Subscription canceled for user {subscription.user_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle subscription deleted: {str(e)}")
        raise

async def handle_payment_succeeded(invoice_data: Dict[str, Any], db: Session):
    """Handle successful payment event"""
    try:
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")
        
        # Find user by customer ID
        user = db.query(User).filter(User.id.in_(
            db.query(Subscription.user_id).filter(
                Subscription.stripe_customer_id == customer_id
            )
        )).first()
        
        if not user:
            logger.warning(f"No user found for Stripe customer: {customer_id}")
            return
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action_type="payment_succeeded",
            description=f"Payment succeeded for subscription",
            meta_data={
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "amount": invoice_data.get("amount_paid"),
                "currency": invoice_data.get("currency")
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Payment succeeded for user {user.id}")
        
    except Exception as e:
        logger.error(f"Failed to handle payment succeeded: {str(e)}")
        raise

async def handle_payment_failed(invoice_data: Dict[str, Any], db: Session):
    """Handle failed payment event"""
    try:
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")
        
        # Find user by customer ID
        user = db.query(User).filter(User.id.in_(
            db.query(Subscription.user_id).filter(
                Subscription.stripe_customer_id == customer_id
            )
        )).first()
        
        if not user:
            logger.warning(f"No user found for Stripe customer: {customer_id}")
            return
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action_type="payment_failed",
            description=f"Payment failed for subscription",
            meta_data={
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "amount": invoice_data.get("amount_due"),
                "currency": invoice_data.get("currency")
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Payment failed for user {user.id}")
        
    except Exception as e:
        logger.error(f"Failed to handle payment failed: {str(e)}")
        raise

async def handle_customer_created(customer_data: Dict[str, Any], db: Session):
    """Handle customer created event"""
    try:
        customer_id = customer_data["id"]
        email = customer_data.get("email")
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning(f"No user found for email: {email}")
            return
        
        # Create subscription record if it doesn't exist
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                stripe_customer_id=customer_id,
                plan_type="free",
                status="incomplete"
            )
            db.add(subscription)
            db.commit()
        
        logger.info(f"Customer created for user {user.id}: {customer_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle customer created: {str(e)}")
        raise

def map_price_to_plan_type(price_id: str) -> str:
    """Map Stripe price ID to plan type"""
    # You'll need to configure this mapping based on your Stripe price IDs
    price_mapping = {
        # Add your actual Stripe price IDs here
        "price_premium_monthly": "premium",
        "price_premium_yearly": "premium",
        "price_enterprise_monthly": "enterprise",
        "price_enterprise_yearly": "enterprise",
    }
    
    return price_mapping.get(price_id, "free")
