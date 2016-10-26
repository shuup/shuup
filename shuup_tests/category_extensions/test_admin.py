import pytest
from django.test import override_settings
from shuup.admin.modules.categories.views import CategoryEditView
from shuup.apps.provides import override_provides
from shuup.category_extensions.admin_module.form_parts import AutopopulateFormPart
from shuup.category_extensions.models.category_populator import CategoryPopulator
from shuup.core.models import Category
from shuup.core.models import Manufacturer
from shuup.core.models import ShopProduct
from shuup.testing.factories import get_default_shop, get_default_supplier, create_product, CategoryFactory
from shuup.testing.utils import apply_request_middleware

DEFAULT_POPULATOR_FORMS = {
    "shuup.category_extensions.forms:AttributePopulatorRuleForm",
    "shuup.category_extensions.forms:ManufacturerPopulatorRuleForm",
    "shuup.category_extensions.forms:CreationDatePopulatorRuleForm",
}

def get_form_part_classes(request, view, object):
    initialized_view = view(request=request, kwargs={"pk": object.pk})
    return initialized_view.get_form_part_classes()

@pytest.mark.django_db
def test_category_view_form_parts(rf, admin_user):
    view = CategoryEditView
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    form_parts = get_form_part_classes(request, view, view.model())
    assert AutopopulateFormPart in form_parts


@pytest.mark.django_db
def test_admin_saving(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()

    category = CategoryFactory()
    auto_category = CategoryFactory()
    manufacturer = Manufacturer.objects.create(name="Manufacturer")

    product = create_product("test-product", shop=shop, supplier=supplier)
    product.manufacturer = manufacturer
    product.save()
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(category)
    shop_product.save()

    assert shop_product.categories.count() == 1
    assert auto_category not in shop_product.categories.all()
    with override_settings(LANGUAGES=[("en", "en")]):
        with override_provides("admin_category_form_part", ["shuup.category_extensions.admin_module.form_parts:AutopopulateFormPart"]):
            view = CategoryEditView.as_view()
            data = {
                "base-name__en": auto_category.name,
                "base-status": auto_category.status.value,
                "base-visibility": auto_category.visibility.value,
                "base-ordering": 1,
                "manufacturer_populator-manufacturers": [manufacturer.pk],
                "attribute_populator-product_attr_name": "",
                "attribute_populator-attribute": "",
                "attribute_populator-operator": 1
            }
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            response = view(request, pk=auto_category.pk)
            if hasattr(response, "render"):
                response.render()
            assert response.status_code in [200, 302]
            assert Category.objects.count() == 2
            assert CategoryPopulator.objects.count() == 1

            shop_product = ShopProduct.objects.get(pk=shop_product.pk)
            cp = CategoryPopulator.objects.first()
            assert cp.matches_product(shop_product)
