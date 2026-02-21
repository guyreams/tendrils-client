"""API client wrapper for all Tendrils Server HTTP calls."""

import httpx


class TendrilsAPIError(Exception):
    """Raised when the server returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class TendrilsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(
            timeout=30.0,
            headers={"Authorization": f"Bearer {token}"},
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, resp: httpx.Response) -> dict | list:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                if "detail" in body:
                    detail = body["detail"]
                    if isinstance(detail, list):
                        msg = "; ".join(item.get("msg", str(item)) for item in detail)
                    else:
                        msg = str(detail)
                elif "message" in body:
                    msg = body["message"]
                else:
                    msg = str(body)
            except Exception:
                msg = resp.text or f"HTTP {resp.status_code}"
            raise TendrilsAPIError(resp.status_code, msg)
        return resp.json()

    def ping(self) -> dict:
        resp = self.http.get(self._url("/"))
        return self._handle_response(resp)

    def get_game(self) -> dict:
        resp = self.http.get(self._url("/game"))
        return self._handle_response(resp)

    def join_game(self, character_data: dict) -> dict:
        resp = self.http.post(self._url("/game/join"), json=character_data)
        return self._handle_response(resp)

    def start_game(self) -> dict:
        resp = self.http.post(self._url("/game/start"))
        return self._handle_response(resp)

    def get_state(self) -> dict:
        resp = self.http.get(self._url("/game/state"))
        return self._handle_response(resp)

    def submit_action(self, action_data: dict) -> dict:
        resp = self.http.post(self._url("/game/action"), json=action_data)
        return self._handle_response(resp)

    def get_log(self) -> list:
        resp = self.http.get(self._url("/game/log"))
        return self._handle_response(resp)

    def get_history(self) -> list:
        resp = self.http.get(self._url("/game/history"))
        return self._handle_response(resp)

    def close(self):
        self.http.close()


class AdminClient:
    """API client for Tendrils Server admin endpoints."""

    def __init__(self, base_url: str, admin_secret: str):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(
            timeout=30.0,
            headers={"X-Admin-Secret": admin_secret},
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, resp: httpx.Response) -> dict | list:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                if "detail" in body:
                    detail = body["detail"]
                    if isinstance(detail, list):
                        msg = "; ".join(item.get("msg", str(item)) for item in detail)
                    else:
                        msg = str(detail)
                elif "message" in body:
                    msg = body["message"]
                else:
                    msg = str(body)
            except Exception:
                msg = resp.text or f"HTTP {resp.status_code}"
            raise TendrilsAPIError(resp.status_code, msg)
        return resp.json()

    def ping(self) -> dict:
        resp = self.http.get(self._url("/"))
        return self._handle_response(resp)

    def list_users(self) -> list:
        resp = self.http.get(self._url("/admin/users"))
        return self._handle_response(resp)

    def get_token(self, owner_id: str) -> dict:
        resp = self.http.get(self._url(f"/admin/users/{owner_id}/token"))
        return self._handle_response(resp)

    def register_user(self, owner_id: str, name: str) -> dict:
        resp = self.http.post(
            self._url("/admin/register"),
            json={"owner_id": owner_id, "name": name},
        )
        return self._handle_response(resp)

    def update_user(self, owner_id: str, name: str) -> dict:
        resp = self.http.patch(
            self._url(f"/admin/users/{owner_id}"),
            json={"name": name},
        )
        return self._handle_response(resp)

    def rotate_token(self, owner_id: str) -> dict:
        resp = self.http.post(self._url(f"/admin/users/{owner_id}/rotate-token"))
        return self._handle_response(resp)

    def delete_user(self, owner_id: str) -> dict:
        resp = self.http.delete(self._url(f"/admin/users/{owner_id}"))
        return self._handle_response(resp)

    def close(self):
        self.http.close()
