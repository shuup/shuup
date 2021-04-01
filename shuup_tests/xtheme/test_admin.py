from shuup.apps.provides import override_provides
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme.admin_module.views import ThemeConfigDetailView, ThemeConfigView, ThemeGuideTemplateView
from shuup_tests.xtheme.utils import FauxTheme


def test_config_view(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = ThemeConfigView.as_view()(request)
    assert response.status_code == 200


def test_config_view2(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    with override_provides("xtheme", ["shuup_tests.xtheme.utils:FauxTheme"]):
        response = ThemeConfigDetailView.as_view()(request, theme_identifier=FauxTheme.identifier)
        assert response.status_code == 200
