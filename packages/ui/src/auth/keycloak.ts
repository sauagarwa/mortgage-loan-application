import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'mortgage-ai',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'mortgage-ai-ui',
});

export default keycloak;
