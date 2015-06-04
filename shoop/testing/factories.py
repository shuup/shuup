# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
from .image_generator import generate_image
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import validate_email, ValidationError
from django.db.transaction import atomic
from django.test import RequestFactory
from django.utils.timezone import now
from django_countries.data import COUNTRIES
from factory.django import DjangoModelFactory
from faker.utils.loading import find_available_locales
from filer.models import imagemodels
from shoop.core.contexts import PriceTaxContext
from shoop.core.defaults.order_statuses import create_default_order_statuses
from shoop.core.models import (
    Address, Attribute, AttributeType,
    Category, CategoryStatus, CompanyContact, Contact, ContactGroup,
    Order, OrderLine, OrderLineType, OrderStatus,
    PaymentMethod, PersonContact,
    Product, ProductMedia, ProductMediaKind, ProductType, SalesUnit,
    ShippingMethod, Shop, ShopProduct, ShopStatus, StockBehavior,
    Supplier, SupplierType, TaxClass,
    Tax)
from shoop.core.models.order_lines import OrderLineTax
from shoop.core.order_creator import OrderSource, SourceLine, OrderCreator
from shoop.core.pricing import TaxlessPrice
from shoop.core.shortcuts import update_order_line_from_product
from shoop.default_tax.models import TaxRule
from shoop.testing.text_data import random_title
from shoop.utils.filer import filer_image_from_data
from six import BytesIO
import factory
import factory.fuzzy as fuzzy
import faker
import random
import six
import uuid

DEFAULT_IDENTIFIER = "default"
DEFAULT_NAME = "Default"

DEFAULT_ADDRESS_DATA = dict(
    prefix="Sir",
    name=u"Dog Hello",
    suffix=", Esq.",
    postal_code="K9N",
    street="Woof Ave.",
    city="Dog Fort",
    country="GB"
)

COUNTRY_CODES = sorted(COUNTRIES.keys())


class FuzzyBoolean(fuzzy.BaseFuzzyAttribute):
    def __init__(self, probability, **kwargs):
        self.probability = probability
        super(FuzzyBoolean, self).__init__()

    def fuzz(self):
        return (random.random() < self.probability)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: 'user%s' % n)
    email = factory.Sequence(lambda n: 'user{0}@example.shoop.io'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'test')
    first_name = fuzzy.FuzzyText(length=4, prefix="First Name ")
    last_name = fuzzy.FuzzyText(length=4, prefix="Last Name ")


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = CompanyContact

    name = fuzzy.FuzzyText()
    vat_id = fuzzy.FuzzyText()
    email = factory.Sequence(lambda n: 'company%d@example.shoop.io' % n)


class ShopFactory(DjangoModelFactory):
    class Meta:
        model = Shop

    slug = fuzzy.FuzzyText(prefix="shop-")
    name = fuzzy.FuzzyText(prefix="A Very nice shop ")
    owner = factory.SubFactory(UserFactory)


class ProductTypeFactory(DjangoModelFactory):
    class Meta:
        model = ProductType

    identifier = factory.Sequence(lambda n: 'type_%d' % n)
    name = fuzzy.FuzzyText(length=6, prefix="Product Type ")


class SalesUnitFactory(DjangoModelFactory):
    class Meta:
        model = SalesUnit

    name = fuzzy.FuzzyText(length=12, prefix="Sales Unit ")
    short_name = fuzzy.FuzzyText(length=6, prefix="SU ")


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    identifier = factory.Sequence(lambda n: 'category%d' % n)
    name = fuzzy.FuzzyText(length=6, prefix="Category ")
    status = fuzzy.FuzzyChoice([CategoryStatus.INVISIBLE, CategoryStatus.VISIBLE, CategoryStatus.VISIBLE])

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        # TODO: Fix and re-enable this -- it seems to occasionally create malformed trees
        self.shops = Shop.objects.all()
        if False and create and random.random() < 0.5:
            try:
                parent = Category.objects.all().exclude(pk=self.pk).order_by("?")[:1][0]
            except IndexError:
                parent = None
            if parent:
                Category.objects.move_node(self, parent, position="last-child")


class ShopProductFactory(DjangoModelFactory):
    class Meta:
        model = ShopProduct

    visible = FuzzyBoolean(probability=0.7)
    listed = FuzzyBoolean(probability=0.7)
    purchasable = FuzzyBoolean(probability=0.7)
    searchable = FuzzyBoolean(probability=0.7)


def _generate_product_image(product):
    image = generate_image(512, 512)
    sio = BytesIO()
    image.save(sio, format="JPEG", quality=75)
    filer_file = filer_image_from_data(
        request=None,
        path="ProductImages/Mock",
        file_name="%s.jpg" % product.sku,
        file_data=sio.getvalue(),
        sha1=True
    )
    media = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=filer_file
    )
    media.shops = Shop.objects.all()
    media.save()
    return media


