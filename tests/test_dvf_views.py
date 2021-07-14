from django.urls import reverse


def test_dvf_view(client, snapshot):
    r = client.get(reverse('view1'))

    assert r.status_code == 200
    assert snapshot == r.content.decode()

    r = client.get(reverse('view1') + '?fragment=if-frag')
    assert r.status_code == 200
    assert snapshot == r.content.decode()

    # this causes the template context to be different, so we get a different fragment
    r = client.get(reverse('view1') + '?fragment=if-frag&condition=true')
    assert r.status_code == 200
    assert snapshot == r.content.decode()


def test_dvf_view_initial(client, snapshot):
    # just check that if we ask for the fragment first that still works
    r = client.get(reverse('view1') + '?fragment=if-frag')
    assert r.status_code == 200
    assert snapshot == r.content.decode()
