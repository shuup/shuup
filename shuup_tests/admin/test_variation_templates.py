import pytest
import json

from shuup.admin.modules.products.forms import VariationVariablesDataForm
from shuup.core.models import ProductVariationVariable, ProductVariationVariableValue
from shuup.testing.factories import create_product
from shuup_tests.utils import printable_gibberish
from shuup.testing.factories import get_default_shop, create_random_user
from shuup.testing.utils import apply_request_middleware

var_data = [{"pk":"$0.3","identifier":"","names":{"en":"Size"},
"values":[{"pk":"$0.8","identifier":"","texts":{"en":"X"}},
{"pk":"$0.1","identifier":"","texts":{"en":"S"}}]}]

@pytest.mark.django_db
def test_variation_template_creation(rf):
    shop = get_default_shop()
    parent = create_product(printable_gibberish())
    user = create_random_user(is_superuser = True, is_staff = True)
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    form = VariationVariablesDataForm(parent_product=parent, request=request)
    form.request = request
    form.cleaned_data = {'data' : "{}"}
    form.save()
    assert form.get_variation_templates() == []
    form.cleaned_data = {'data': '{"variable_values": []}', 'template_name': 'Test'}
    form.save()
    var_template = form.get_variation_templates()[0]
    assert len(form.get_variation_templates()) == 1
    template_identifier = var_template.get('identifier')
    template_data = {'data': '{"variable_values":' + str(var_data) + '}', 'template_name': 'Test'}
    form.cleaned_data = {'data': json.dumps({"variable_values": var_data, 'template_identifier' : template_identifier}), 'template_name': '' }
    form.save()
    assert len(form.get_variation_templates()) == 1
    var_template = form.get_variation_templates()[0]
    assert var_template["data"] == var_data


def test_variation_activation(rf):
    shop = get_default_shop()
    parent = create_product(printable_gibberish(), shop=shop)
    user = create_random_user(is_superuser = True, is_staff = True)
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    form = VariationVariablesDataForm(parent_product=parent, request=request)
    assert len(ProductVariationVariable.objects.all()) == 0  # Assert no active Variations are present
    assert form.get_variation_templates() == []  # Assert no templates exist (yet)

    var_data_dict = {
        'data': json.dumps({"variable_values": var_data}),
        'template_name': ''
    }  # Base skeleton
    form.cleaned_data = var_data_dict
    form.is_valid()
    form.save()

    assert len(ProductVariationVariable.objects.filter(product=parent)) == 1 # Size
    assert len(ProductVariationVariableValue.objects.all()) == 2  # X,S

    var_data_one_value = [{
        "pk": "$0.3",
        "identifier": "",
        "names": {"en": "Size"},
        "values": [{
            "pk": "$0.8",
            "identifier": "",
            "texts": {
                "en": "X"
            }
        }]
    }] #  Delete one value
    var_data_dict['data'] = json.dumps({"variable_values": var_data_one_value})
    form.cleaned_data = var_data_dict
    form.save()

    assert len(ProductVariationVariable.objects.filter(product=parent)) == 1
    assert len(ProductVariationVariableValue.objects.all()) == 1
    var_data_dict["template_name"] = printable_gibberish()  # Create template
    form.save()

    assert len(ProductVariationVariable.objects.filter(product=parent)) == 1
    assert len(ProductVariationVariableValue.objects.all()) == 1
    assert len(form.get_variation_templates()) == 1

    template_identifier = form.get_variation_templates()[0].get('identifier')
    # dict with template identifier which contains only one ProductVariationVariableValue data
    one_value_dict = json.dumps({"variable_values": var_data_one_value, 'template_identifier' : template_identifier})
    two_values_dict = json.dumps({"variable_values": var_data, 'template_identifier' : template_identifier})  # Has two PVVV
    var_data_dict['data'] = two_values_dict
    var_data_dict['template_name'] = ''
    form.cleaned_data = var_data_dict
    form.save()

    assert len(ProductVariationVariable.objects.filter(product=parent)) == 1
    assert len(ProductVariationVariableValue.objects.all()) == 2
    var_template_data = form.get_variation_templates()[0].get("data")
    assert var_template_data == var_data
    var_data_dict['data'] = one_value_dict
    form.cleaned_data = var_data_dict
    form.save()

    assert len(ProductVariationVariable.objects.filter(product=parent)) == 1
    assert len(ProductVariationVariableValue.objects.all()) == 1
    var_template_data = form.get_variation_templates()[0].get("data")
    assert var_template_data == var_data_one_value