class FuzzyName(fuzzy.FuzzyText):
    def fuzz(self):
        return random_title(prefix=self.prefix, suffix=self.suffix)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    type = factory.LazyAttribute(lambda obj: get_default_product_type())
    sku = fuzzy.FuzzyText(length=10)
    sales_unit = factory.LazyAttribute(lambda obj: get_default_sales_unit())
    tax_class = factory.LazyAttribute(lambda obj: get_default_tax_class())
    profit_center = fuzzy.FuzzyInteger(10000, 99999)
    cost_center = fuzzy.FuzzyInteger(10000, 99999)
    name = FuzzyName()

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        if random.random() < 0.6:
            image = _generate_product_image(self)
            self.primary_image = image
            self.save()
        else:
            image = None

        for shop in Shop.objects.all():
            sp = ShopProductFactory.build()
            sp.shop = shop
            sp.product = self
            sp.shop_primary_image = image
            sp.save()
            sp.suppliers.add(get_default_supplier())
            sp.categories = shop.categories.all()


def get_address(**overrides):
    data = dict(DEFAULT_ADDRESS_DATA, **overrides)
    return Address(**data)


ATTR_SPECS = [
    dict(type=AttributeType.BOOLEAN, identifier="awesome", name="Awesome?"),
    dict(type=AttributeType.INTEGER, identifier="bogomips", name="BogoMIPS"),
    dict(type=AttributeType.DECIMAL, identifier="surface_pressure", name="Surface pressure (kPa)"),
    dict(type=AttributeType.TIMEDELTA, identifier="time_to_finish", name="Time to finish"),
    dict(type=AttributeType.UNTRANSLATED_STRING, identifier="author", name="Author"),
    dict(type=AttributeType.TRANSLATED_STRING, identifier="genre", name="Genre"),
    dict(type=AttributeType.DATE, identifier="release_date", name="Release Date"),
    dict(type=AttributeType.DATETIME, identifier="important_datetime", name="Time and Date of Eschaton"),
]


def default_by_identifier(model):
    return model.objects.filter(identifier=DEFAULT_IDENTIFIER).first()


def get_default_attribute_set():
    for spec in ATTR_SPECS:
        if not Attribute.objects.filter(identifier=spec["identifier"]).exists():
            attr = Attribute.objects.create(**spec)
            assert attr.pk, "attribute was saved"
            assert str(attr) == spec["name"], "attribute has correct name"
    return list(Attribute.objects.filter(identifier__in=set(spec["identifier"] for spec in ATTR_SPECS)))


def get_default_product_type():
    product_type = default_by_identifier(ProductType)
    if not product_type:
        product_type = ProductType.objects.create(identifier=DEFAULT_IDENTIFIER, name="Default Product Type")
        assert product_type.pk, "product type was saved"
        assert (product_type.identifier == "default"), "product type has requested identifier"
        for attr in get_default_attribute_set():
            product_type.attributes.add(attr)
    return product_type


def get_tax(code, name, rate=None, amount=None):
    tax = Tax.objects.filter(code=code).first()
    if not tax:
        tax = Tax.objects.create(
            code=code,
            name=name,
            rate=Decimal(rate) if rate is not None else None,
            amount=Decimal(amount) if amount is not None else None
        )
        assert tax.pk
        assert str(tax) == name
    return tax


def create_default_tax_rule(tax):
    tr = TaxRule.objects.filter(tax=tax).first()
    if not tr:
        tr = TaxRule.objects.create(tax=tax)
        tr.tax_classes.add(get_default_tax_class())
    return tr


def get_default_tax():
    tax = get_tax(DEFAULT_IDENTIFIER, DEFAULT_NAME, Decimal("0.5"))
    create_default_tax_rule(tax)  # Side-effect, but useful
    return tax


def get_test_tax(rate):
    name = "TEST_%s" % rate
    return get_tax(name, name, rate)


def get_default_tax_class():
    tax_class = default_by_identifier(TaxClass)
    if not tax_class:
        tax_class = TaxClass.objects.create(
            identifier=DEFAULT_IDENTIFIER,
            name=DEFAULT_NAME,
            # tax_rate=Decimal("0.5"),
        )
        assert tax_class.pk
        assert str(tax_class) == DEFAULT_NAME
    return tax_class


def get_default_payment_method():
    payment_method = default_by_identifier(PaymentMethod)
    if not payment_method:
        payment_method = PaymentMethod.objects.create(
            identifier=DEFAULT_IDENTIFIER, name=DEFAULT_NAME,
            tax_class=get_default_tax_class(),
        )
        assert payment_method.pk and payment_method.identifier == DEFAULT_IDENTIFIER
    return payment_method


