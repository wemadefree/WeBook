from azure.identity.aio import DefaultAzureCredential
from kiota_authentication_azure.azure_identity_authentication_provider import (
    AzureIdentityAuthenticationProvider,
)
from django.conf import settings
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient, GraphRequestAdapter


def is_graph_configured() -> bool:
    """Whether the settings needed to talk to Graph / Outlook are present"""
    return all([settings.AZURE_TENANT_ID, settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET])


def create_graph_service_client() -> GraphServiceClient:
    """
    Create a new instance of Graph Service Client

    Returns:
        An instance of GraphServiceClient

    Raises:
        Exception if any of the required environment variables are missing
    """
    if not is_graph_configured():
        raise Exception("Configuration values missing, Graph Service client can not be instantiated.")

    credential = ClientSecretCredential(
        tenant_id=settings.AZURE_TENANT_ID,
        client_id=settings.AZURE_CLIENT_ID,
        client_secret=settings.AZURE_CLIENT_SECRET
    )

    return GraphServiceClient(credentials=credential)
