from clicksign.resources.template import Template
from clicksign.resources.template_field import TemplateField
from tests.support.http_mock import make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TMPL_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def tmpl_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "templates",
        "attributes": {"name": "Contract", **attrs},
        "relationships": {},
    }


def tf_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "template_fields",
        "attributes": {"name": "client_name", "kind": "text", **attrs},
        "relationships": {"template": {"data": {"type": "templates", "id": TMPL_ID}}},
    }


# ── Template ──────────────────────────────────────────────────────────────


def test_template_resource_type():
    assert Template.resource_type == "templates"


def test_template_endpoint():
    assert Template.endpoint == "/templates"


def test_template_list():
    with mock_urlopen(make_response(200, {"data": [tmpl_data()]})):
        items = Template.list()
    assert len(items) == 1


def test_template_retrieve():
    with mock_urlopen(make_response(200, {"data": tmpl_data()})):
        t = Template.retrieve(UUID)
    assert t.id == UUID


def test_template_create():
    with mock_urlopen(make_response(201, {"data": tmpl_data()})):
        t = Template.create(name="Contract")
    assert t.name == "Contract"


def test_template_update():
    t = Template(
        {"id": UUID, "type": "templates", "attributes": {"name": "Old"}, "relationships": {}}
    )
    with mock_urlopen(make_response(200, {"data": tmpl_data(name="New")})):
        t.update(name="New")
    assert t.name == "New"


def test_template_delete():
    t = Template({"id": UUID, "type": "templates", "attributes": {}, "relationships": {}})
    with mock_urlopen(make_response(204, None)):
        t.delete()


def test_template_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Template.filter(name="Contract").to_list()


# ── TemplateField ─────────────────────────────────────────────────────────


def test_template_field_resource_type():
    assert TemplateField.resource_type == "template_fields"


def test_template_field_endpoint():
    assert TemplateField.endpoint == "/template_fields"


def test_template_field_list():
    with mock_urlopen(make_response(200, {"data": [tf_data()]})):
        items = TemplateField.list()
    assert len(items) == 1
    assert items[0].name == "client_name"


def test_template_field_template_id():
    tf = TemplateField(tf_data())
    assert tf.template_id == TMPL_ID
