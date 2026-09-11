from app.services.app_settings_service import AppSettingsService


def test_fresh_install_uses_kickerkasse_as_app_name(db_session):
    settings = AppSettingsService(db_session).get_or_create_settings()

    assert settings.app_name == "KickerKasse"


def test_existing_app_name_is_preserved(db_session):
    service = AppSettingsService(db_session)
    settings = service.get_or_create_settings()
    settings.app_name = "Vereinskasse"
    db_session.commit()

    assert service.get_or_create_settings().app_name == "Vereinskasse"
