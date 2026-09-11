"""Tests for automatic username generation when a role/login is assigned to a member.

Covers Roadmap-UX-Sicherheit.md, Punkt 2 ("BENUTZERNAME-KOLLISIONEN"):
  Vorname.Nachname, on collision Vorname.Nachname.2, .3, ... and the generated username is
  surfaced back on the member so the UI can show it in a success message.
"""
from app.services.member_service import MemberService


def _create_member_with_role(service, first_name, last_name, *, role="VERKAUF", password="Initial123!"):
    return service.create_member(
        first_name=first_name,
        last_name=last_name,
        role=role,
        account_password=password,
    )


class TestUsernameCollisionHandling:
    def test_first_account_uses_plain_vorname_nachname(self, db_session):
        service = MemberService(db_session)
        member = _create_member_with_role(service, "Max", "Mustermann")

        linked_user = service.user_repo.get_by_member_id(member.id)
        assert linked_user.username == "Max.Mustermann"

    def test_second_colliding_account_gets_suffix_2(self, db_session):
        service = MemberService(db_session)
        _create_member_with_role(service, "Max", "Mustermann")
        second_member = _create_member_with_role(service, "Max", "Mustermann")

        linked_user = service.user_repo.get_by_member_id(second_member.id)
        assert linked_user.username == "Max.Mustermann.2"

    def test_third_colliding_account_gets_suffix_3(self, db_session):
        service = MemberService(db_session)
        _create_member_with_role(service, "Max", "Mustermann")
        _create_member_with_role(service, "Max", "Mustermann")
        third_member = _create_member_with_role(service, "Max", "Mustermann")

        linked_user = service.user_repo.get_by_member_id(third_member.id)
        assert linked_user.username == "Max.Mustermann.3"

    def test_generated_username_is_returned_via_member_response_fields(self, db_session):
        # The API layer (schemas/member.py) reads the linked user's username back onto the
        # member response as `account_username` / `has_user_account`, which is what the
        # frontend uses to show the "Benutzerkonto angelegt mit Benutzername ..." message.
        service = MemberService(db_session)
        member = _create_member_with_role(service, "Erika", "Musterfrau")

        linked_user = service.user_repo.get_by_member_id(member.id)
        assert linked_user is not None
        assert linked_user.username == "Erika.Musterfrau"
        assert linked_user.role.value == "VERKAUF"
