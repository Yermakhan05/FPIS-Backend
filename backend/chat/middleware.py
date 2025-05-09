import urllib.parse
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from api.models import FirebaseUser, Medics  # ваша модель

class FirebaseAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token = None

        # Получаем токен из query_string (например: ?token=uid123)
        qs = urllib.parse.parse_qs(scope["query_string"].decode())
        token = qs.get("token", [None])[0]

        # Или можно взять из заголовка Authorization
        if not token and "authorization" in dict(scope["headers"]):
            raw_auth = dict(scope["headers"]).get(b"authorization")
            if raw_auth:
                token = raw_auth.decode().split("Bearer ")[-1]

        user = AnonymousUser()
        if token:
            try:
                # Ищем пользователя по UID (токену)
                fb_user = await FirebaseUser.objects.aget(uid=token)
                scope["firebase_user"] = fb_user
                user = fb_user  # если модель совместима с auth.User
                print(f"[FirebaseAuthMiddleware] ✅ Пользователь найден: {fb_user}")
            except FirebaseUser.DoesNotExist:
                try:
                    medic = await Medics.objects.select_related('user').aget(doctor_firebase_id=token)
                    if medic.user:
                        scope["medic"] = medic
                        user = medic.user
                        print(f"[FirebaseAuthMiddleware] ✅ Врач найден: {medic}")
                    else:
                        print(f"[FirebaseAuthMiddleware] ⚠️ У врача нет связанного user")
                except Medics.DoesNotExist:
                    print(f"[FirebaseAuthMiddleware] ❌ Ни FirebaseUser, ни Medics не найдены по токену {token}")

        scope["user"] = user
        return await self.inner(scope, receive, send)

def CustomAuthMiddlewareStack(inner):
    return AuthMiddlewareStack(FirebaseAuthMiddleware(inner))