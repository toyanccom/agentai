"""Platform implementations for the social agent."""

from .facebook import FacebookPlatform
from .instagram import InstagramPlatform
from .linkedin import LinkedInPlatform
from .pinterest import PinterestPlatform
from .tiktok import TikTokPlatform
from .xcom import XComPlatform

__all__ = [
    "FacebookPlatform",
    "InstagramPlatform",
    "LinkedInPlatform",
    "PinterestPlatform",
    "TikTokPlatform",
    "XComPlatform",
]
