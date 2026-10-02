"""
PocketSmart AI — Planner Input Models
Pydantic schemas for all three planners.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from enum import Enum


class RoomType(str, Enum):
    living_room = "living_room"
    bedroom = "bedroom"
    kitchen = "kitchen"
    bathroom = "bathroom"
    dining_room = "dining_room"
    study = "study"
    kids_room = "kids_room"
    balcony = "balcony"
    multiple = "multiple"


class HomeStyle(str, Enum):
    modern = "modern"
    traditional = "traditional"
    minimalist = "minimalist"
    bohemian = "bohemian"
    industrial = "industrial"
    scandinavian = "scandinavian"
    rustic = "rustic"
    contemporary = "contemporary"


class HomePlannerInput(BaseModel):
    budget: float
    home_type: str = "Apartment"
    rooms: List[str] = ["Living Room"]
    style: str = "modern"
    num_lights: int = 0
    num_fans: int = 0
    num_tables: int = 0
    num_chairs: int = 0
    need_curtains: bool = False
    need_storage: bool = False
    need_wall_decor: bool = False
    additional_preferences: str = ""

    @field_validator("budget")
    @classmethod
    def budget_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Budget must be a positive number")
        if v > 100_000_000:
            raise ValueError("Budget seems unrealistically high")
        return v

    @field_validator("num_lights", "num_fans", "num_tables", "num_chairs")
    @classmethod
    def quantity_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        if v > 100:
            raise ValueError("Quantity seems unrealistically high")
        return v


class EventType(str, Enum):
    birthday = "birthday"
    wedding = "wedding"
    corporate = "corporate"
    anniversary = "anniversary"
    college_event = "college_event"
    family_gathering = "family_gathering"
    baby_shower = "baby_shower"
    farewell = "farewell"
    other = "other"


class VenueType(str, Enum):
    home = "home"
    banquet_hall = "banquet_hall"
    outdoor = "outdoor"
    restaurant = "restaurant"
    hotel = "hotel"
    rooftop = "rooftop"


class PartyPlannerInput(BaseModel):
    budget: float
    event_type: str = "birthday"
    guest_count: int = 20
    venue_type: str = "home"
    location: str = ""
    food_preference: str = "veg"
    decoration_style: str = "simple"
    need_entertainment: bool = False
    need_accommodation: bool = False
    additional_preferences: str = ""

    @field_validator("budget")
    @classmethod
    def budget_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Budget must be a positive number")
        return v

    @field_validator("guest_count")
    @classmethod
    def guests_valid(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Guest count must be at least 1")
        if v > 10000:
            raise ValueError("Guest count seems unrealistically high")
        return v


class JewelryOccasion(str, Enum):
    wedding = "wedding"
    engagement = "engagement"
    festival = "festival"
    party = "party"
    casual = "casual"
    office = "office"
    anniversary = "anniversary"
    birthday = "birthday"


class JewelryStyle(str, Enum):
    traditional = "traditional"
    contemporary = "contemporary"
    fusion = "fusion"
    minimalist = "minimalist"
    statement = "statement"
    bridal = "bridal"


class JewelryPlannerInput(BaseModel):
    budget: float
    occasion: str = "casual"
    jewelry_types: List[str] = ["necklace"]
    preferred_style: str = "contemporary"
    preferred_metal: str = "gold"
    outfit_description: str = ""
    additional_preferences: str = ""

    @field_validator("budget")
    @classmethod
    def budget_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Budget must be a positive number")
        return v
