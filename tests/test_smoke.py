"""冒烟测试：确认最基本的链路是通的。

"冒烟测试"就是先确认程序没冒烟——页面能打开、数据能显示。
后面每加一个功能，就往这里加一个测试。
"""


def test_home_redirects_to_list(client):
    """访问首页应该跳到 /records。"""
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/records" in resp.headers["Location"]


def test_list_page_shows_records(client):
    """列表页能出数据。"""
    resp = client.get("/records")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "测试记录" in html


def test_list_page_hides_other_users_records(client):
    """列表只显示自己的记录（权限隔离）。"""
    html = client.get("/records").get_data(as_text=True)
    assert "别人的记录" not in html


def test_detail_page_ok(client):
    """详情页能打开，字段都在。"""
    resp = client.get("/records/1")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "测试记录" in html
    assert "边界没考虑" in html


def test_cannot_read_other_users_record(client):
    """别人记录的 id 直接访问应该 404，而不是 403——不泄露"存在但无权"。"""
    resp = client.get("/records/2")
    assert resp.status_code == 404


def test_missing_record_returns_404(client):
    """不存在的 id 返回 404，并且是自定义的 404 页面。"""
    resp = client.get("/records/99999")
    assert resp.status_code == 404
    assert "404" in resp.get_data(as_text=True)


def test_unknown_url_returns_404(client):
    """随便输一个地址也有友好页面，而不是白屏。"""
    resp = client.get("/this-page-does-not-exist")
    assert resp.status_code == 404
