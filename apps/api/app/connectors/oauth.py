from app.connectors.base import ConnectorPost, SocialConnector


class OAuthNotConfiguredError(RuntimeError):
    pass


class XConnector(SocialConnector):
    platform = "x"

    def import_posts(self, payload: str) -> list[ConnectorPost]:
        raise OAuthNotConfiguredError("X OAuth import is planned but not configured in v1.")


class InstagramConnector(SocialConnector):
    platform = "instagram"

    def import_posts(self, payload: str) -> list[ConnectorPost]:
        raise OAuthNotConfiguredError("Instagram OAuth import is planned but not configured in v1.")
