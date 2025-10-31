from enum import Enum, auto

from django.templatetags.static import static


class PeerReviewBadge(Enum):
    IRON = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    PLATINUM = auto()


def validate_badge_name_match(badge_name_normalized: str) -> PeerReviewBadge | None:
    matched_badge = None
    for badge in PeerReviewBadge:
        if badge_name_normalized == badge.name:
            matched_badge = badge
            break

    return matched_badge


def get_badge_icon_path(badge_name: str) -> str:
    # Convert the badge name to lowercase and append "_badge.png"
    normalized_name = f"badge_{badge_name.lower()}.png"

    # Use the Django static function to get the correct static path
    icon_path = static(f"img/badges/{normalized_name}")

    return icon_path
