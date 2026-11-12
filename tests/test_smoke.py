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


def test_anonymous_redirected_to_login(anon_client):
    """没登录访问列表页，应该被踢到登录页。"""
    resp = anon_client.get("/records")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_page_is_public(anon_client):
    """登录页本身必须不用登录就能打开，否则死循环。"""
    resp = anon_client.get("/login")
    assert resp.status_code == 200


def test_search_by_keyword(client):
    """关键词能搜到自己的记录。"""
    resp = client.get("/records?q=测试")
    assert resp.status_code == 200
    assert "测试记录" in resp.get_data(as_text=True)


def test_search_no_match_shows_empty_hint(client):
    """搜不到时给出"没有符合条件"的提示，而不是一片空白。"""
    html = client.get("/records?q=绝不存在的词zzz").get_data(as_text=True)
    assert "测试记录" not in html
    assert "没有符合条件的记录" in html


def test_search_cannot_find_other_users_records(client):
    """搜索也要讲权限：搜别人的标题，同样搜不出来。

    注意：不能直接断言"别人的记录"不在 HTML 里——
    关键词会被回填到搜索框的 value 属性里，那也算出现。
    正确的判据是"结果为空"：页面显示"没有符合条件的记录"。
    """
    html = client.get("/records?q=别人的记录").get_data(as_text=True)
    assert "没有符合条件的记录" in html


def test_filter_by_tag(client):
    """按标签筛选能出数据。"""
    resp = client.get("/records?tag=DP")
    assert resp.status_code == 200
    assert "测试记录" in resp.get_data(as_text=True)


def test_filter_by_unused_tag_is_empty(client):
    """筛一个自己没用过的标签，结果为空。"""
    html = client.get("/records?tag=BFS").get_data(as_text=True)
    assert "测试记录" not in html
    assert "没有符合条件的记录" in html


def test_stats_page_ok(client):
    """统计页能打开，平均难度算对了（唯一一条记录难度 4）。"""
    resp = client.get("/stats")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "总错题数" in html
    assert "4.0" in html


def test_stats_only_counts_own_records(client):
    """统计也不能把别人的题算进来。

    conftest 里 demo 有 1 条（难度 4），另一个用户有 1 条（难度 3）。
    若权限漏了，图表数据会变成 [0, 0, 1, 1, 0]。
    """
    html = client.get("/stats").get_data(as_text=True).replace(" ", "")
    assert "[0,0,0,1,0]" in html


def test_stats_requires_login(anon_client):
    """统计页同样受登录守卫保护。"""
    resp = anon_client.get("/stats")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
