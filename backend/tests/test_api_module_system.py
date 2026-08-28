"""模块接口测试 —— module_system（系统管理）
认证数据测试：admin 登录后验证 CRUD 真实数据。
"""

from conftest import assert_route
from fastapi.testclient import TestClient


class TestAuth:
    """认证授权接口（无需认证）。"""

    def test_auth_captcha(self, test_client: TestClient) -> None:
        assert_route(test_client, "GET", "/system/auth/captcha/get")

    def test_auth_login(self, test_client: TestClient) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/auth/login",
            data={"username": "admin", "password": "admin123"},
            expected_status=200,
        )

    def test_auth_logout(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/auth/logout",
            auth=auth_headers,
            json={"token": "mock_token"},
        )

    def test_auth_refresh(self, test_client: TestClient) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/auth/token/refresh",
            json={"refresh_token": "mock_refresh_token"},
        )


class TestUser:
    """用户管理接口 — 数据验证。"""

    def test_user_current_info(self, test_client: TestClient, auth_headers: dict) -> None:
        resp = test_client.get("/system/user/current/info", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["username"] == "admin", f"期望 admin，实际 {data['data'].get('username')}"

    def test_user_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/user/list", auth=auth_headers)

    def test_user_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        resp = test_client.get("/system/user/detail/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["username"] == "super", f"id=1 应为 super，实际 {data['data'].get('username')}"

    def test_user_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/user/create",
            auth=auth_headers,
            json={"username": "test_user", "password": "test123", "name": "测试", "dept_id": 1},
        )

    def test_user_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/user/update/1",
            auth=auth_headers,
            json={"name": "更新用户"},
        )

    def test_user_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/user/delete", auth=auth_headers, json=[9999])

    def test_user_import_template(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/user/import/template", auth=auth_headers)

    def test_user_export(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/user/export", auth=auth_headers)

    def test_user_import_data(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/user/import/data",
            auth=auth_headers,
            json={"list": []},
        )

    def test_user_current_info_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/user/current/info/update",
            auth=auth_headers,
            json={"name": "更新个人信息"},
        )

    def test_user_password_change(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/user/password/change",
            auth=auth_headers,
            json={"old_password": "old", "new_password": "new123"},
        )

    def test_user_password_forget(self, test_client: TestClient) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/user/password/forget",
            json={"username": "admin"},
        )

    def test_user_password_reset(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/user/password/reset/1",
            auth=auth_headers,
            json={"password": "newpass123"},
        )

    def test_user_register(self, test_client: TestClient) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/user/register",
            json={"username": "new_user", "password": "pass123", "name": "新用户"},
        )

    def test_user_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/user/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestRole:
    """角色管理接口 — 数据验证。"""

    def test_role_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/role/list", auth=auth_headers)

    def test_role_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/role/detail/1", auth=auth_headers)

    def test_role_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/role/create",
            auth=auth_headers,
            json={"name": "测试角色", "code": "test_role", "sort": 1},
        )

    def test_role_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/role/update/1",
            auth=auth_headers,
            json={"name": "更新角色"},
        )

    def test_role_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/role/delete", auth=auth_headers, json=[9999])

    def test_role_export(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/role/export", auth=auth_headers)

    def test_role_permission(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/role/permission",
            auth=auth_headers,
            json={"role_id": 1, "menu_ids": [1, 2]},
        )

    def test_role_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/role/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestDept:
    """部门管理接口 — 数据验证。"""

    def test_dept_tree(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dept/tree", auth=auth_headers)

    def test_dept_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dept/detail/1", auth=auth_headers)

    def test_dept_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/dept/create",
            auth=auth_headers,
            json={"name": "测试部门", "parent_id": 0, "sort": 1},
        )

    def test_dept_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/dept/update/1",
            auth=auth_headers,
            json={"name": "更新部门"},
        )

    def test_dept_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/dept/delete", auth=auth_headers, json=[9999])

    def test_dept_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/dept/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestPosition:
    """岗位管理接口 — 数据验证。"""

    def test_position_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/position/list", auth=auth_headers)

    def test_position_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/position/detail/1", auth=auth_headers)

    def test_position_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/position/create",
            auth=auth_headers,
            json={"name": "测试岗位", "code": "test_pos", "sort": 1},
        )

    def test_position_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/position/update/1",
            auth=auth_headers,
            json={"name": "更新岗位"},
        )

    def test_position_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/position/delete", auth=auth_headers, json=[9999])

    def test_position_export(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/position/export", auth=auth_headers)

    def test_position_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/position/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestDict:
    """字典管理接口 — 数据验证。"""

    def test_dict_type_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dict/type/list", auth=auth_headers)

    def test_dict_type_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dict/type/detail/1", auth=auth_headers)

    def test_dict_type_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/dict/type/create",
            auth=auth_headers,
            json={"dict_name": "测试字典", "dict_type": "test_dict", "status": 0},
        )

    def test_dict_type_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/dict/type/update/1",
            auth=auth_headers,
            json={"dict_name": "更新字典"},
        )

    def test_dict_type_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/dict/type/delete", auth=auth_headers, json=[9999])

    def test_dict_data_by_type(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dict/data/info/sys_normal_disable", auth=auth_headers)

    def test_dict_data_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dict/data/list", auth=auth_headers)

    def test_dict_data_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/dict/data/create",
            auth=auth_headers,
            json={"dict_type": "sys_normal_disable", "dict_label": "测试", "dict_value": "0", "sort": 1},
        )

    def test_dict_data_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/dict/data/update/1",
            auth=auth_headers,
            json={"dict_label": "更新标签"},
        )

    def test_dict_data_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/dict/data/delete", auth=auth_headers, json=[9999])

    def test_dict_data_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/dict/data/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )

    def test_dict_type_optionselect(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/dict/type/optionselect", auth=auth_headers)

    def test_dict_type_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/dict/type/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestNotice:
    """公告通知接口 — 数据验证。"""

    def test_notice_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/notice/list", auth=auth_headers)

    def test_notice_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/notice/detail/1", auth=auth_headers)

    def test_notice_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/notice/create",
            auth=auth_headers,
            json={"notice_title": "测试公告", "notice_content": "内容", "status": 0},
        )

    def test_notice_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/notice/update/1",
            auth=auth_headers,
            json={"notice_title": "更新公告"},
        )

    def test_notice_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/notice/delete", auth=auth_headers, json=[9999])

    def test_notice_available(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/notice/available", auth=auth_headers)

    def test_notice_status_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PATCH",
            "/system/notice/status/batch",
            auth=auth_headers,
            json={"ids": [1], "status": 1},
        )