def get_default_shipping_method():
    shipping_method = default_by_identifier(ShippingMethod)
    if not shipping_method:
        shipping_method = ShippingMethod.objects.create(
            identifier=DEFAULT_IDENTIFIER, name=DEFAULT_NAME,
            tax_class=get_default_tax_class(),
        )
        assert shipping_method.pk and shipping_method.identifier == DEFAULT_IDENTIFIER
    return shipping_method


def get_default_customer_group():
    group = default_by_identifier(ContactGroup)
    if not group:
        group = ContactGroup.objects.create(name=DEFAULT_NAME, identifier=DEFAULT_IDENTIFIER)
        assert str(group) == DEFAULT_NAME
    return group


def get_default_supplier():
    supplier = default_by_identifier(Supplier)
    if not supplier:
        supplier = Supplier.objects.create(name=DEFAULT_NAME, identifier=DEFAULT_IDENTIFIER, type=SupplierType.INTERNAL)
        assert str(supplier) == DEFAULT_NAME
    return supplier


def get_default_shop():
    shop = default_by_identifier(Shop)
    if not shop:
        shop = Shop.objects.create(name=DEFAULT_NAME, identifier=DEFAULT_IDENTIFIER, status=ShopStatus.ENABLED)
        assert str(shop) == DEFAULT_NAME
    return shop


def get_default_product():
    product = Product.objects.filter(sku=DEFAULT_IDENTIFIER).first()
    if not product:
        product = create_product(DEFAULT_IDENTIFIER)
        image = get_random_filer_image()
        media = ProductMedia.objects.create(product=product, kind=ProductMediaKind.IMAGE, file=image, enabled=True,
                                            public=True)
        product.primary_image = media
        product.save()
        assert product.primary_image_id
        sp = ShopProduct.objects.create(product=product, shop=get_default_shop())
        sp.suppliers.add(get_default_supplier())
    return product


def get_default_shop_product():
    shop = get_default_shop()
    product = get_default_product()
    shop_product = product.get_shop_instance(shop)
    return shop_product


def get_default_sales_unit():
    unit = default_by_identifier(SalesUnit)
    if not unit:
        unit = SalesUnit.objects.create(
            identifier=DEFAULT_IDENTIFIER,
            decimals=0,
            name=DEFAULT_NAME,
            short_name=DEFAULT_NAME[:3].lower()
        )
        assert str(unit) == DEFAULT_NAME
    return unit


def get_default_category():
    category = default_by_identifier(Category)
    if not category:
        category = Category.objects.create(
            parent=None,
            identifier=DEFAULT_IDENTIFIER,
            name=DEFAULT_NAME,
        )
        assert str(category) == DEFAULT_NAME
    return category


def get_initial_order_status():
    create_default_order_statuses()
    return OrderStatus.objects.get_default_initial()


def get_completed_order_status():
    create_default_order_statuses()
    return OrderStatus.objects.get_default_complete()


def create_product(sku, shop=None, supplier=None):
    product = Product(
        type=get_default_product_type(),
        tax_class=get_default_tax_class(),
        sku=sku,
        name=sku.title(),
        width=100,
        height=100,
        depth=100,
        net_weight=100,
        gross_weight=100,
        sales_unit=get_default_sales_unit(),
        stock_behavior=StockBehavior.UNSTOCKED
    )
    product.full_clean()
    product.save()
    if shop:
        sp = ShopProduct.objects.create(product=product, shop=shop)
        if supplier:
            sp.suppliers.add(supplier)

    return product


def create_empty_order():
    order = Order(
        shop=get_default_shop(),
        payment_method=get_default_payment_method(),
        shipping_method=get_default_shipping_method(),
        billing_address=get_address(name="Mony Doge"),
        shipping_address=get_address(name="Shippy Doge"),
        order_date=now(),
        status=get_initial_order_status()
    )
    return order


def create_order_with_product(product, supplier, quantity, taxless_unit_price, tax_rate=0, n_lines=1):
    order = create_empty_order()
    order.full_clean()
    order.save()
    for x in range(n_lines):
        product_order_line = OrderLine(order=order)
        update_order_line_from_product(request=None, order_line=product_order_line, product=product, quantity=quantity,
                                       supplier=supplier)
        product_order_line.unit_price = TaxlessPrice(taxless_unit_price)
        product_order_line.save()
        product_order_line.taxes.add(
            OrderLineTax.from_tax(get_test_tax(tax_rate), product_order_line.taxless_total_price)
        )
    assert order.get_product_ids_and_quantities()[product.pk] == (quantity * n_lines), "Things got added"
    return order


