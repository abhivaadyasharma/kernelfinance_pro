import json
import os
import urllib.error
import urllib.request


class ApiClient:
    """HTTP client that replaces the Database class, calling the Node.js backend."""

    def __init__(self, base_url=None):
        port = os.environ.get("KF_PORT", "3721")
        self.base_url = base_url or f"http://127.0.0.1:{port}/api"

    def _request(self, method, path, body=None):
        url = self.base_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                return json.loads(exc.read().decode("utf-8"))
            except Exception:
                raise ConnectionError(f"Server error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ConnectionError(f"Cannot reach server: {exc.reason}") from exc

    def _get(self, path):
        return self._request("GET", path)

    def _post(self, path, body):
        return self._request("POST", path, body)

    def _put(self, path, body):
        return self._request("PUT", path, body)

    def _delete(self, path):
        return self._request("DELETE", path)

    @staticmethod
    def _map_user(u):
        if u is None:
            return None
        return {
            "id": u["id"],
            "username_display": u["username_display"],
            "currency": u.get("currency", "INR"),
            "theme": u.get("theme", "dark"),
            "real_name": u.get("real_name", ""),
        }

    @staticmethod
    def _map_tx(row):
        return {
            "id": row["id"],
            "amount": row["amount"],
            "category": row["category"],
            "remark": row.get("remark", ""),
            "created_at": row["created_at"],
        }

    def health_check(self):
        result = self._get("/health")
        return result.get("ok", False)

    # --- Auth ---

    def create_user(self, username, password, security_answer):
        result = self._post("/auth/create-account", {
            "username": username,
            "password": password,
            "securityAnswer": security_answer,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to create account."))

    def verify_login(self, username, password):
        result = self._post("/auth/login", {
            "username": username,
            "password": password,
        })
        if not result["ok"]:
            return None
        return self._map_user(result["user"])

    def get_user_by_username(self, username):
        result = self._post("/auth/login", {
            "username": username,
            "password": "",
        })
        return None

    def verify_security_answer(self, username, answer):
        result = self._post("/auth/verify-security", {
            "username": username,
            "securityAnswer": answer,
        })
        if not result["ok"]:
            return None
        return self._map_user(result["user"])

    def reset_password(self, user_id, new_password):
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        result = self._post("/auth/reset-password", {
            "username": user["username_display"],
            "securityAnswer": "",
            "newPassword": new_password,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to reset password."))

    def reset_password_with_answer(self, username, security_answer, new_password):
        result = self._post("/auth/reset-password", {
            "username": username,
            "securityAnswer": security_answer,
            "newPassword": new_password,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to reset password."))

    # --- User ---

    def get_user_by_id(self, user_id):
        result = self._get(f"/users/{user_id}")
        if not result["ok"]:
            return None
        return self._map_user(result["user"])

    def update_currency(self, user_id, currency_code):
        result = self._put(f"/users/{user_id}/currency", {"currency": currency_code})
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to update currency."))

    def update_profile_credentials(self, user_id, username, new_password, security_answer):
        result = self._put(f"/users/{user_id}/profile", {
            "username": username,
            "newPassword": new_password,
            "securityAnswer": security_answer,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to update profile."))

    def update_theme(self, user_id, theme_name):
        result = self._put(f"/users/{user_id}/theme", {"theme": theme_name})
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to update theme."))

    # --- Transactions ---

    def add_transaction(self, user_id, amount, category, remark):
        result = self._post(f"/transactions/{user_id}/transactions", {
            "amount": amount,
            "category": category,
            "remark": remark,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to add transaction."))

    def get_transactions(self, user_id):
        result = self._get(f"/transactions/{user_id}/transactions")
        if not result["ok"]:
            return []
        return [self._map_tx(r) for r in result["rows"]]

    def get_transaction_by_id(self, user_id, tx_id):
        result = self._get(f"/transactions/{user_id}/transactions/{tx_id}")
        if not result["ok"]:
            return None
        return self._map_tx(result["row"])

    def update_transaction(self, user_id, tx_id, amount, category, remark):
        result = self._put(f"/transactions/{user_id}/transactions/{tx_id}", {
            "amount": amount,
            "category": category,
            "remark": remark,
        })
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to update transaction."))

    def delete_transaction(self, user_id, tx_id):
        result = self._delete(f"/transactions/{user_id}/transactions/{tx_id}")
        if not result["ok"]:
            raise ValueError(result.get("error", "Failed to delete transaction."))

    # --- Data ---

    def download_backup(self):
        url = self.base_url + "/data/backup"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            return resp.read()

    def upload_restore(self, file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        url = self.base_url + "/data/restore"
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/octet-stream")
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if not result["ok"]:
            raise ValueError(result.get("error", "Restore failed."))
