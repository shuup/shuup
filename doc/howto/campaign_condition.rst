Campaign filters and effects
============================

When Shuup determines if a product should have a
discounted price, it looks for the
`DiscountModules <shuup.core.pricing.DiscountModule>` in the system.

Creating a ContextCondition
---------------------------

In this example we'll create a ``ContextCondition`` that matches only if
the temperature is higher than the one merchant has set.

First, we need a ``ContextCondition`` which defines the actual rulesets
when the condition is being matched. Ours is called ``WeatherCondition``.

.. code-block:: python

    from shuup.campaigns.models import ContextCondition


    class WeatherCondition(ContextCondition):
        identifier = "weather_condition"
        name = _("Weather")

        min_temp = models.DecimalField(
            verbose_name=_("min temp"),
            help_text=_("Give the minimum temperature when this condition matches."))

        def matches(self, context):
            current_weather = self._get_weather_from_api()
            return (current_weather.get("current_temperature", 0) >= self.min_temp)

        @property
        def description(self):
            return _("Limit the campaign to given temperature.")

        @property
        def values(self):
            return self.min_temp

        @values.setter
        def values(self, values):
            self.min_temp = values

        def _get_weather_from_api(self):
            # build a fancy api connection
            return {"current_temperature": 10}

.. note:: This api call is simply an example, please don't use
          network-heavy calls in real life as it can render
          your shop unusable. Remember to cache.

Next, we'll need a form that allows the merchant to configure the
condition through the shop admin.

.. code-block:: python

    from example.models import WeatherCondition
    from shuup.campaigns.admin_module.forms._base.BaseRuleModelForm


    class WeatherConditionForm(BaseRuleModelForm):
        class Meta(BaseRuleModelForm.Meta):
            model = WeatherCondition


Next, we'll need to create an ``AppConfig`` for our addon, if it
doesn't already exist. Like many things in Shuup, functionality can be
added through the :doc:`provides system <../ref/provides>`. In this case,
a provide key ``campaign_context_condition`` is being used.

.. code-block:: python

    class WeatherAppConfig(AppConfig):
        name = "example.weathertools"
        verbose_name = "Example Weathertools"
        label = "weathertools"
        provides = {
            "campaign_context_condition": [
                "example.weathertools.admin_module.forms:WeatherConditionForm",
            ],
            ...
        }

.. note:: Define your **form** into this provide and not the actual condition.
