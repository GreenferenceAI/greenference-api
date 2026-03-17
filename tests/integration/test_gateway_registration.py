from greenference_gateway.application.services import GatewayService
from greenference_gateway.infrastructure.repository import GatewayRepository
from greenference_protocol import APIKeyCreateRequest, UserRegistrationRequest


def test_gateway_registers_user_and_persists_api_key():
    gateway = GatewayService(
        repository=GatewayRepository(database_url="sqlite+pysqlite:///:memory:", bootstrap=True)
    )
    user = gateway.register_user(UserRegistrationRequest(username="alice", email="alice@example.com"))
    api_key = gateway.create_api_key(APIKeyCreateRequest(name="default", user_id=user.user_id))

    assert user.user_id
    assert api_key.user_id == user.user_id
    assert api_key.secret.startswith("gk_")