def get_random_filer_image():
    pil_image = generate_image(256, 256)
    io = six.BytesIO()
    pil_image.save(io, "JPEG", quality=45)
    jpeg_data = io.getvalue()
    name = "%s.jpg" % uuid.uuid4()
    image = imagemodels.Image(name=name)
    image.file.save(name, ContentFile(jpeg_data))
    return image


def get_faker(providers, locale=None):
    providers = [
        ("faker.providers.%s" % provider if ("." not in provider) else provider)
        for provider in providers
        ]
    locale = locale or (random.choice(["en_US"] + list(find_available_locales(providers))))
    fake = faker.Factory.create(locale=locale)
    fake.locale = locale
    fake.locale_language = fake.locale.split("_")[0]
    return fake


def create_random_address(fake=None, **values):
    if not fake:
        fake = get_faker(["person", "address"])
    empty = str  # i.e. constructor for empty string
    values.setdefault("name", fake.name())
    values.setdefault("street", fake.address())
    values.setdefault("city", fake.city())
    values.setdefault("region", getattr(fake, "state", empty)())
    values.setdefault("country", random.choice(COUNTRY_CODES))
    values.setdefault("postal_code", getattr(fake, "postalcode", empty)())
    return Address.objects.create(**values)


def create_random_person(locale=None):
    fake = get_faker(["person", "internet", "address"], locale=locale)
    name = "%s %s" % (fake.first_name(), fake.last_name())
    while True:
        email = fake.email()
        try:  # Faker sometimes generates invalid emails. That's terrible.
            validate_email(email)
        except ValidationError:
            pass
        else:
            break

    phone = fake.phone_number()
    # `prefix`/`suffix` are broken (see https://github.com/joke2k/faker/issues/202)
    # so better just avoid them.
    prefix = ""  # (random.choice(fake.prefix()) if random.random() < 0.05 else "")
    suffix = ""  # (random.choice(fake.suffix()) if random.random() < 0.05 else "")
    language = random.choice(["en", fake.locale_language])
    address = create_random_address(
        fake=fake,
        name=name,
        prefix=prefix,
        suffix=suffix,
        email=email,
        phone=phone,
    )

    return PersonContact.objects.create(
        email=email,
        phone=phone,
        name=name,
        prefix=prefix,
        suffix=suffix,
        default_shipping_address=address,
        default_billing_address=address,
        gender=random.choice("mfuo"),
        language=language
    )


def create_random_company():
    fake = get_faker(["company", "person", "internet"])
    name = fake.company()
    email = fake.email()
    phone = fake.phone_number()
    language = random.choice(["en", fake.locale_language])
    address = create_random_address(name=name, email=email, phone=phone)

    return CompanyContact.objects.create(
        email=email,
        phone=phone,
        name=name,
        default_shipping_address=address,
        default_billing_address=address,
        language=language
    )


def create_random_order(customer=None, products=(), completion_probability=0):
    if not customer:
        customer = Contact.objects.all().order_by("?").first()

    if not customer:
        raise ValueError("No valid contacts")

    request = RequestFactory().get("/")
    request.customer = customer
    context = PriceTaxContext.from_request(request)
    source = OrderSource()
    source.customer = customer
    source.customer_comment = "Mock Order"

    if customer.default_billing_address and customer.default_shipping_address:
        source.billing_address = customer.default_billing_address
        source.shipping_address = customer.default_shipping_address
    else:
        source.billing_address = create_random_address()
        source.shipping_address = create_random_address()
    source.order_date = now() - datetime.timedelta(days=random.uniform(0, 400))

    source.shop = Shop.objects.first()
    source.language = customer.language
    source.status = get_initial_order_status()

    if not products:
        products = list(Product.objects.list_visible(source.shop, customer).order_by("?")[:40])

    source.lines = []
    for i in range(random.randint(3, 10)):
        product = random.choice(products)
        quantity = random.randint(1, 5)
        price = product.get_price(context, quantity=quantity)
        shop_product = product.get_shop_instance(source.shop)
        supplier = shop_product.suppliers.first()
        line = SourceLine(
            type=OrderLineType.PRODUCT,
            product=product,
            supplier=supplier,
            quantity=quantity,
            unit_price=price,
            sku=product.sku,
            text=product.safe_translation_getter("name", any_language=True)
        )
        source.lines.append(line)
    with atomic():
        oc = OrderCreator(request)
        order = oc.create_order(source)
        if random.random() < completion_probability:
            order.create_shipment_of_all_products()
            # also set complete
            order.status = OrderStatus.objects.get_default_complete()
            order.save(update_fields=("status",))
        return order
