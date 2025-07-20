from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

# Import models from all apps
from sourcing.models import SourcingRequest, Quotation, Shipping
from shipments.models import Shipment as ShipmentModel
from warehouse.models import InboundShipment, OutboundShipment
from .models import Notification


def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_staff or user.is_superuser


def get_user_reference_url(user, instance, app_name, notification_type, status=None):
    """Get reference URL based on user role"""
    if is_admin_user(user):
        # Admin URLs
        if app_name == 'shipment':
            return f"/admin/shipments/edit/{instance.id}"
        elif app_name == 'sourcing':
            return f"/admin/sourcing/edit/{instance.id}"
        elif app_name == 'warehouse':
            if isinstance(instance, InboundShipment):
                return f"/admin/warehouse/inbound-shipments/{instance.id}"
            elif isinstance(instance, OutboundShipment):
                return f"/admin/warehouse/outbound-shipments/{instance.id}"
    else:
        # User URLs
        if app_name == 'shipment':
            # Special case for delivery_price_assigned status
            if status == 'delivery_price_assigned':
                return f"/shipments/make-a-payment/{instance.id}"
            return "/shipments"
        elif app_name == 'sourcing':
            # Special case for quotation_sent status
            if status == 'quotation_sent':
                return f"/sourcing/make-a-payment/{instance.id}"
            return "/sourcing"
        elif app_name == 'warehouse':
            return "/warehouse"

    return None

def create_notification(user, app_name, notification_type, title, message, content_object, reference_number=None,
                        reference_url=None, status=None):
    """Helper function to create notifications"""

    # If reference_url not provided, generate based on user role
    if reference_url is None:
        reference_url = get_user_reference_url(user, content_object, app_name, notification_type, status)

    notification = Notification.objects.create(
        user=user,
        app_name=app_name,
        notification_type=notification_type,
        title=title,
        message=message,
        content_object=content_object,
        reference_number=reference_number,
        reference_url=reference_url
    )
    send_realtime_notification(notification)
    return notification


def send_realtime_notification(notification):
    """Send notification through websocket"""
    channel_layer = get_channel_layer()
    if channel_layer:
        notification_data = {
            "id": notification.id,
            "app_name": notification.app_name,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
            "reference_number": notification.reference_number,
            "reference_url": notification.reference_url
        }

        async_to_sync(channel_layer.group_send)(
            f"notifications_{notification.user.id}",
            {
                "type": "send_notification",
                "notification": notification_data
            }
        )


# Sourcing App Signals
@receiver(pre_save, sender=SourcingRequest)
def sourcing_request_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = SourcingRequest.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                create_notification(
                    user=instance.user,
                    app_name='sourcing',
                    notification_type='sourcing_status',
                    title=f"Sourcing Request Status Updated",
                    message=f"Your sourcing request '{instance.name}' (Ref: {instance.reference_number}) status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                    content_object=instance,
                    reference_number=instance.reference_number,
                    status=instance.status  # Pass the status for special URL handling
                )
        except SourcingRequest.DoesNotExist:
            pass


@receiver(post_save, sender=Quotation)
def quotation_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.sourcing_request.user,
            app_name='sourcing',
            notification_type='quotation_created',
            title="New Quotation Received",
            message=f"A quotation has been created for '{instance.sourcing_request.name}' (Ref: {instance.sourcing_request.reference_number})",
            content_object=instance.sourcing_request,  # Use sourcing request as content object
            reference_number=instance.sourcing_request.reference_number
        )
    else:
        create_notification(
            user=instance.sourcing_request.user,
            app_name='sourcing',
            notification_type='quotation_updated',
            title="Quotation Updated",
            message=f"The quotation for '{instance.sourcing_request.name}' has been updated",
            content_object=instance.sourcing_request,  # Use sourcing request as content object
            reference_number=instance.sourcing_request.reference_number
        )


# Shipment App Signals
@receiver(post_save, sender=ShipmentModel)
def shipment_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.user,
            app_name='shipment',
            notification_type='shipment_created',
            title="Shipment Created",
            message=f"New shipment {instance.shipment_number} has been created",
            content_object=instance,
            reference_number=instance.shipment_number
        )
    else:
        # Check for status changes
        if instance.pk:
            try:
                old_instance = ShipmentModel.objects.get(pk=instance.pk)

                if old_instance.status != instance.status:
                    create_notification(
                        user=instance.user,
                        app_name='shipment',
                        notification_type='shipment_status',
                        title="Shipment Status Updated",
                        message=f"Shipment {instance.shipment_number} status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                        content_object=instance,
                        reference_number=instance.shipment_number
                    )

                # Check for tracking number addition
                if not old_instance.tracking_number and instance.tracking_number:
                    create_notification(
                        user=instance.user,
                        app_name='shipment',
                        notification_type='shipment_tracking',
                        title="Tracking Number Added",
                        message=f"Tracking number {instance.tracking_number} has been added to shipment {instance.shipment_number}",
                        content_object=instance,
                        reference_number=instance.shipment_number
                    )

                # Check for delivery price assignment when payment is still pending
                if (not old_instance.delivery_price and instance.delivery_price and
                        instance.payment_status == 'pending'):
                    create_notification(
                        user=instance.user,
                        app_name='shipment',
                        notification_type='delivery_price_assigned',
                        title="Delivery Price Available",
                        message=f"Delivery price has been assigned for shipment {instance.shipment_number}. Please proceed with payment.",
                        content_object=instance,
                        reference_number=instance.shipment_number,
                        status='delivery_price_assigned'  # Pass status for special URL handling
                    )

            except ShipmentModel.DoesNotExist:
                pass

# Warehouse App Signals
@receiver(post_save, sender=InboundShipment)
def inbound_shipment_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.user,
            app_name='warehouse',
            notification_type='inbound_created',
            title="Inbound Shipment Created",
            message=f"New inbound shipment {instance.shipment_number} to {instance.warehouse.country} warehouse",
            content_object=instance,
            reference_number=instance.shipment_number
        )
    else:
        if instance.pk:
            try:
                old_instance = InboundShipment.objects.get(pk=instance.pk)
                if old_instance.status != instance.status:
                    create_notification(
                        user=instance.user,
                        app_name='warehouse',
                        notification_type='inbound_status',
                        title="Inbound Shipment Status Updated",
                        message=f"Inbound shipment {instance.shipment_number} status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                        content_object=instance,
                        reference_number=instance.shipment_number
                    )
            except InboundShipment.DoesNotExist:
                pass


@receiver(post_save, sender=OutboundShipment)
def outbound_shipment_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.user,
            app_name='warehouse',
            notification_type='outbound_created',
            title="Outbound Shipment Created",
            message=f"New outbound shipment {instance.shipment_number} for {instance.customer_name}",
            content_object=instance,
            reference_number=instance.shipment_number
        )
    else:
        if instance.pk:
            try:
                old_instance = OutboundShipment.objects.get(pk=instance.pk)
                if old_instance.status != instance.status:
                    create_notification(
                        user=instance.user,
                        app_name='warehouse',
                        notification_type='outbound_status',
                        title="Outbound Shipment Status Updated",
                        message=f"Outbound shipment {instance.shipment_number} status changed from {old_instance.get_status_display()} to {instance.get_status_display()}",
                        content_object=instance,
                        reference_number=instance.shipment_number
                    )
            except OutboundShipment.DoesNotExist:
                pass