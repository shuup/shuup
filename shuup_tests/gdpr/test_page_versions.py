import pytest
from django.test import override_settings
from django.utils.translation import activate
from reversion.models import Version

from shuup.gdpr.models import GDPRSettings, GDPRUserConsentDocument
from shuup.gdpr.utils import ensure_gdpr_privacy_policy, create_user_consent_for_all_documents, \
    is_documents_consent_in_sync
from shuup.simple_cms.admin_module.views import PageEditView
from shuup.simple_cms.models import PageType, Page
from shuup.testing import factories
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_page_form(rf, admin_user):
    with override_settings(LANGUAGES=[("en", "en")]):
        activate("en")
        shop = get_default_shop()
        gdpr_settings = GDPRSettings.get_for_shop(shop)
        gdpr_settings.enabled = True
        gdpr_settings.save()

        original_gdpr_page = ensure_gdpr_privacy_policy(shop)
        versions = Version.objects.get_for_object(original_gdpr_page)
        assert len(versions) == 1

        # consent to this with user
        user = factories.create_random_user("en")
        create_user_consent_for_all_documents(shop, user)

        version = versions[0]
        assert GDPRUserConsentDocument.objects.filter(page=original_gdpr_page, version=version).exists()

        assert is_documents_consent_in_sync(shop, user)

        assert Page.objects.count() == 1

        view = PageEditView.as_view()

        # load the page
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        response = view(request, pk=original_gdpr_page.pk)
        assert 200 <= response.status_code < 300

        # update the page
        post_data = {
            "content__en": "test_data",
            "available_from": "",
            "url__en": "test",
            "title__en": "defa",
            "available_to": "",
            "page_type": PageType.REVISIONED.value
        }
        request = apply_request_middleware(rf.post("/", post_data), user=admin_user)
        response = view(request, pk=original_gdpr_page.pk)
        assert response.status_code == 302

        versions = Version.objects.get_for_object(original_gdpr_page)
        assert len(versions) == 4  # saved 4 times in total

        assert not is_documents_consent_in_sync(shop, user)

        create_user_consent_for_all_documents(shop, user)
        assert is_documents_consent_in_sync(shop, user)
