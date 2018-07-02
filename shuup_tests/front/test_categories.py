import pytest
from django.core.urlresolvers import reverse
from shuup.testing.factories import (
    get_default_category, get_default_shop
)


@pytest.mark.django_db
def test_category_page(client):
    get_default_shop()
    category = get_default_category()
    response = client.get(
        reverse('shuup:category', kwargs={
            'pk': category.pk,
            'slug': category.slug
            }
        )
    )
    assert b'no such element' not in response.content, 'All items are not rendered correctly'