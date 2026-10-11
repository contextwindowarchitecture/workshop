---
id: sso
title: Single sign-on (SAML)
version: 8
updated: 2026-08-25T11:00:00Z
---
SAML single sign-on lets members sign in to Fernway through your identity provider. It is available on the Business plan. Fernway supports Okta, Microsoft Entra ID, Google Workspace, and any SAML 2.0 identity provider.

To set up SSO, a workspace owner opens Settings, then Security, then Single sign-on, and copies Fernway's ACS URL and entity ID into a new SAML app in the identity provider. Then paste the provider's metadata URL back into Fernway and choose Test connection.

Before enforcing SSO, verify your email domain under Settings, then Domains, by adding the TXT record Fernway shows to your DNS. Only members with an email address on a verified domain can sign in with SSO.

Once the test succeeds, turn on Require SSO. Members then must sign in through the identity provider, and password sign-in is disabled for them. Workspace owners keep a password as a recovery path in case the identity provider is down.

SCIM provisioning creates, updates and deactivates Fernway members from your identity provider. Generate a SCIM token under Single sign-on, then SCIM, and paste it with the SCIM base URL into Okta or Entra ID. Deactivating a user in the identity provider removes their seat in Fernway within minutes.
