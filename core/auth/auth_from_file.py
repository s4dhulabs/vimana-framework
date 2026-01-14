import yaml
import os
import logging
import requests
from core.auth.vf_auth import VimanaAuthenticationManager
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("VFAuthFromFile")

class VFAuthFromFile():
    """
    Class to load authentication configuration from a file
    """
    def __init__(self, target_url=None, session=None, *args, **kwargs):
        self.auth_configured = False
        self.target_url = target_url
        # Create a new session if none is provided
        self.session = session if session is not None else requests.Session()
        # Pass the target URL and session to the authentication manager
        self.auth_manager = VimanaAuthenticationManager(target_url, self.session)

    def configure_authentication(self, auth_type: str, auth_params: Dict[str, Any]) -> bool:
        """
        Configure authentication for the scan
        
        Args:
            auth_type: Type of authentication (basic, form, api_key, jwt, oauth2, custom)
            auth_params: Authentication parameters
            
        Returns:
            bool: True if authentication was configured successfully
        """
        result = False
        
        # Expand environment variables in auth parameters
        auth_params = self._expand_env_vars(auth_params)
        
        # Configure authentication based on type
        if auth_type == "basic":
            username = auth_params.get('username')
            password = auth_params.get('password')
            result = self.auth_manager.configure_basic_auth(username, password)
            logger.info(f"Configured Basic Authentication for {username}")
        
        elif auth_type == "form":
            login_url = auth_params.get('login_url')
            username_field = auth_params.get('username_field')
            password_field = auth_params.get('password_field')
            username = auth_params.get('username')
            password = auth_params.get('password')
            extra_fields = auth_params.get('extra_fields')
            success_indicator = auth_params.get('success_indicator')
            
            result = self.auth_manager.configure_form_auth(
                login_url, username_field, password_field,
                username, password, extra_fields, success_indicator
            )
            logger.info(f"Configured Form Authentication for {username}")
        
        elif auth_type == "api_key":
            api_key = auth_params.get('api_key')
            header_name = auth_params.get('header_name', 'X-API-Key')
            as_query_param = auth_params.get('as_query_param', False)
            param_name = auth_params.get('param_name', 'api_key')
            
            result = self.auth_manager.configure_api_key(
                api_key, header_name, as_query_param, param_name
            )
            logger.info(f"Configured API Key Authentication with key: {api_key[:4]}...")
        
        elif auth_type == "jwt":
            token = auth_params.get('token')
            refresh_token = auth_params.get('refresh_token')
            auth_url = auth_params.get('auth_url')
            username = auth_params.get('username')
            password = auth_params.get('password')
            
            result = self.auth_manager.configure_jwt(
                token, refresh_token, auth_url, username, password
            )
            logger.info(f"Configured JWT Authentication with token: {token[:10]}...")
        
        elif auth_type == "oauth2":
            client_id = auth_params.get('client_id')
            client_secret = auth_params.get('client_secret')
            token_url = auth_params.get('token_url')
            scope = auth_params.get('scope')
            
            result = self.auth_manager.configure_oauth2(
                client_id, client_secret, token_url, scope
            )
            logger.info(f"Configured OAuth2 Authentication")
        
        elif auth_type == "custom":
            headers = auth_params.get('headers')
            cookies = auth_params.get('cookies')
            
            result = self.auth_manager.configure_custom(headers, cookies)
            logger.info(f"Configured Custom Authentication")

        elif auth_type == "django":
            username = auth_params.get('username')
            password = auth_params.get('password')
            login_url = auth_params.get('login_url', '/admin/login/')
            
            result = self.auth_manager.configure_django_auth(username, password, login_url)
            logger.info(f"Configured Django Authentication for {username}")
        
        else:
            logger.error(f"Unsupported authentication type: {auth_type}")
            return False
        
        self.auth_configured = result
        
        return result
    
    def _expand_env_vars(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand environment variables in parameter values
        
        Args:
            params: Dictionary of parameters
            
        Returns:
            Dictionary with environment variables expanded
        """
        expanded_params = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('$'):

                # Remove the $ and get from environment
                env_var = value[1:]
                expanded_value = os.environ.get(env_var)

                if expanded_value is None:
                    logger.warning(f"Environment variable {env_var} not found, using original value")
                    expanded_value = value
                else:
                    logger.info(f"Expanded environment variable {value} to {expanded_value[:10]}...")
                    
                expanded_params[key] = expanded_value
            elif isinstance(value, dict):
                # Recursively expand nested dictionaries
                expanded_params[key] = self._expand_env_vars(value)
            elif isinstance(value, list):
                # Expand values in lists
                expanded_list = []
                for v in value:
                    if isinstance(v, str) and v.startswith('$'):
                        env_var = v[1:]
                        expanded_v = os.environ.get(env_var, v)
                        expanded_list.append(expanded_v)
                    else:
                        expanded_list.append(v)
                expanded_params[key] = expanded_list
            else:
                expanded_params[key] = value
                
        return expanded_params
        
    def load_authentication_from_file(self, auth_file: str) -> bool:
        """
        Load authentication configuration from a file
        
        Args:
            auth_file: Path to authentication configuration file
            
        Returns:
            bool: True if authentication was configured successfully
        """
        try:
            logger.info(f"Loading authentication from file: {auth_file}")
            
            with open(auth_file, 'r') as f:
                auth_config = yaml.safe_load(f)
                
            auth_type = auth_config.get('type')
            auth_params = auth_config.get('params', {})
            
            # Log the authentication type being loaded
            logger.info(f"Found {auth_type} authentication configuration")
            
            success = self.configure_authentication(auth_type, auth_params)
            
            if success:
                logger.info(f"Successfully configured {auth_type} authentication from file")
            else:
                logger.error(f"Failed to configure {auth_type} authentication from file")
                
            return success
            
        except Exception as e:
            logger.error(f"Error loading authentication configuration: {str(e)}")
            print(f"Error loading authentication configuration: {str(e)}")
            return False