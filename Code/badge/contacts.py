try:
    from typing import Optional, List
except ImportError:
    # we're on an MCU, typing is not available
    pass

from internal_os.contacts import Contact
from internal_os.internalos import InternalOS

internal_os = InternalOS.instance()

def my_contact() -> Optional[Contact]:
    """
    Get the contact information for the current user.
    This is based on the badge ID.
    """
    badge_id = internal_os.get_badge_id_int()
    return internal_os.contacts.get_contact_by_badge_id(badge_id)

def get_contact_by_badge_id(badge_id: int) -> Optional[Contact]:
    """
    Get a contact by their badge ID.
    """
    return internal_os.contacts.get_contact_by_badge_id(badge_id)

def get_contact_by_name(name: str) -> Optional[Contact]:
    """
    Get a contact by their name.
    """
    return internal_os.contacts.get_contact_by_name(name)

def get_all_contacts() -> List[Contact]:
    """
    Get all contacts.
    """
    return internal_os.contacts.get_all_contacts()

def add_contact(contact: Contact) -> None:
    """
    Add a new contact.
    """
    if "contacts:write" in internal_os.apps.get_current_app_repr().permissions:
        # Add the contact
        internal_os.contacts.add_contact(contact.name, contact.pronouns, contact.badge_id, contact.handle)
    else:
        raise RuntimeError("You need the 'contacts:write' permission to add contacts.")
    
def remove_contact_by_badge_id(badge_id: str) -> bool:
    """
    Remove a contact by their badge ID.
    :return: True if the contact was removed, False if not found.
    """
    if "contacts:write" in internal_os.apps.get_current_app_repr().permissions:
        return internal_os.contacts.remove_contact_by_badge_id(badge_id)
    else:
        raise RuntimeError("You need the 'contacts:write' permission to remove contacts.")

def remove_contact_by_name(name: str) -> bool:
    """
    Remove a contact by their name.
    :return: True if the contact was removed, False if not found.
    """
    if "contacts:write" in internal_os.apps.get_current_app_repr().permissions:
        return internal_os.contacts.remove_contact_by_name(name)
    else:
        raise RuntimeError("You need the 'contacts:write' permission to remove contacts.")