import pytest

from shuup.notify.base import Action
from shuup.notify.script import Step, Context

TEST_STEP_ACTIONS = [
    {
        "identifier": "send_email",
        "language": {
            "constant": "fi"
        },
        "recipient": {
            "variable": "customer_email"
        },
        "template_data": {
            "fi": {
                "body": "Irrelevant body",
                "content_type": "plain",
                "subject": "Irrelevant subject"

            }
        }
    },
    {
        "identifier": "send_email",
        "language": {
            "constant": "fi"
        },
        "recipient": {
            "constant": "some.email@domain.net"
        },
        "template_data": {
            "fi": {
                "body": "Irrelevant body",
                "content_type": "html",
                "subject": "Irrelevant subject"
            }
        }
    }
]


@pytest.mark.django_db
def test_render_template():
    step = Step(
        conditions=(),
        actions=[Action.unserialize(action) for action in TEST_STEP_ACTIONS],
    )
    assert step

    execution_context = Context(variables={
        "customer_phone": "0594036495",
        "language": "fi",
        "customer_email": "some.email@gmail.com"
    })

    step.execute(context=execution_context)