class TestParams:
    """参数管理接口 — 数据验证（当前仅实现缓存参数信息查询与更新）。"""

    def test_params_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/param/update/1",
            auth=auth_headers,
            json={"param_value": "new_val"},
        )

    def test_params_info(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/param/info", auth=auth_headers)


class TestLog:
    """日志管理接口 — 数据验证。"""

    def test_login_log_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/log/login/list", auth=auth_headers)

    def test_login_log_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/log/login/detail/1", auth=auth_headers)

    def test_operation_log_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/log/operation/list", auth=auth_headers)

    def test_operation_log_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/log/operation/detail/1", auth=auth_headers)


class TestTicket:
    """工单管理接口 — 数据验证。"""

    def test_ticket_list(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/ticket/list", auth=auth_headers)

    def test_ticket_detail(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "GET", "/system/ticket/detail/1", auth=auth_headers)

    def test_ticket_create(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "POST",
            "/system/ticket/create",
            auth=auth_headers,
            json={"title": "测试工单", "ticket_type": "bug", "ticket_content": "内容描述"},
        )

    def test_ticket_update(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(
            test_client,
            "PUT",
            "/system/ticket/update/1",
            auth=auth_headers,
            json={"title": "更新工单"},
        )

    def test_ticket_delete(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "DELETE", "/system/ticket/delete", auth=auth_headers, json=[9999])

    def test_ticket_batch(self, test_client: TestClient, auth_headers: dict) -> None:
        assert_route(test_client, "PUT", "/system/ticket/batch", auth=auth_headers)
