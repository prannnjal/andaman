from django.core.management.base import BaseCommand
from inquiries.models import Hotel, RoomCategory, EventPlace, CustomUser
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample hotels, room categories, and event places for testing'

    def handle(self, *args, **options):
        # Get or create admin user
        admin_user, created = CustomUser.objects.get_or_create(
            mobile_number='7004677366',
            defaults={
                'email': 'admin@example.com',
                'name': 'Admin User',
                'role': 'Admin',
                'is_staff': True,
                'is_active': True,
            }
        )
        
        # Create sample hotels
        hotels_data = [
            {
                'name': 'Taj Hotel Mumbai',
                'address': 'Apollo Bunder, Colaba, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'contact_number': '+91-22-6665-3366',
                'email': 'reservations.mumbai@tajhotels.com',
                'star_rating': 5,
                'amenities': 'WiFi, Swimming Pool, Spa, Restaurant, Business Center',
                'rooms': [
                    {'type': 'Deluxe', 'price': 15000, 'extra_mattress': 2000, 'occupancy': 2},
                    {'type': 'Suite', 'price': 25000, 'extra_mattress': 3000, 'occupancy': 3},
                ]
            },
            {
                'name': 'Hotel Paradise Goa',
                'address': 'Calangute Beach, Goa',
                'city': 'Goa',
                'state': 'Goa',
                'contact_number': '+91-832-227-6776',
                'email': 'info@hotelparadisegoa.com',
                'star_rating': 4,
                'amenities': 'WiFi, Beach Access, Restaurant, Bar, Water Sports',
                'rooms': [
                    {'type': 'Standard', 'price': 8000, 'extra_mattress': 1500, 'occupancy': 2},
                    {'type': 'Deluxe', 'price': 12000, 'extra_mattress': 2000, 'occupancy': 3},
                ]
            },
            {
                'name': 'Kerala Backwaters Resort',
                'address': 'Alleppey Backwaters, Kerala',
                'city': 'Alleppey',
                'state': 'Kerala',
                'contact_number': '+91-477-223-4567',
                'email': 'reservations@keralaresort.com',
                'star_rating': 4,
                'amenities': 'WiFi, Houseboat, Ayurveda Spa, Restaurant, Cultural Shows',
                'rooms': [
                    {'type': 'Standard', 'price': 6000, 'extra_mattress': 1000, 'occupancy': 2},
                    {'type': 'Deluxe', 'price': 9000, 'extra_mattress': 1500, 'occupancy': 3},
                ]
            },
            {
                'name': 'Rajasthan Palace Hotel',
                'address': 'City Palace Road, Jaipur',
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'contact_number': '+91-141-238-5555',
                'email': 'info@rajasthanpalace.com',
                'star_rating': 5,
                'amenities': 'WiFi, Palace Architecture, Pool, Spa, Cultural Programs',
                'rooms': [
                    {'type': 'Standard', 'price': 10000, 'extra_mattress': 2000, 'occupancy': 2},
                    {'type': 'Deluxe', 'price': 15000, 'extra_mattress': 2500, 'occupancy': 3},
                    {'type': 'Suite', 'price': 20000, 'extra_mattress': 3000, 'occupancy': 4},
                ]
            }
        ]
        
        # Create hotels and room categories
        for hotel_data in hotels_data:
            rooms = hotel_data.pop('rooms')
            hotel, created = Hotel.objects.get_or_create(
                name=hotel_data['name'],
                defaults={**hotel_data, 'created_by': admin_user}
            )
            
            if created:
                self.stdout.write(f'Created hotel: {hotel.name}')
            
            # Create room categories
            for room_data in rooms:
                room_category, created = RoomCategory.objects.get_or_create(
                    hotel=hotel,
                    room_type=room_data['type'],
                    defaults={
                        'price_per_night': Decimal(str(room_data['price'])),
                        'extra_mattress_price': Decimal(str(room_data['extra_mattress'])),
                        'max_occupancy': room_data['occupancy'],
                        'description': f'Comfortable {room_data["type"]} room with modern amenities'
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created room category: {room_category.room_type}')
        
        # Create event places
        event_places_data = [
            {
                'name': 'Gateway of India',
                'location': 'Apollo Bunder, Colaba',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'event_type': 'Monument',
                'entry_fee': 0,
                'description': 'Historic monument and popular tourist attraction',
                'contact_number': '+91-22-2204-4040',
                'operating_hours': '24 Hours'
            },
            {
                'name': 'Calangute Beach',
                'location': 'Calangute, North Goa',
                'city': 'Goa',
                'state': 'Goa',
                'event_type': 'Beach',
                'entry_fee': 0,
                'description': 'Popular beach destination with water sports',
                'contact_number': '+91-832-227-6776',
                'operating_hours': '6 AM - 8 PM'
            },
            {
                'name': 'Alleppey Backwaters',
                'location': 'Alleppey Backwaters',
                'city': 'Alleppey',
                'state': 'Kerala',
                'event_type': 'Houseboat Tour',
                'entry_fee': 3000,
                'description': 'Scenic backwater cruise experience',
                'contact_number': '+91-477-223-4567',
                'operating_hours': '9 AM - 6 PM'
            },
            {
                'name': 'City Palace Jaipur',
                'location': 'City Palace Road',
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'event_type': 'Palace',
                'entry_fee': 500,
                'description': 'Historic royal palace with museum',
                'contact_number': '+91-141-238-5555',
                'operating_hours': '9:30 AM - 5 PM'
            },
            {
                'name': 'Elephant Village Jaipur',
                'location': 'Amer Road',
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'event_type': 'Wildlife',
                'entry_fee': 800,
                'description': 'Elephant sanctuary and cultural experience',
                'contact_number': '+91-141-253-0840',
                'operating_hours': '8 AM - 6 PM'
            },
            {
                'name': 'Periyar Wildlife Sanctuary',
                'location': 'Thekkady',
                'city': 'Kerala',
                'state': 'Kerala',
                'event_type': 'Wildlife',
                'entry_fee': 100,
                'description': 'Wildlife sanctuary with boat safari',
                'contact_number': '+91-4869-222-027',
                'operating_hours': '6 AM - 6 PM'
            }
        ]
        
        # Create event places
        for event_data in event_places_data:
            event_place, created = EventPlace.objects.get_or_create(
                name=event_data['name'],
                defaults={**event_data, 'entry_fee': Decimal(str(event_data['entry_fee'])), 'created_by': admin_user}
            )
            
            if created:
                self.stdout.write(f'Created event place: {event_place.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
