from typing import Callable

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.schemas.api_response import api_repoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
from app.models.revoked_token import RevokedToken


def _auth_error(request: Request, message: str) -> JSONResponse:
    response = api_repoint(
        req=request,
        status_code=401,
        message="Failed",
        error=message,
    )
    return JSONResponse(
        status_code=response.status_code,
        content=jsonable_encoder(response),
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request.state.user_id = None

        if request.method == "POST" and request.url.path in {
            "/auth/refresh",
            "/auth/logout",
        }:
            return await call_next(request)

        authorization = request.headers.get("Authorization")

        # Không có token: cho phép Guest
        if not authorization:
            return await call_next(request)

        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer" or not token:
            return _auth_error(request, "Authorization header không hợp lệ.")

        db: Session = SessionLocal()

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != "access":
                return _auth_error(request, "Token không hợp lệ")

            user_id = decode_access_token(token)

            token_jti = payload.get("jti")

            if not token_jti:
                return _auth_error(request, "Access Token không hợp lệ")

            revoked_token = (
                db.query(RevokedToken)
                .filter(RevokedToken.token_jti == token_jti)
                .first()
            )

            if revoked_token:
                return _auth_error(request, "Access Token đã bị thu hồi")

            request.state.user_id = user_id

        except ExpiredSignatureError:
            return _auth_error(request, "Token hết hạn")

        except (JWTError, KeyError, TypeError, ValueError):
            return _auth_error(request, "Token không hợp lệ")

        finally:
            db.close()

        return await call_next(request)
